"""
페르소나 분류 Agent
사용자 입력을 바탕으로 페르소나를 분류합니다.
"""

import numpy as np
from typing import Dict, Any
from ..core.state import RecommendationState, PersonaType, PersonaVector, PERSONA_PROTOTYPES, MATCHING_WEIGHTS


def calculate_l2_distance(vector1: PersonaVector, vector2: PersonaVector) -> float:
    """두 벡터 간의 L2 거리 계산"""
    keys = ["trust_safety", "quality_condition", "remote_transaction",
            "activity_responsiveness", "price_flexibility"]
    return np.sqrt(sum((vector1[key] - vector2[key]) ** 2 for key in keys))


def classify_persona(user_vector: PersonaVector) -> tuple[PersonaType, float, PersonaVector]:
    """사용자 벡터를 바탕으로 페르소나 분류"""
    min_distance = float('inf')
    best_persona = PersonaType.HYBRID_TRADE
    best_prototype = PERSONA_PROTOTYPES[PersonaType.HYBRID_TRADE]["vector"]

    for persona_type, persona_data in PERSONA_PROTOTYPES.items():
        prototype_vector = persona_data["vector"]
        distance = calculate_l2_distance(user_vector, prototype_vector)

        if distance < min_distance:
            min_distance = distance
            best_persona = persona_type
            best_prototype = prototype_vector

    # 신뢰도 계산 (거리를 0-1 범위로 정규화)
    max_possible_distance = np.sqrt(5 * 100**2)  # 5개 축, 각각 0-100 범위
    confidence = 1 - (min_distance / max_possible_distance)

    return best_persona, confidence, best_prototype


def create_user_vector_from_input(user_input: Dict[str, Any]) -> PersonaVector:
    """사용자 입력에서 페르소나 벡터 생성 (임시 구현)"""
    # 실제로는 사용자의 과거 거래 데이터를 분석하여 벡터를 생성해야 함
    # 현재는 기본값으로 균형형 페르소나 사용

    # TODO: 실제 사용자 데이터 분석 로직 구현
    # 예시: 검색 쿼리 분석, 가격 범위 분석, 카테고리 선호도 분석 등

    return {
        "trust_safety": 50.0,
        "quality_condition": 50.0,
        "remote_transaction": 50.0,
        "activity_responsiveness": 50.0,
        "price_flexibility": 50.0
    }


def persona_classifier_node(state: RecommendationState) -> RecommendationState:
    """페르소나 분류 노드"""
    try:
        # 사용자 벡터 생성
        user_vector = create_user_vector_from_input(state["user_input"])

        # 페르소나 분류
        persona_type, confidence, matched_prototype = classify_persona(
            user_vector)

        # 결과를 상태에 저장
        state["persona_classification"] = {
            "persona_type": persona_type,
            "confidence": confidence,
            "vector": user_vector,
            "matched_prototype": matched_prototype
        }

        state["current_step"] = "persona_classified"
        state["completed_steps"].append("persona_classification")

        print(f"페르소나 분류 완료: {persona_type.value} (신뢰도: {confidence:.3f})")

    except Exception as e:
        state["error_message"] = f"페르소나 분류 중 오류: {str(e)}"
        state["current_step"] = "error"
        print(f"페르소나 분류 오류: {e}")

    return state
