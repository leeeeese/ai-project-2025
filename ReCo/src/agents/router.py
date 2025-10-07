"""
라우터 Agent
다음 실행할 Agent를 결정합니다.
"""

from typing import Literal
from ..core.state import RecommendationState


def should_continue(state: RecommendationState) -> Literal["continue", "end"]:
    """계속 진행할지 결정"""
    if state.get("error_message"):
        return "end"

    if state.get("current_step") == "products_ranked":
        return "end"

    return "continue"


def router_node(state: RecommendationState) -> RecommendationState:
    """라우터 노드"""
    try:
        current_step = state.get("current_step", "")

        if current_step == "start":
            state["current_step"] = "persona_classification"
            print("다음 단계: 페르소나 분류")

        elif current_step == "persona_classified":
            state["current_step"] = "query_generation"
            print("다음 단계: 검색 쿼리 생성")

        elif current_step == "query_generated":
            state["current_step"] = "product_matching"
            print("다음 단계: 상품 매칭")

        elif current_step == "products_matched":
            state["current_step"] = "ranking"
            print("다음 단계: 상품 랭킹")

        elif current_step == "products_ranked":
            state["current_step"] = "completed"
            print("모든 단계 완료")

        else:
            state["error_message"] = f"알 수 없는 단계: {current_step}"
            state["current_step"] = "error"

    except Exception as e:
        state["error_message"] = f"라우터 오류: {str(e)}"
        state["current_step"] = "error"
        print(f"라우터 오류: {e}")

    return state
