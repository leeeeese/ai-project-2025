"""
API 라우트 정의
FastAPI 엔드포인트를 정의합니다.
"""

import time
import uuid
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from .schemas import UserInputRequest, RecommendationResponse, ErrorResponse
from ..graphs.recommendation_graph import create_recommendation_graph, create_initial_state

router = APIRouter()

# 그래프 인스턴스 생성
recommendation_graph = create_recommendation_graph()


@router.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(request: UserInputRequest):
    """상품 추천 API"""
    try:
        # 세션 ID 생성
        session_id = str(uuid.uuid4())
        
        # 초기 상태 생성
        user_input = {
            "search_query": request.search_query,
            "price_min": request.price_min,
            "price_max": request.price_max,
            "category": request.category,
            "location": request.location,
            "user_id": request.user_id
        }
        
        initial_state = create_initial_state(user_input, session_id)
        
        # 그래프 실행
        start_time = time.time()
        result = recommendation_graph.invoke(initial_state)
        execution_time = time.time() - start_time
        
        # 에러 체크
        if result.get("error_message"):
            raise HTTPException(
                status_code=500,
                detail=result["error_message"]
            )
        
        # 응답 생성
        products = []
        if result.get("ranking_result") and result["ranking_result"].get("products"):
            for product in result["ranking_result"]["products"]:
                products.append({
                    "product_id": product["product_id"],
                    "seller_id": product["seller_id"],
                    "title": product["title"],
                    "price": product["price"],
                    "category": product["category"],
                    "condition": product["condition"],
                    "location": product["location"],
                    "match_score": product["match_score"],
                    "persona_score": product["persona_score"]
                })
        
        persona_classification = None
        if result.get("persona_classification"):
            pc = result["persona_classification"]
            persona_classification = {
                "persona_type": pc["persona_type"].value,
                "confidence": pc["confidence"],
                "vector": pc["vector"]
            }
        
        return RecommendationResponse(
            products=products,
            total_count=len(products),
            persona_classification=persona_classification,
            search_query=result.get("search_query"),
            execution_time=execution_time,
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"추천 시스템 오류: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """헬스 체크 API"""
    return {"status": "healthy", "service": "ReCo Recommendation System"}


@router.get("/personas")
async def get_personas():
    """페르소나 목록 조회 API"""
    from ..core.state import PERSONA_PROTOTYPES
    
    personas = []
    for persona_type, data in PERSONA_PROTOTYPES.items():
        personas.append({
            "type": persona_type.value,
            "name": data["name"],
            "vector": data["vector"]
        })
    
    return {"personas": personas}
