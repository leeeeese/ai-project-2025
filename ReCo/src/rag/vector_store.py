"""
벡터 저장소 관리
Playbook 문서의 임베딩을 저장하고 검색합니다.
"""

import json
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import pickle
import os


class PlaybookVectorStore:
    """Playbook 문서의 벡터 저장소"""

    def __init__(self, vector_store_path: str = "./data/vector_store.pkl"):
        self.vector_store_path = vector_store_path
        self.embeddings = []
        self.documents = []
        self.metadata = []

    def load_playbook_documents(self, playbook_dir: str) -> List[Dict[str, Any]]:
        """Playbook 디렉토리에서 문서들을 로드"""
        documents = []
        playbook_path = Path(playbook_dir)

        # 페르소나 정의서 로드
        persona_def_path = playbook_path / "persona_definition.md"
        if persona_def_path.exists():
            with open(persona_def_path, 'r', encoding='utf-8') as f:
                content = f.read()
                documents.append({
                    "content": content,
                    "type": "persona_definition",
                    "source": str(persona_def_path)
                })

        # 개별 페르소나 문서들 로드
        personas_dir = playbook_path / "personas"
        if personas_dir.exists():
            for persona_file in personas_dir.glob("*.md"):
                with open(persona_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    documents.append({
                        "content": content,
                        "type": "persona",
                        "persona_name": persona_file.stem,
                        "source": str(persona_file)
                    })

        return documents

    def create_embeddings(self, documents: List[Dict[str, Any]]) -> None:
        """문서들에 대한 임베딩 생성 (임시 구현)"""
        # 실제로는 OpenAI Embeddings API 사용
        # 현재는 간단한 TF-IDF 스타일 임베딩 사용

        for doc in documents:
            # 간단한 단어 빈도 기반 임베딩 (실제로는 더 정교한 방법 필요)
            words = doc["content"].lower().split()
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1

            # 100차원 벡터로 변환 (실제로는 1536차원 OpenAI embedding)
            embedding = np.random.rand(100)  # 임시 구현

            self.embeddings.append(embedding)
            self.documents.append(doc)
            self.metadata.append({
                "type": doc.get("type", "unknown"),
                "persona_name": doc.get("persona_name", None),
                "source": doc.get("source", "")
            })

    def save_vector_store(self) -> None:
        """벡터 저장소를 파일에 저장"""
        os.makedirs(os.path.dirname(self.vector_store_path), exist_ok=True)

        with open(self.vector_store_path, 'wb') as f:
            pickle.dump({
                "embeddings": self.embeddings,
                "documents": self.documents,
                "metadata": self.metadata
            }, f)

    def load_vector_store(self) -> bool:
        """저장된 벡터 저장소 로드"""
        if not os.path.exists(self.vector_store_path):
            return False

        try:
            with open(self.vector_store_path, 'rb') as f:
                data = pickle.load(f)
                self.embeddings = data["embeddings"]
                self.documents = data["documents"]
                self.metadata = data["metadata"]
            return True
        except Exception as e:
            print(f"벡터 저장소 로드 실패: {e}")
            return False

    def similarity_search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """쿼리 벡터와 유사한 문서들 검색"""
        if not self.embeddings:
            return []

        # 코사인 유사도 계산
        similarities = []
        for i, embedding in enumerate(self.embeddings):
            similarity = np.dot(query_vector, embedding) / (
                np.linalg.norm(query_vector) * np.linalg.norm(embedding)
            )
            similarities.append((i, similarity))

        # 유사도 순으로 정렬
        similarities.sort(key=lambda x: x[1], reverse=True)

        # 상위 k개 반환
        results = []
        for i, (doc_idx, similarity) in enumerate(similarities[:top_k]):
            results.append({
                "document": self.documents[doc_idx],
                "metadata": self.metadata[doc_idx],
                "similarity": similarity,
                "rank": i + 1
            })

        return results

    def initialize_from_playbook(self, playbook_dir: str) -> None:
        """Playbook에서 벡터 저장소 초기화"""
        documents = self.load_playbook_documents(playbook_dir)
        self.create_embeddings(documents)
        self.save_vector_store()
        print(f"벡터 저장소 초기화 완료: {len(documents)}개 문서")
