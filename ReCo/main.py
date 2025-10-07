"""
ReCo - 중고거래 추천 시스템
FastAPI 웹 서버 + LangGraph Agent 시스템
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router
from src.core.config import settings

# FastAPI 앱 생성
app = FastAPI(
    title=settings.app_name,
    description="중고거래 추천 시스템 - LangGraph Agent 기반",
    version="1.0.0",
    debug=settings.debug
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "ReCo - 중고거래 추천 시스템",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
