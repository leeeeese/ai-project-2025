"""
Ranker(FusionRanker) Agent
3,4단계 결과를 종합 → 최종 점수/설명
입력: seller_item_scores → 출력: final_item_scores
"""

import numpy as np
from typing import List, Dict, Any, Optional
from ..core.state import RecommendationState
from ..utils.chain_of_thought import ChainOfThought


class FusionRanker:
    """융합 랭킹기"""

    def __init__(self):
        self.cot = ChainOfThought()

    def fuse_scores(self, seller_item_scores: List[Dict[str, Any]],
                    persona_classification: Dict[str, Any]) -> List[Dict[str, Any]]:
        """3,4단계 결과를 융합하여 최종 점수 생성"""
        if not seller_item_scores:
            return []

        # 1. 기본 점수 정규화
        normalized_scores = self._normalize_scores(seller_item_scores)

        # 2. 페르소나 가중치 적용
        persona_weighted_scores = self._apply_persona_weights(
            normalized_scores, persona_classification)

        # 3. 다양성 보너스 적용
        diversity_adjusted_scores = self._apply_diversity_bonus(
            persona_weighted_scores)

        # 4. 최종 점수 계산
        final_scores = self._calculate_final_scores(diversity_adjusted_scores)

        # 5. Chain of Thought 추론 과정 기록
        self._record_reasoning_process(seller_item_scores, final_scores,
                                       persona_classification)

        return final_scores

    def _normalize_scores(self, seller_item_scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """점수들을 0-1 범위로 정규화"""
        if not seller_item_scores:
            return []

        # 각 점수 유형별로 최대값, 최소값 계산
        persona_scores = [item['seller_persona_score']
                          for item in seller_item_scores]
        quality_scores = [item['seller_quality_score']
                          for item in seller_item_scores]
        feature_scores = [item['product_feature_score']
                          for item in seller_item_scores]

        # Min-Max 정규화
        def normalize_list(scores):
            if not scores or max(scores) == min(scores):
                return [0.5] * len(scores)
            return [(score - min(scores)) / (max(scores) - min(scores)) for score in scores]

        norm_persona = normalize_list(persona_scores)
        norm_quality = normalize_list(quality_scores)
        norm_feature = normalize_list(feature_scores)

        # 정규화된 점수 적용
        normalized_items = []
        for i, item in enumerate(seller_item_scores):
            normalized_item = item.copy()
            normalized_item['norm_persona_score'] = norm_persona[i]
            normalized_item['norm_quality_score'] = norm_quality[i]
            normalized_item['norm_feature_score'] = norm_feature[i]
            normalized_items.append(normalized_item)

        return normalized_items

    def _apply_persona_weights(self, normalized_scores: List[Dict[str, Any]],
                               persona_classification: Dict[str, Any]) -> List[Dict[str, Any]]:
        """페르소나에 따른 가중치 적용"""
        persona_type = persona_classification.get(
            "persona_type", "hybrid_trade")
        confidence = persona_classification.get("confidence", 0.5)

        # 페르소나별 가중치 설정
        persona_weights = {
            "trust_safety_pro": {"persona": 0.6, "quality": 0.3, "feature": 0.1},
            "high_quality_new": {"persona": 0.4, "quality": 0.4, "feature": 0.2},
            "fast_shipping_online": {"persona": 0.5, "quality": 0.3, "feature": 0.2},
            "local_offline": {"persona": 0.6, "quality": 0.2, "feature": 0.2},
            "negotiation_friendly": {"persona": 0.5, "quality": 0.2, "feature": 0.3},
            "power_seller": {"persona": 0.4, "quality": 0.4, "feature": 0.2},
            "responsive_kind": {"persona": 0.5, "quality": 0.3, "feature": 0.2},
            "niche_specialist": {"persona": 0.4, "quality": 0.3, "feature": 0.3},
            "balanced_low_activity": {"persona": 0.4, "quality": 0.3, "feature": 0.3},
            "hybrid_trade": {"persona": 0.4, "quality": 0.3, "feature": 0.3}
        }

        weights = persona_weights.get(
            persona_type, {"persona": 0.4, "quality": 0.3, "feature": 0.3})

        # 신뢰도에 따른 가중치 조정
        confidence_factor = 0.5 + (confidence * 0.5)  # 0.5 ~ 1.0
        weights = {k: v * confidence_factor for k, v in weights.items()}

        # 가중치 적용
        weighted_items = []
        for item in normalized_scores:
            weighted_item = item.copy()
            weighted_score = (
                weights["persona"] * item['norm_persona_score'] +
                weights["quality"] * item['norm_quality_score'] +
                weights["feature"] * item['norm_feature_score']
            )
            weighted_item['weighted_score'] = weighted_score
            weighted_item['persona_weights'] = weights
            weighted_items.append(weighted_item)

        return weighted_items

    def _apply_diversity_bonus(self, weighted_scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """다양성 보너스 적용 (카테고리, 판매자 다양성)"""
        if len(weighted_scores) <= 1:
            return weighted_scores

        # 카테고리 다양성 계산
        categories = [item['category'] for item in weighted_scores]
        unique_categories = len(set(categories))
        category_diversity = unique_categories / \
            len(categories) if categories else 0

        # 판매자 다양성 계산
        sellers = [item['seller_id'] for item in weighted_scores]
        unique_sellers = len(set(sellers))
        seller_diversity = unique_sellers / len(sellers) if sellers else 0

        # 다양성 보너스 적용
        diversity_bonus = 0.1 * (category_diversity + seller_diversity) / 2

        diversity_items = []
        for i, item in enumerate(weighted_scores):
            diversity_item = item.copy()
            # 순위가 낮을수록 더 많은 보너스 (다양성 촉진)
            rank_bonus = diversity_bonus * (1 - i / len(weighted_scores))
            diversity_item['diversity_bonus'] = rank_bonus
            diversity_item['diversity_score'] = item['weighted_score'] + rank_bonus
            diversity_items.append(diversity_item)

        return diversity_items

    def _calculate_final_scores(self, diversity_scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """최종 점수 계산 및 정렬"""
        final_items = []

        for item in diversity_scores:
            final_item = item.copy()
            final_item['final_score'] = item['diversity_score']

            # 추가 메타데이터
            final_item['ranking_factors'] = {
                'persona_match': item['norm_persona_score'],
                'seller_quality': item['norm_quality_score'],
                'product_features': item['norm_feature_score'],
                'diversity_bonus': item['diversity_bonus'],
                'persona_weights': item['persona_weights']
            }

            final_items.append(final_item)

        # 최종 점수 순으로 정렬
        final_items.sort(key=lambda x: x['final_score'], reverse=True)

        return final_items

    def _record_reasoning_process(self, original_scores: List[Dict[str, Any]],
                                  final_scores: List[Dict[str, Any]],
                                  persona_classification: Dict[str, Any]) -> None:
        """추론 과정 기록"""
        # 1. 입력 분석
        self.cot.add_step("입력 분석", {
            "total_items": len(original_scores),
            "persona_type": persona_classification.get("persona_type"),
            "confidence": persona_classification.get("confidence")
        })

        # 2. 정규화 과정
        self.cot.add_step("점수 정규화", {
            "method": "Min-Max Normalization",
            "score_types": ["persona", "quality", "feature"]
        })

        # 3. 가중치 적용
        self.cot.add_step("페르소나 가중치 적용", {
            "persona_type": persona_classification.get("persona_type"),
            "confidence_factor": 0.5 + (persona_classification.get("confidence", 0.5) * 0.5)
        })

        # 4. 다양성 보너스
        categories = set(item['category'] for item in final_scores)
        sellers = set(item['seller_id'] for item in final_scores)
        self.cot.add_step("다양성 보너스 적용", {
            "category_diversity": len(categories),
            "seller_diversity": len(sellers)
        })

        # 5. 최종 랭킹
        self.cot.add_step("최종 랭킹 생성", {
            "top_item": final_scores[0]['title'] if final_scores else None,
            "top_score": final_scores[0]['final_score'] if final_scores else 0
        })

    def generate_explanation(self, final_scores: List[Dict[str, Any]],
                             persona_classification: Dict[str, Any]) -> str:
        """추천 근거 설명 생성"""
        return self.cot.generate_explanation(final_scores, persona_classification)


def ranker_node(state: RecommendationState) -> RecommendationState:
    """랭킹 노드"""
    try:
        seller_item_scores = state.get("seller_item_scores")
        persona_classification = state.get("persona_classification")

        if not seller_item_scores:
            raise ValueError("매칭된 상품이 없습니다.")

        if not persona_classification:
            raise ValueError("페르소나 분류가 완료되지 않았습니다.")

        # FusionRanker 인스턴스 생성
        ranker = FusionRanker()

        # 3,4단계 결과 융합
        final_item_scores = ranker.fuse_scores(
            seller_item_scores, persona_classification)

        # 추천 근거 설명 생성
        explanation = ranker.generate_explanation(
            final_item_scores, persona_classification)

        # 결과를 상태에 저장
        state["final_item_scores"] = final_item_scores
        state["ranking_explanation"] = explanation
        state["current_step"] = "products_ranked"
        state["completed_steps"].append("ranking")

        print(f"상품 랭킹 완료: {len(final_item_scores)}개 상품")
        print(f"추천 근거:")
        print(explanation)

        # 상위 5개 결과 출력
        for i, item in enumerate(final_item_scores[:5], 1):
            print(f"  {i}. {item['title']} (최종점수: {item['final_score']:.3f})")
            print(f"     페르소나: {item['ranking_factors']['persona_match']:.3f}, "
                  f"품질: {item['ranking_factors']['seller_quality']:.3f}, "
                  f"피처: {item['ranking_factors']['product_features']:.3f}")

    except Exception as e:
        state["error_message"] = f"상품 랭킹 중 오류: {str(e)}"
        state["current_step"] = "error"
        print(f"상품 랭킹 오류: {e}")

    return state
