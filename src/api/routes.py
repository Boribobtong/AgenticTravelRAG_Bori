"""
API Routes Module (추가 라우팅 정의)

src/api/main.py에 주요 라우트가 정의되어 있으므로, 
이 파일은 유틸리티 또는 확장 라우트를 정의하는 데 사용됩니다.
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/status/version")
async def get_version():
    """
    애플리케이션 버전 정보를 반환하는 유틸리티 라우트
    """
    return {
        "api_name": "AgenticTravelRAG API",
        "version": "1.0.0",
        "environment": "development"
    }

# 이 라우터는 main.py에서 다음과 같이 포함될 수 있습니다:
# from src.api.routes import router as utility_router
# app.include_router(utility_router, prefix="/api/v1")