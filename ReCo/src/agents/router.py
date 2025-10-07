"""
Router(Orchestrator) Agent
서브그래프를 순차적으로 연결/실행
입력: user_query → 출력: SQL query
"""

import time
from typing import Literal, Dict, Any, Optional
from ..core.state import RecommendationState


class Orchestrator:
    """워크플로우 오케스트레이터"""
    
    def __init__(self):
        self.workflow_steps = [
            "persona_classification",
            "product_matching", 
            "ranking",
            "query_generation"
        ]
        self.step_descriptions = {
            "persona_classification": "사용자 페르소나 분류",
            "product_matching": "상품 매칭 (사용자↔판매자↔상품)",
            "ranking": "최종 랭킹 및 점수 융합",
            "query_generation": "SQL 쿼리 생성"
        }
    
    def should_continue(self, state: RecommendationState) -> Literal["continue", "end"]:
        """계속 진행할지 결정"""
        if state.get("error_message"):
            return "end"
        
        current_step = state.get("current_step", "")
        
        # 완료 조건들
        if current_step == "query_generated":
            return "end"
        elif current_step == "completed":
            return "end"
        elif current_step == "error":
            return "end"
        
        return "continue"
    
    def get_next_step(self, current_step: str) -> Optional[str]:
        """다음 단계 결정"""
        if current_step == "start":
            return "persona_classification"
        elif current_step == "persona_classified":
            return "product_matching"
        elif current_step == "products_matched":
            return "ranking"
        elif current_step == "products_ranked":
            return "query_generation"
        else:
            return None
    
    def validate_step_completion(self, state: RecommendationState, step: str) -> bool:
        """단계 완료 검증"""
        if step == "persona_classification":
            return state.get("persona_classification") is not None
        elif step == "product_matching":
            return state.get("seller_item_scores") is not None
        elif step == "ranking":
            return state.get("final_item_scores") is not None
        elif step == "query_generation":
            return state.get("sql_query") is not None
        return False
    
    def handle_error(self, state: RecommendationState, error: str) -> RecommendationState:
        """에러 처리"""
        state["error_message"] = error
        state["current_step"] = "error"
        state["completed_steps"].append("error_handling")
        
        print(f"❌ 오류 발생: {error}")
        return state
    
    def log_step_progress(self, state: RecommendationState, step: str) -> None:
        """단계 진행 로그"""
        step_desc = self.step_descriptions.get(step, step)
        completed_steps = state.get("completed_steps", [])
        
        print(f"🔄 현재 단계: {step_desc}")
        print(f"✅ 완료된 단계: {', '.join(completed_steps)}")
        
        # 실행 시간 로그
        if "execution_start_time" not in state:
            state["execution_start_time"] = time.time()
        
        current_time = time.time()
        elapsed_time = current_time - state.get("execution_start_time", current_time)
        print(f"⏱️  경과 시간: {elapsed_time:.2f}초")


def router_node(state: RecommendationState) -> RecommendationState:
    """라우터 노드 (오케스트레이터)"""
    try:
        orchestrator = Orchestrator()
        current_step = state.get("current_step", "")
        
        # 에러 상태 체크
        if current_step == "error":
            return state
        
        # 완료 상태 체크
        if current_step == "completed":
            print("🎉 모든 단계가 완료되었습니다!")
            return state
        
        # 다음 단계 결정
        next_step = orchestrator.get_next_step(current_step)
        
        if next_step is None:
            error_msg = f"알 수 없는 단계: {current_step}"
            return orchestrator.handle_error(state, error_msg)
        
        # 단계 진행 로그
        orchestrator.log_step_progress(state, next_step)
        
        # 다음 단계로 설정
        state["current_step"] = next_step
        
        # 단계별 추가 처리
        if next_step == "persona_classification":
            print("📊 사용자 선호도를 분석하여 페르소나를 분류합니다...")
            
        elif next_step == "product_matching":
            print("🔍 사용자 페르소나와 판매자/상품을 매칭합니다...")
            
        elif next_step == "ranking":
            print("📈 매칭 결과를 융합하여 최종 랭킹을 생성합니다...")
            
        elif next_step == "query_generation":
            print("💾 최종 결과를 바탕으로 SQL 쿼리를 생성합니다...")
        
        # 워크플로우 완료 체크
        if next_step == "query_generation" and state.get("sql_query"):
            state["current_step"] = "completed"
            state["completed_steps"].append("query_generation")
            
            # 최종 실행 시간 계산
            if "execution_start_time" in state:
                total_time = time.time() - state["execution_start_time"]
                state["execution_time"] = total_time
                print(f"🎯 전체 실행 완료! 총 소요시간: {total_time:.2f}초")
            
            print("📋 생성된 SQL 쿼리:")
            sql_query = state.get("sql_query", {})
            if sql_query.get("query"):
                query_preview = sql_query["query"][:100] + "..." if len(sql_query["query"]) > 100 else sql_query["query"]
                print(f"   {query_preview}")
        
    except Exception as e:
        error_msg = f"라우터 오류: {str(e)}"
        orchestrator = Orchestrator()
        return orchestrator.handle_error(state, error_msg)
    
    return state


def should_continue(state: RecommendationState) -> Literal["continue", "end"]:
    """계속 진행할지 결정 (LangGraph용)"""
    orchestrator = Orchestrator()
    return orchestrator.should_continue(state)
