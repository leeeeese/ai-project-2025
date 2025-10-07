"""
랭킹 Agent
매칭된 상품들을 최종적으로 랭킹합니다.
"""

from typing import List
from ..core.state import RecommendationState, RankingResult


def rank_products(product_matches: List[dict]) -> List[dict]:
    """상품들을 랭킹"""
    # 매칭 점수 기준으로 내림차순 정렬
    ranked_products = sorted(
        product_matches, key=lambda x: x["match_score"], reverse=True)
    return ranked_products


def ranker_node(state: RecommendationState) -> RecommendationState:
    """랭킹 노드"""
    try:
        product_matches = state.get("product_matches")

        if not product_matches:
            raise ValueError("매칭된 상품이 없습니다.")

        # 상품 랭킹
        ranked_products = rank_products(product_matches)

        # 결과를 상태에 저장
        state["ranking_result"] = {
            "products": ranked_products,
            "total_count": len(ranked_products),
            "ranking_criteria": ["match_score", "persona_score"]
        }

        state["current_step"] = "products_ranked"
        state["completed_steps"].append("ranking")

        print(f"상품 랭킹 완료: {len(ranked_products)}개 상품")
        for i, product in enumerate(ranked_products[:5], 1):  # 상위 5개만 출력
            print(
                f"  {i}. {product['title']} (점수: {product['match_score']:.3f})")

    except Exception as e:
        state["error_message"] = f"상품 랭킹 중 오류: {str(e)}"
        state["current_step"] = "error"
        print(f"상품 랭킹 오류: {e}")

    return state
