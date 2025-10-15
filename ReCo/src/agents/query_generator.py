"""
검색 쿼리 생성 Agent
페르소나와 사용자 입력을 바탕으로 검색 쿼리를 생성합니다.
"""

import re
from typing import List, Dict, Any
from ..core.state import RecommendationState, PersonaType


def extract_keywords(query: str) -> List[str]:
    """검색 쿼리에서 키워드 추출"""
    # 간단한 키워드 추출 (실제로는 더 정교한 NLP 처리 필요)
    keywords = re.findall(r'\b\w+\b', query.lower())
    # 불용어 제거 (간단한 예시)
    stop_words = {'의', '을', '를', '이', '가', '은', '는', '에',
                  '에서', '로', '으로', '와', '과', '도', '만', '까지', '부터'}
    keywords = [kw for kw in keywords if kw not in stop_words and len(kw) > 1]
    return keywords


def enhance_query_for_persona(original_query: str, persona_type: PersonaType) -> str:
    """페르소나에 맞게 쿼리 향상"""
    persona_enhancements = {
        PersonaType.TRUST_SAFETY_PRO: "안전결제 신뢰도높은",
        PersonaType.HIGH_QUALITY_NEW: "새상품 미개봉 상태좋은",
        PersonaType.FAST_SHIPPING_ONLINE: "빠른배송 택배",
        PersonaType.LOCAL_OFFLINE: "직거래 동네",
        PersonaType.NEGOTIATION_FRIENDLY: "흥정 협상가능",
        PersonaType.RESPONSIVE_KIND: "친절 응답빠른",
        PersonaType.POWER_SELLER: "활발한 판매자",
        PersonaType.NICHE_SPECIALIST: "전문가 전문상품",
        PersonaType.BALANCED_LOW_ACTIVITY: "신중한 판매자",
        PersonaType.HYBRID_TRADE: "온오프라인"
    }

    enhancement = persona_enhancements.get(persona_type, "")
    if enhancement:
        return f"{original_query} {enhancement}"
    return original_query


def create_filters(user_input: Dict[str, Any]) -> Dict[str, Any]:
    """사용자 입력에서 필터 조건 생성"""
    filters = {}

    if user_input.get("price_min"):
        filters["price_min"] = user_input["price_min"]
    if user_input.get("price_max"):
        filters["price_max"] = user_input["price_max"]
    if user_input.get("category"):
        filters["category"] = user_input["category"]
    if user_input.get("location"):
        filters["location"] = user_input["location"]

    return filters


def query_generator_node(state: RecommendationState) -> RecommendationState:
    """검색 쿼리 생성 노드"""
    try:
        user_input = state["user_input"]
        persona_classification = state.get("persona_classification")

        if not persona_classification:
            raise ValueError("페르소나 분류가 완료되지 않았습니다.")

        original_query = user_input["search_query"]
        persona_type = persona_classification["persona_type"]

        # 키워드 추출
        keywords = extract_keywords(original_query)

        # 페르소나에 맞게 쿼리 향상
        enhanced_query = enhance_query_for_persona(
            original_query, persona_type)

        # 필터 조건 생성
        filters = create_filters(user_input)

        # 결과를 상태에 저장
        state["search_query"] = {
            "original_query": original_query,
            "enhanced_query": enhanced_query,
            "keywords": keywords,
            "filters": filters
        }

        state["current_step"] = "query_generated"
        state["completed_steps"].append("query_generation")

        print(f"검색 쿼리 생성 완료: {enhanced_query}")
        print(f"추출된 키워드: {keywords}")
        print(f"필터 조건: {filters}")

    except Exception as e:
        state["error_message"] = f"검색 쿼리 생성 중 오류: {str(e)}"
        state["current_step"] = "error"
        print(f"검색 쿼리 생성 오류: {e}")

    return state
