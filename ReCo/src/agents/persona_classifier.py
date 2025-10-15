"""
PersonaClassifier Agent
슬라이더 입력 정규화 + playbook 기반 RAG 분류 + rules.json threshold 매칭
입력: user_prefs → 출력: persona
"""

import json
import numpy as np
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from ..core.state import RecommendationState, PersonaType, PersonaVector, PERSONA_PROTOTYPES
from ..rag.vector_store import PlaybookVectorStore
from ..rag.retriever import PlaybookRetriever


class PersonaClassifier:
    """페르소나 분류기"""

    def __init__(self, playbook_dir: str = "./playbook", rules_path: str = "./src/config/rules.json"):
        self.playbook_dir = playbook_dir
        self.rules_path = rules_path
        self.rules = self._load_rules()
        self.vector_store = PlaybookVectorStore()
        self.retriever = None
        self._initialize_rag()

    def _load_rules(self) -> Dict[str, Any]:
        """rules.json 로드"""
        try:
            with open(self.rules_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Rules 파일을 찾을 수 없습니다: {self.rules_path}")
            return {}

    def _initialize_rag(self) -> None:
        """RAG 시스템 초기화"""
        # 벡터 저장소 로드 또는 초기화
        if not self.vector_store.load_vector_store():
            print("벡터 저장소를 초기화합니다...")
            self.vector_store.initialize_from_playbook(self.playbook_dir)

        self.retriever = PlaybookRetriever(self.vector_store)

    def normalize_slider_inputs(self, user_prefs: Dict[str, Any]) -> PersonaVector:
        """슬라이더 입력을 정규화하여 페르소나 벡터 생성"""
        # 슬라이더 값들을 0-100 범위로 정규화
        normalized_vector = {}

        for key in ["trust_safety", "quality_condition", "remote_transaction",
                    "activity_responsiveness", "price_flexibility"]:
            value = user_prefs.get(key, 50.0)  # 기본값 50
            # 0-100 범위로 클램핑
            normalized_vector[key] = max(0.0, min(100.0, float(value)))

        return PersonaVector(**normalized_vector)

    def rag_classification(self, user_vector: PersonaVector, user_prefs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """RAG를 통한 페르소나 분류"""
        if not self.retriever:
            return []

        # RAG로 관련 페르소나 후보들 검색
        persona_candidates = self.retriever.get_persona_candidates(user_prefs)

        return persona_candidates

    def calculate_l2_distance(self, vector1: PersonaVector, vector2: PersonaVector) -> float:
        """두 벡터 간의 L2 거리 계산"""
        keys = ["trust_safety", "quality_condition", "remote_transaction",
                "activity_responsiveness", "price_flexibility"]
        return np.sqrt(sum((vector1[key] - vector2[key]) ** 2 for key in keys))

    def apply_rules_threshold(self, user_vector: PersonaVector, persona_candidates: List[Dict[str, Any]]) -> Tuple[PersonaType, float, str]:
        """rules.json의 threshold를 적용하여 최종 페르소나 결정"""
        persona_rules = self.rules.get("persona_rules", {})
        thresholds = self.rules.get("persona_thresholds", {})

        best_persona = PersonaType.HYBRID_TRADE
        best_confidence = 0.0
        best_reason = "기본 페르소나 (규칙 매칭 없음)"

        # 1. 벡터 거리 기반 분류
        min_distance = float('inf')
        for persona_type, persona_data in PERSONA_PROTOTYPES.items():
            prototype_vector = persona_data["vector"]
            distance = self.calculate_l2_distance(
                user_vector, prototype_vector)

            if distance < min_distance:
                min_distance = distance
                best_persona = persona_type

        # 거리 기반 신뢰도 계산
        max_possible_distance = np.sqrt(5 * 100**2)
        distance_confidence = 1 - (min_distance / max_possible_distance)

        # 2. Rules 기반 검증
        persona_name = best_persona.value
        if persona_name in persona_rules:
            rule = persona_rules[persona_name]
            min_confidence = rule.get("min_confidence", 0.5)

            # 각 조건 검사
            conditions_met = True
            for condition_key, threshold_value in rule.items():
                if condition_key == "min_confidence":
                    continue

                vector_key = condition_key.replace(
                    "min_", "").replace("max_", "")
                if vector_key in user_vector:
                    user_value = user_vector[vector_key]
                    if condition_key.startswith("min_"):
                        if user_value < threshold_value:
                            conditions_met = False
                            break
                    elif condition_key.startswith("max_"):
                        if user_value > threshold_value:
                            conditions_met = False
                            break

            if conditions_met and distance_confidence >= min_confidence:
                best_confidence = distance_confidence
                best_reason = f"규칙 매칭 성공: {persona_name}"
            else:
                # Fallback 페르소나 사용
                fallback = thresholds.get("fallback_persona", "hybrid_trade")
                best_persona = PersonaType(fallback)
                best_confidence = 0.5
                best_reason = f"규칙 미충족, Fallback 사용: {fallback}"
        else:
            best_confidence = distance_confidence
            best_reason = f"벡터 거리 기반: {persona_name}"

        # 3. RAG 결과와 결합 (가중치 적용)
        if persona_candidates:
            rag_confidence = max([c["similarity"] for c in persona_candidates])
            # RAG와 벡터 거리 결과를 결합
            best_confidence = 0.7 * best_confidence + 0.3 * rag_confidence
            best_reason += f" + RAG 보정"

        return best_persona, best_confidence, best_reason

    def classify_persona(self, user_prefs: Dict[str, Any]) -> Dict[str, Any]:
        """전체 페르소나 분류 프로세스"""
        # 1. 슬라이더 입력 정규화
        user_vector = self.normalize_slider_inputs(user_prefs)

        # 2. RAG 분류
        persona_candidates = self.rag_classification(user_vector, user_prefs)

        # 3. Rules threshold 적용
        persona_type, confidence, reason = self.apply_rules_threshold(
            user_vector, persona_candidates)

        # 4. 매칭된 프로토타입 벡터
        matched_prototype = PERSONA_PROTOTYPES[persona_type]["vector"]

        return {
            "persona_type": persona_type,
            "confidence": confidence,
            "vector": user_vector,
            "matched_prototype": matched_prototype,
            "reason": reason,
            "rag_candidates": persona_candidates
        }


def persona_classifier_node(state: RecommendationState) -> RecommendationState:
    """페르소나 분류 노드"""
    try:
        # user_prefs 추출 (user_input에서 변환)
        user_input = state["user_input"]
        user_prefs = {
            "trust_safety": user_input.get("trust_safety", 50.0),
            "quality_condition": user_input.get("quality_condition", 50.0),
            "remote_transaction": user_input.get("remote_transaction", 50.0),
            "activity_responsiveness": user_input.get("activity_responsiveness", 50.0),
            "price_flexibility": user_input.get("price_flexibility", 50.0),
            "search_query": user_input.get("search_query", ""),
            "category": user_input.get("category", ""),
            "location": user_input.get("location", "")
        }

        # PersonaClassifier 인스턴스 생성 및 실행
        classifier = PersonaClassifier()
        result = classifier.classify_persona(user_prefs)

        # 결과를 상태에 저장
        state["persona_classification"] = result
        state["current_step"] = "persona_classified"
        state["completed_steps"].append("persona_classification")

        print(f"페르소나 분류 완료: {result['persona_type'].value}")
        print(f"신뢰도: {result['confidence']:.3f}")
        print(f"분류 근거: {result['reason']}")

    except Exception as e:
        state["error_message"] = f"페르소나 분류 중 오류: {str(e)}"
        state["current_step"] = "error"
        print(f"페르소나 분류 오류: {e}")

    return state
