"""
추천 시스템 LangGraph 정의
전체 워크플로우를 관리합니다.
"""

from langgraph.graph import StateGraph, END
from typing import Literal
from ..core.state import RecommendationState
from ..agents.persona_classifier import persona_classifier_node
from ..agents.query_generator import query_generator_node
from ..agents.product_matching import product_matching_node
from ..agents.ranker import ranker_node
from ..agents.router import router_node, should_continue


def create_recommendation_graph():
    """추천 시스템 그래프 생성"""

    # StateGraph 생성
    workflow = StateGraph(RecommendationState)

    # 노드 추가
    workflow.add_node("router", router_node)
    workflow.add_node("persona_classifier", persona_classifier_node)
    workflow.add_node("query_generator", query_generator_node)
    workflow.add_node("product_matching", product_matching_node)
    workflow.add_node("ranker", ranker_node)

    # 엔트리 포인트 설정
    workflow.set_entry_point("router")

    # 조건부 엣지 추가
    workflow.add_conditional_edges(
        "router",
        lambda state: state.get("current_step", ""),
        {
            "persona_classification": "persona_classifier",
            "query_generation": "query_generator",
            "product_matching": "product_matching",
            "ranking": "ranker",
            "completed": END,
            "error": END
        }
    )

    # 각 Agent 노드에서 라우터로 돌아가는 엣지
    workflow.add_edge("persona_classifier", "router")
    workflow.add_edge("query_generator", "router")
    workflow.add_edge("product_matching", "router")
    workflow.add_edge("ranker", "router")

    # 그래프 컴파일
    app = workflow.compile()

    return app


def create_initial_state(user_input: dict, session_id: str) -> RecommendationState:
    """초기 상태 생성"""
    import time

    return {
        "user_input": user_input,
        "persona_classification": None,
        "seller_item_scores": None,  # ProductMatching 출력
        "final_item_scores": None,   # Ranker 출력
        "sql_query": None,           # QueryGenerator 출력
        "ranking_explanation": None, # Ranker 설명
        "current_step": "start",
        "completed_steps": [],
        "error_message": None,
        "session_id": session_id,
        "timestamp": time.time(),
        "execution_time": None,
        "execution_start_time": time.time()
    }
