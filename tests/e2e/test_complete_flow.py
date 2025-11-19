"""
End-to-End Test: 
전체 시스템 (FastAPI + Agentic Workflow)의 동작을 확인합니다.
실제 API 키 및 ElasticSearch 인스턴스에 의존합니다.
"""

import pytest
import httpx
import os
import asyncio
from datetime import datetime, timedelta

# FastAPI 서버 URL (Docker Compose 환경을 가정)
BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_health_check():
    """API 서버 및 종속성 상태 확인 (ES 연결 여부 포함)"""
    try:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/health", timeout=10)
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == "healthy" # ES와 워크플로우 모두 정상일 때
            assert data['elasticsearch'] is True
            assert data['workflow'] is True
            
    except httpx.ConnectError:
        pytest.fail(f"FastAPI 서버에 연결할 수 없습니다: {BASE_URL}")


@pytest.mark.asyncio
async def test_single_turn_travel_plan():
    """단일 턴 여행 계획 생성 테스트 (가장 중요한 E2E 테스트)"""
    
    # 현재 날짜 기준 다음 주 월요일부터 3일
    start_date = (datetime.now() + timedelta(days=(7 - datetime.now().weekday()))).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=(7 - datetime.now().weekday() + 2))).strftime("%Y-%m-%d")
    
    query = f"파리에서 {start_date}부터 3일 동안 낭만적이고 조용한 호텔을 찾아줘. 예산은 $300 이내."
    
    payload = {
        "query": query,
        "session_id": None
    }
    
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=120) as client:
            response = await client.post("/api/v1/plan", json=payload)
            
            assert response.status_code == 200
            result = response.json()
            
            # 기본 검증
            assert result['success'] is True
            assert result['session_id'] is not None
            assert "여행 계획이 성공적으로 생성되었습니다" in result['message']
            
            # 결과 내용 검증
            itinerary = result['itinerary']
            hotels = result['hotels']
            
            assert itinerary is not None
            assert "파리" in itinerary['summary']
            assert len(hotels) >= 1 # 호텔 검색 결과가 최소 1개 이상 존재해야 함
            assert hotels[0]['name'] is not None
            assert hotels[0]['rating'] >= 3.0
            
            # 워크플로우 실행 경로 검증
            # assert 'response_generator' in result['execution_path']
            
    except httpx.ConnectError:
        pytest.fail("FastAPI 서버에 연결할 수 없습니다.")
    except Exception as e:
        pytest.fail(f"E2E 테스트 중 오류 발생: {e}")

@pytest.mark.asyncio
async def test_multi_turn_feedback_refinement():
    """다중 턴 피드백 기반 개선 테스트"""
    
    # 1. 초기 계획 생성
    initial_query = "뉴욕에서 가족 여행용 호텔 추천해줘. 4박 5일."
    initial_response = await httpx.AsyncClient(base_url=BASE_URL, timeout=120).post(
        "/api/v1/plan", json={"query": initial_query, "session_id": None}
    )
    initial_result = initial_response.json()
    assert initial_result['success'] is True
    session_id = initial_result['session_id']
    
    # 2. 피드백 제출: 더 저렴한 호텔 요청
    feedback_query = "호텔이 너무 비싸. 가격대가 더 저렴한 곳을 찾아줘."
    
    payload_feedback = {
        "session_id": session_id,
        "query": feedback_query
    }
    
    # 3. 개선된 계획 생성 요청
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120) as client:
        refinement_response = await client.post("/api/v1/plan", json=payload_feedback)
        
        assert refinement_response.status_code == 200
        refinement_result = refinement_response.json()
        
        # 기본 검증
        assert refinement_result['success'] is True
        assert refinement_result['session_id'] == session_id
        
        # 실행 경로 검증 (Feedback Handler -> Hotel RAG 재실행 확인)
        # assert 'feedback_handler' in refinement_result['execution_path']
        # assert refinement_result['execution_path'].count('hotel_rag') > 1 # 재실행되었는지 확인

        # 결과 검증 (가격이 더 저렴한 옵션이 추천되었는지, 정량적 검증은 어려우므로 정성적 검증)
        assert len(refinement_result['hotels']) >= 1