"""
API 스키마 정의
요청/응답 모델을 정의합니다.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class UserInputRequest(BaseModel):
    """사용자 입력 요청"""
    search_query: str = Field(..., description="검색 쿼리")
    price_min: Optional[float] = Field(None, description="최소 가격")
    price_max: Optional[float] = Field(None, description="최대 가격")
    category: Optional[str] = Field(None, description="카테고리")
    location: Optional[str] = Field(None, description="지역")
    user_id: Optional[str] = Field(None, description="사용자 ID")


class PersonaClassificationResponse(BaseModel):
    """페르소나 분류 응답"""
    persona_type: str
    confidence: float
    vector: Dict[str, float]


class ProductMatchResponse(BaseModel):
    """상품 매칭 응답"""
    product_id: str
    seller_id: str
    title: str
    price: float
    category: str
    condition: str
    location: str
    match_score: float
    persona_score: float


class RecommendationResponse(BaseModel):
    """추천 결과 응답"""
    products: List[ProductMatchResponse]
    total_count: int
    persona_classification: Optional[PersonaClassificationResponse]
    search_query: Optional[Dict[str, Any]]
    execution_time: Optional[float]
    session_id: str


class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str
    detail: Optional[str] = None
    session_id: str
