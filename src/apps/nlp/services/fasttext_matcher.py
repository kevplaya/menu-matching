import os
from typing import Dict, List, Optional, Tuple

from django.conf import settings

import fasttext
import numpy as np


class FastTextMatcher:
    def __init__(self, model_path: Optional[str] = None):
        """
        Args:
            model_path: FastText 모델 파일 경로
        """
        if fasttext is None:
            raise ImportError("FastText is not installed. Please install fasttext")

        self.model_path = model_path or getattr(settings, "FASTTEXT_MODEL_PATH", None)
        self.model = None

        if self.model_path and os.path.exists(self.model_path):
            self.load_model(self.model_path)

    def load_model(self, model_path: str):
        """
        FastText 모델을 로드합니다.

        Args:
            model_path: 모델 파일 경로
        """
        self.model = fasttext.load_model(model_path)
        self.model_path = model_path

    def is_model_loaded(self) -> bool:
        """모델이 로드되었는지 확인합니다."""
        return self.model is not None

    def get_vector(self, text: str) -> Optional[np.ndarray]:
        """
        텍스트의 벡터 표현을 얻습니다.

        Args:
            text: 입력 텍스트

        Returns:
            벡터 (numpy array) 또는 None
        """
        if not self.is_model_loaded():
            return None

        return self.model.get_sentence_vector(text)

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        두 벡터의 코사인 유사도를 계산합니다.

        Args:
            vec1: 첫 번째 벡터
            vec2: 두 번째 벡터

        Returns:
            코사인 유사도 (0-1)
        """
        if vec1 is None or vec2 is None:
            return 0.0

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        두 텍스트의 유사도를 계산합니다.

        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트

        Returns:
            유사도 점수 (0-1)
        """
        vec1 = self.get_vector(text1)
        vec2 = self.get_vector(text2)

        if vec1 is None or vec2 is None:
            return 0.0

        return self.cosine_similarity(vec1, vec2)

    def find_best_match(
        self, query: str, candidates: List[str], threshold: float = 0.7
    ) -> Optional[Tuple[str, float]]:
        """
        후보 목록에서 가장 유사한 항목을 찾습니다.

        Args:
            query: 검색할 텍스트
            candidates: 후보 텍스트 리스트
            threshold: 최소 유사도 임계값

        Returns:
            (가장 유사한 텍스트, 유사도 점수) 또는 None
        """
        if not self.is_model_loaded() or not candidates:
            return None

        query_vec = self.get_vector(query)
        if query_vec is None:
            return None

        best_match = None
        best_score = threshold

        for candidate in candidates:
            candidate_vec = self.get_vector(candidate)
            if candidate_vec is None:
                continue

            score = self.cosine_similarity(query_vec, candidate_vec)
            if score > best_score:
                best_score = score
                best_match = candidate

        if best_match:
            return (best_match, best_score)

        return None

    def find_top_matches(
        self, query: str, candidates: List[str], top_k: int = 5, threshold: float = 0.5
    ) -> List[Tuple[str, float]]:
        """
        후보 목록에서 상위 K개의 유사한 항목을 찾습니다.

        Args:
            query: 검색할 텍스트
            candidates: 후보 텍스트 리스트
            top_k: 반환할 상위 항목 개수
            threshold: 최소 유사도 임계값

        Returns:
            (텍스트, 유사도 점수) 튜플의 리스트
        """
        if not self.is_model_loaded() or not candidates:
            return []

        query_vec = self.get_vector(query)
        if query_vec is None:
            return []

        similarities = []
        for candidate in candidates:
            candidate_vec = self.get_vector(candidate)
            if candidate_vec is None:
                continue

            score = self.cosine_similarity(query_vec, candidate_vec)
            if score >= threshold:
                similarities.append((candidate, score))

        # 점수 내림차순 정렬
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    def batch_similarity(
        self, queries: List[str], targets: List[str]
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        여러 쿼리에 대해 일괄적으로 유사도를 계산합니다.

        Args:
            queries: 쿼리 텍스트 리스트
            targets: 타겟 텍스트 리스트

        Returns:
            {쿼리: [(타겟, 유사도)] } 형태의 딕셔너리
        """
        if not self.is_model_loaded():
            return {}

        results = {}
        for query in queries:
            matches = self.find_top_matches(query, targets, top_k=3)
            results[query] = matches

        return results
