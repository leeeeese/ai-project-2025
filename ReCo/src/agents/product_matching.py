"""
ProductMatching Agent
사용자 persona ↔ 판매자 persona ↔ 상품 피처 매칭
입력: persona, seller_features → 출력: seller_item_scores
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from ..core.state import RecommendationState, PersonaVector, PersonaType, MATCHING_WEIGHTS
from ..services.database_service import DatabaseService


class ProductMatching:
    """상품 매칭기"""

    def __init__(self):
        self.db_service = DatabaseService()

    def match_user_seller_persona(self, user_persona: PersonaVector, sellers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """1단계: 사용자 페르소나 ↔ 판매자 페르소나 매칭"""
        seller_scores = []

        for seller in sellers:
            seller_vector = seller["persona_vector"]

            # 페르소나 매칭 점수 계산
            persona_score = self._calculate_persona_score(
                user_persona, seller_vector)

            # 추가 판매자 특성 점수
            seller_quality_score = self._calculate_seller_quality_score(seller)

            # 최종 판매자 점수 (가중 평균)
            final_score = 0.7 * persona_score + 0.3 * seller_quality_score

            seller_scores.append({
                "seller_id": seller["seller_id"],
                "seller_name": seller["seller_name"],
                "persona_score": persona_score,
                "quality_score": seller_quality_score,
                "final_score": final_score,
                "persona_vector": seller_vector,
                "total_sales": seller["total_sales"],
                "avg_rating": seller["avg_rating"],
                "response_time_hours": seller["response_time_hours"]
            })

        # 점수 순으로 정렬
        seller_scores.sort(key=lambda x: x["final_score"], reverse=True)

        return seller_scores

    def match_seller_product_features(self, seller_scores: List[Dict[str, Any]], products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """2단계: 판매자 ↔ 상품 피처 매칭"""
        seller_item_scores = []

        for seller_score in seller_scores:
            seller_id = seller_score["seller_id"]
            seller_products = [
                p for p in products if p["seller_id"] == seller_id]

            for product in seller_products:
                # 상품 피처 점수 계산
                product_feature_score = self._calculate_product_feature_score(
                    product)

                # 판매자 점수와 상품 점수 결합
                final_item_score = 0.6 * \
                    seller_score["final_score"] + 0.4 * product_feature_score

                seller_item_scores.append({
                    "product_id": product["product_id"],
                    "seller_id": seller_id,
                    "seller_name": seller_score["seller_name"],
                    "title": product["title"],
                    "price": product["price"],
                    "category": product["category"],
                    "condition": product["condition"],
                    "location": product["location"],
                    "description": product["description"],
                    "seller_persona_score": seller_score["persona_score"],
                    "seller_quality_score": seller_score["quality_score"],
                    "product_feature_score": product_feature_score,
                    "final_item_score": final_item_score,
                    "seller_rating": seller_score["avg_rating"],
                    "view_count": product["view_count"],
                    "like_count": product["like_count"]
                })

        # 최종 점수 순으로 정렬
        seller_item_scores.sort(
            key=lambda x: x["final_item_score"], reverse=True)

        return seller_item_scores

    def _calculate_persona_score(self, user_vector: PersonaVector, seller_vector: PersonaVector) -> float:
        """사용자와 판매자 간의 페르소나 매칭 점수 계산"""
        score = 0.0
        total_weight = 0.0

        for key, weight in MATCHING_WEIGHTS.items():
            if key in user_vector and key in seller_vector:
                # 점수 계산: w_k * (1 - |u_k - s_k| / 100)
                diff = abs(user_vector[key] - seller_vector[key])
                match_score = weight * (1 - diff / 100)
                score += match_score
                total_weight += weight

        return score / total_weight if total_weight > 0 else 0.0

    def _calculate_seller_quality_score(self, seller: Dict[str, Any]) -> float:
        """판매자 품질 점수 계산"""
        # 평점 기반 점수 (0-1)
        rating_score = min(seller["avg_rating"] / 5.0, 1.0)

        # 판매량 기반 점수 (0-1)
        sales_score = min(seller["total_sales"] / 1000.0, 1.0)

        # 응답 시간 기반 점수 (0-1, 빠를수록 높음)
        response_score = max(0, 1 - (seller["response_time_hours"] / 24.0))

        # 가중 평균
        return 0.5 * rating_score + 0.3 * sales_score + 0.2 * response_score

    def _calculate_product_feature_score(self, product: Dict[str, Any]) -> float:
        """상품 피처 점수 계산"""
        # 조회수 기반 점수 (0-1)
        view_score = min(product["view_count"] / 1000.0, 1.0)

        # 좋아요 기반 점수 (0-1)
        like_score = min(product["like_count"] / 100.0, 1.0)

        # 상품 상태 기반 점수
        condition_scores = {
            "새상품": 1.0,
            "거의새것": 0.8,
            "중고": 0.6,
            "사용감있음": 0.4
        }
        condition_score = condition_scores.get(product["condition"], 0.5)

        # 가중 평균
        return 0.4 * view_score + 0.3 * like_score + 0.3 * condition_score

    def get_products_for_matching(self, filters: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """매칭을 위한 판매자와 상품 데이터 조회"""
        # 실제 DB에서 데이터 조회 (현재는 목업 사용)
        try:
            sellers = self.db_service.get_sellers_with_persona(limit=50)
            seller_ids = [s["seller_id"] for s in sellers]
            products = self.db_service.get_products_by_sellers(
                seller_ids, filters)
        except Exception as e:
            print(f"DB 조회 실패, 목업 데이터 사용: {e}")
            sellers = self.db_service.get_mock_sellers()
            seller_ids = [s["seller_id"] for s in sellers]
            products = self.db_service.get_mock_products(seller_ids)

        return sellers, products


def product_matching_node(state: RecommendationState) -> RecommendationState:
    """상품 매칭 노드"""
    try:
        persona_classification = state.get("persona_classification")
        search_query = state.get("search_query")

        if not persona_classification:
            raise ValueError("페르소나 분류가 완료되지 않았습니다.")

        # 필터 추출
        filters = search_query.get("filters", {}) if search_query else {}

        # ProductMatching 인스턴스 생성
        matcher = ProductMatching()

        # 1. 판매자와 상품 데이터 조회
        sellers, products = matcher.get_products_for_matching(filters)

        if not sellers or not products:
            raise ValueError("매칭할 판매자나 상품이 없습니다.")

        # 2. 사용자 페르소나 ↔ 판매자 페르소나 매칭
        user_persona = persona_classification["vector"]
        seller_scores = matcher.match_user_seller_persona(
            user_persona, sellers)

        # 3. 판매자 ↔ 상품 피처 매칭
        seller_item_scores = matcher.match_seller_product_features(
            seller_scores, products)

        # 결과를 상태에 저장
        state["seller_item_scores"] = seller_item_scores
        state["current_step"] = "products_matched"
        state["completed_steps"].append("product_matching")

        print(f"상품 매칭 완료: {len(seller_item_scores)}개 상품")
        print(f"판매자 매칭: {len(seller_scores)}개 판매자")

        # 상위 5개 결과 출력
        for i, item in enumerate(seller_item_scores[:5], 1):
            print(
                f"  {i}. {item['title']} (점수: {item['final_item_score']:.3f})")
            print(
                f"     판매자: {item['seller_name']} (페르소나: {item['seller_persona_score']:.3f})")

    except Exception as e:
        state["error_message"] = f"상품 매칭 중 오류: {str(e)}"
        state["current_step"] = "error"
        print(f"상품 매칭 오류: {e}")

    return state
