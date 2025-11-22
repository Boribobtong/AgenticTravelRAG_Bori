"""
FastAPI Server for AgenticTravelRAG
여행 계획 API 엔드포인트를 제공합니다.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from loguru import logger
from dotenv import load_dotenv

# [1] 서버 시작 전 .env 로드
env_path = Path("config/.env")
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

# [2] 프록시 환경 변수 제거 (OpenAI 라이브러리 충돌 방지)
# 이 코드가 없으면 'unexpected keyword argument proxies' 에러가 발생할 수 있습니다.
proxy_keys = ["http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "OPENAI_PROXY"]
for key in proxy_keys:
    if key in os.environ:
        del os.environ[key]

# 프로젝트 루트를 Python Path에 추가
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.workflow import get_workflow
from src.core.state import AppState, StateManager

# FastAPI 앱 초기화
app = FastAPI(
    title="AgenticTravelRAG API",
    description="TripAdvisor 리뷰 기반 지능형 여행 플래너 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수
sessions: Dict[str, AppState] = {}
workflow = None

# ==================== Request/Response 모델 ====================

class TravelRequest(BaseModel):
    """여행 계획 요청 모델"""
    query: str = Field(..., description="사용자의 여행 관련 질문")
    session_id: Optional[str] = Field(None, description="기존 세션 ID (Multi-turn 대화용)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "파리에서 조용하고 낭만적인 호텔 추천해줘. 12월 15일부터 3일간 여행이야.",
                "session_id": None
            }
        }

class TravelResponse(BaseModel):
    """여행 계획 응답 모델"""
    success: bool
    session_id: str
    message: str
    itinerary: Optional[Dict[str, Any]] = None
    hotels: Optional[list] = None
    weather: Optional[list] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """헬스체크 응답"""
    status: str
    elasticsearch: bool
    workflow: bool

# ==================== API 엔드포인트 ====================

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    global workflow
    logger.info("AgenticTravelRAG API 서버 시작...")
    
    try:
        # 워크플로우 초기화
        workflow = get_workflow()
        logger.success("워크플로우 초기화 완료")
    except Exception as e:
        logger.error(f"워크플로우 초기화 실패: {str(e)}")

@app.get("/", tags=["Root"])
async def root():
    """루트 엔드포인트"""
    return {
        "service": "AgenticTravelRAG API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """헬스체크 엔드포인트"""
    
    # ElasticSearch 상태 확인
    es_status = False
    try:
        from src.rag.elasticsearch_rag import get_rag_instance
        rag = get_rag_instance()
        if rag.es.ping():
            es_status = True
    except:
        pass
    
    # 워크플로우 상태
    workflow_status = workflow is not None
    
    return HealthResponse(
        status="healthy" if es_status and workflow_status else "degraded",
        elasticsearch=es_status,
        workflow=workflow_status
    )

@app.post("/api/v1/plan", response_model=TravelResponse, tags=["Travel Planning"])
async def create_travel_plan(request: TravelRequest):
    """
    여행 계획 생성 엔드포인트
    
    사용자의 자연어 쿼리를 받아 맞춤형 여행 계획을 생성합니다.
    """
    
    if not workflow:
        raise HTTPException(status_code=503, detail="Workflow not initialized")
    
    try:
        # 세션 ID 처리
        session_id = request.session_id or str(uuid.uuid4())
        
        # 기존 세션이 있는 경우
        if request.session_id and request.session_id in sessions:
            # Multi-turn 대화 계속
            previous_state = sessions[request.session_id]
            result = await workflow.continue_conversation(
                user_input=request.query,
                session_id=session_id,
                previous_state=previous_state
            )
        else:
            # 새로운 대화 시작
            result = await workflow.run(
                user_query=request.query,
                session_id=session_id
            )
        
        # 세션 저장 (메모리에 임시 저장)
        if result.get('success'):
            # 나중에 Redis 등으로 교체 필요
            sessions[session_id] = result.get('state', {})
        
        return TravelResponse(
            success=result.get('success', False),
            session_id=session_id,
            message="여행 계획이 성공적으로 생성되었습니다." if result.get('success') else "계획 생성 중 오류가 발생했습니다.",
            itinerary=result.get('itinerary'),
            hotels=result.get('hotels'),
            weather=result.get('weather'),
            error=result.get('error')
        )
        
    except Exception as e:
        logger.error(f"여행 계획 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/sessions/{session_id}", tags=["Sessions"])
async def get_session(session_id: str):
    """
    세션 정보 조회 엔드포인트
    """
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = sessions[session_id]
    
    return {
        "session_id": session_id,
        "destination": state.get('destination'),
        "dates": state.get('travel_dates'),
        "chat_history": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat() if hasattr(msg.timestamp, 'isoformat') else str(msg.timestamp)
            }
            for msg in state.get('chat_history', [])
        ],
        "hotels_found": len(state.get('hotel_options', [])),
        "has_weather": bool(state.get('weather_forecast'))
    }

@app.delete("/api/v1/sessions/{session_id}", tags=["Sessions"])
async def delete_session(session_id: str):
    """세션 삭제 엔드포인트"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del sessions[session_id]
    return {"message": "Session deleted successfully"}

@app.post("/api/v1/feedback", tags=["Feedback"])
async def submit_feedback(
    session_id: str,
    feedback: str,
    rating: Optional[int] = None
):
    """사용자 피드백 제출 엔드포인트"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = sessions[session_id]
    state['user_feedback'] = feedback
    if rating:
        state['satisfaction_score'] = rating
    
    return {"message": "Feedback submitted successfully"}

@app.get("/api/v1/hotels/search", tags=["Hotels"])
async def search_hotels(
    destination: str,
    check_in: Optional[str] = None,
    check_out: Optional[str] = None,
    min_rating: Optional[float] = 3.5
):
    """호텔 직접 검색 엔드포인트"""
    
    try:
        from src.rag.elasticsearch_rag import get_rag_instance
        rag = get_rag_instance()
        
        results = rag.hybrid_search(
            query=f"{destination} hotel",
            location=destination,
            min_rating=min_rating,
            top_k=10
        )
        
        return {"hotels": results}
        
    except Exception as e:
        logger.error(f"호텔 검색 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/weather/{location}", tags=["Weather"])
async def get_weather(location: str, days: int = 5):
    """날씨 정보 조회 엔드포인트"""
    
    try:
        from src.agents.weather_tool import WeatherToolAgent
        weather_agent = WeatherToolAgent()
        
        from datetime import datetime, timedelta
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        
        forecast = await weather_agent.get_forecast(
            location=location,
            dates=[start_date, end_date]
        )
        
        return {"weather": forecast}
        
    except Exception as e:
        logger.error(f"날씨 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 메인 실행 ====================

if __name__ == "__main__":
    # 환경변수 로드 (uvicorn으로 직접 실행하지 않을 경우를 대비)
    load_dotenv("config/.env")
    
    # 서버 실행
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )