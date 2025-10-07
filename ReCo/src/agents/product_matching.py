"""
상품 매칭 Agent
검색 쿼리와 페르소나를 바탕으로 상품을 매칭합니다.
"""

import time
from typing import List, Dict, Any
from ..core.state import RecommendationState, ProductMatch, PersonaVector, MATCHING_WEIGHTS


def calculate_persona_score(user_vector: PersonaVector, seller_vector: PersonaVector) -> float:
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


def calculate_text_match_score(query: str, product_title: str, keywords: List[str]) -> float:
    """텍스트 매칭 점수 계산"""
    query_lower = query.lower()
    title_lower = product_title.lower()

    # 키워드 매칭 점수
    keyword_matches = sum(1 for keyword in keywords if keyword in title_lower)
    keyword_score = keyword_matches / len(keywords) if keywords else 0.0

    # 전체 쿼리 매칭 점수
    query_words = query_lower.split()
    query_matches = sum(1 for word in query_words if word in title_lower)
    query_score = query_matches / len(query_words) if query_words else 0.0

    # 가중 평균
    return 0.7 * keyword_score + 0.3 * query_score


def mock_database_search(search_query: Dict[str, Any], persona_type: str) -> List[Dict[str, Any]]:
    """데이터베이스 검색 (임시 구현)"""
    # 실제로는 MySQL에서 상품 데이터를 조회해야 함
    # 현재는 목업 데이터 반환

    mock_products = [
        {
            "product_id": "1",
            "seller_id": "seller_1",
            "title": "아이폰 14 Pro Max 256GB 새상품",
            "price": 1200000,
            "category": "스마트폰",
            "condition": "새상품",
            "location": "서울 강남구",
            "seller_vector": {
                "trust_safety": 80,
                "quality_condition": 90,
                "remote_transaction": 70,
                "activity_responsiveness": 85,
                "price_flexibility": 30
            }
        },
        {
            "product_id": "2",
            "seller_id": "seller_2",
            "title": "맥북 프로 16인치 M2 칩",
            "price": 2500000,
            "category": "노트북",
            "condition": "중고",
            "location": "서울 서초구",
            "seller_vector": {
                "trust_safety": 60,
                "quality_condition": 70,
                "remote_transaction": 80,
                "activity_responsiveness": 90,
                "price_flexibility": 50
            }
        },
        {
            "product_id": "3",
            "seller_id": "seller_3",
            "title": "나이키 에어맥스 270 운동화",
            "price": 150000,
            "category": "신발",
            "condition": "거의새것",
            "location": "부산 해운대구",
            "seller_vector": {
                "trust_safety": 70,
                "quality_condition": 60,
                "remote_transaction": 60,
                "activity_responsiveness": 70,
                "price_flexibility": 80
            }
        }
    ]

    # 필터 적용
    filtered_products = []
    for product in mock_products:
        if search_query["filters"].get("price_min") and product["price"] < search_query["filters"]["price_min"]:
            continue
        if search_query["filters"].get("price_max") and product["price"] > search_query["filters"]["price_max"]:
            continue
        if search_query["filters"].get("category") and product["category"] != search_query["filters"]["category"]:
            continue
        if search_query["filters"].get("location") and search_query["filters"]["location"] not in product["location"]:
            continue

        filtered_products.append(product)

    return filtered_products


def product_matching_node(state: RecommendationState) -> RecommendationState:
    """상품 매칭 노드"""
    try:
        search_query = state.get("search_query")
        persona_classification = state.get("persona_classification")

        if not search_query or not persona_classification:
            raise ValueError("검색 쿼리 또는 페르소나 분류가 완료되지 않았습니다.")

        # 데이터베이스에서 상품 검색
        products = mock_database_search(
            search_query, persona_classification["persona_type"])

        # 각 상품에 대해 매칭 점수 계산
        product_matches = []
        user_vector = persona_classification["vector"]

        for product in products:
            # 텍스트 매칭 점수
            text_score = calculate_text_match_score(
                search_query["enhanced_query"],
                product["title"],
                search_query["keywords"]
            )

            # 페르소나 매칭 점수
            persona_score = calculate_persona_score(
                user_vector, product["seller_vector"])

            # 전체 매칭 점수 (가중 평균)
            total_score = 0.6 * text_score + 0.4 * persona_score

            product_match = ProductMatch(
                product_id=product["product_id"],
                seller_id=product["seller_id"],
                title=product["title"],
                price=product["price"],
                category=product["category"],
                condition=product["condition"],
                location=product["location"],
                match_score=total_score,
                persona_score=persona_score
            )

            product_matches.append(product_match)

        # 결과를 상태에 저장
        state["product_matches"] = product_matches
        state["current_step"] = "products_matched"
        state["completed_steps"].append("product_matching")

        print(f"상품 매칭 완료: {len(product_matches)}개 상품")
        for match in product_matches[:3]:  # 상위 3개만 출력
            print(f"  - {match['title']} (점수: {match['match_score']:.3f})")

    except Exception as e:
        state["error_message"] = f"상품 매칭 중 오류: {str(e)}"
        state["current_step"] = "error"
        print(f"상품 매칭 오류: {e}")

    return state
