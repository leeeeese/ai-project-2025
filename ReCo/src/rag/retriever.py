"""
RAG 검색기
사용자 입력을 바탕으로 관련 Playbook 문서를 검색합니다.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from .vector_store import PlaybookVectorStore


class PlaybookRetriever:
    """Playbook 문서 검색기"""

    def __init__(self, vector_store: PlaybookVectorStore):
        self.vector_store = vector_store

    def create_query_embedding(self, user_prefs: Dict[str, Any]) -> np.ndarray:
        """사용자 선호도를 바탕으로 쿼리 임베딩 생성"""
        # 사용자 선호도를 텍스트로 변환
        query_text = self._prefs_to_text(user_prefs)

        # 간단한 임베딩 생성 (실제로는 OpenAI Embeddings API 사용)
        # 현재는 사용자 벡터를 그대로 사용
        user_vector = self._extract_user_vector(user_prefs)

        # 100차원으로 변환 (실제로는 1536차원)
        query_embedding = np.random.rand(100)  # 임시 구현

        return query_embedding

    def _prefs_to_text(self, user_prefs: Dict[str, Any]) -> str:
        """사용자 선호도를 텍스트로 변환"""
        text_parts = []

        # 슬라이더 값들을 텍스트로 변환
        if "trust_safety" in user_prefs:
            text_parts.append(f"신뢰안전중시도: {user_prefs['trust_safety']}")
        if "quality_condition" in user_prefs:
            text_parts.append(f"품질상태중시도: {user_prefs['quality_condition']}")
        if "remote_transaction" in user_prefs:
            text_parts.append(f"원격거래선호도: {user_prefs['remote_transaction']}")
        if "activity_responsiveness" in user_prefs:
            text_parts.append(
                f"활동응답중시도: {user_prefs['activity_responsiveness']}")
        if "price_flexibility" in user_prefs:
            text_parts.append(f"가격유연성: {user_prefs['price_flexibility']}")

        # 추가 컨텍스트
        if "search_query" in user_prefs:
            text_parts.append(f"검색어: {user_prefs['search_query']}")
        if "category" in user_prefs:
            text_parts.append(f"카테고리: {user_prefs['category']}")

        return " ".join(text_parts)

    def _extract_user_vector(self, user_prefs: Dict[str, Any]) -> Dict[str, float]:
        """사용자 선호도에서 벡터 추출"""
        return {
            "trust_safety": user_prefs.get("trust_safety", 50.0),
            "quality_condition": user_prefs.get("quality_condition", 50.0),
            "remote_transaction": user_prefs.get("remote_transaction", 50.0),
            "activity_responsiveness": user_prefs.get("activity_responsiveness", 50.0),
            "price_flexibility": user_prefs.get("price_flexibility", 50.0)
        }

    def retrieve_relevant_documents(self, user_prefs: Dict[str, Any], top_k: int = 3) -> List[Dict[str, Any]]:
        """사용자 선호도와 관련된 문서들 검색"""
        query_embedding = self.create_query_embedding(user_prefs)
        results = self.vector_store.similarity_search(query_embedding, top_k)

        return results

    def get_persona_candidates(self, user_prefs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """페르소나 후보들을 검색"""
        results = self.retrieve_relevant_documents(user_prefs, top_k=5)

        # 페르소나 관련 문서만 필터링
        persona_candidates = []
        for result in results:
            if result["metadata"]["type"] == "persona":
                persona_candidates.append({
                    "persona_name": result["metadata"]["persona_name"],
                    "content": result["document"]["content"],
                    "similarity": result["similarity"]
                })

        return persona_candidates
