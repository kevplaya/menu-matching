import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings

import fasttext
import numpy as np

logger = logging.getLogger(__name__)


class FastTextMatcher:
    def __init__(self, model_path: Optional[str] = None):
        if fasttext is None:
            raise ImportError("FastText is not installed. Please install fasttext")

        self.model_path = model_path or getattr(settings, "FASTTEXT_MODEL_PATH", None)
        self.model = None

        if self.model_path and os.path.exists(self.model_path):
            self.load_model(self.model_path)

    def load_model(self, model_path: str) -> None:
        self.model = fasttext.load_model(model_path)
        self.model_path = model_path

    def is_model_loaded(self) -> bool:
        return self.model is not None

    def get_vector(self, text: str) -> Optional[np.ndarray]:
        if not self.is_model_loaded():
            return None
        return self.model.get_sentence_vector(text)

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        if vec1 is None or vec2 is None:
            return 0.0
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot_product / (norm1 * norm2))

    def calculate_similarity(self, text1: str, text2: str) -> float:
        vec1 = self.get_vector(text1)
        vec2 = self.get_vector(text2)
        if vec1 is None or vec2 is None:
            return 0.0
        return self.cosine_similarity(vec1, vec2)

    def find_best_match(
        self, query: str, candidates: List[str], threshold: float = 0.7
    ) -> Optional[Tuple[str, float]]:
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
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def batch_similarity(
        self, queries: List[str], targets: List[str]
    ) -> Dict[str, List[Tuple[str, float]]]:
        if not self.is_model_loaded():
            return {}
        results = {}
        for query in queries:
            matches = self.find_top_matches(query, targets, top_k=3)
            results[query] = matches
        return results

    def train_model(
        self,
        training_data_path: str,
        output_path: str,
        model_type: str = "skipgram",
        dim: int = 200,
        epoch: int = 10,
        lr: float = 0.05,
        word_ngrams: int = 2,
        min_count: int = 1,
        thread: int = 4,
        verbose: int = 2,
        **kwargs: Any,
    ) -> None:
        if not os.path.exists(training_data_path):
            raise FileNotFoundError(f"Training data file not found: {training_data_path}")

        logger.info("FastText training start: %s -> %s", training_data_path, output_path)

        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        model = fasttext.train_unsupervised(
            training_data_path,
            model=model_type,
            dim=dim,
            epoch=epoch,
            lr=lr,
            wordNgrams=word_ngrams,
            minCount=min_count,
            thread=thread,
            verbose=verbose,
            **kwargs,
        )

        model.save_model(output_path)
        self.model = model
        self.model_path = output_path
        logger.info("FastText training done: vocab_size=%d", len(model.words))

    def get_model_info(self) -> Optional[Dict[str, Any]]:
        if not self.is_model_loaded():
            return None
        try:
            return {
                "model_path": self.model_path,
                "vocabulary_size": len(self.model.words),
                "vector_dimension": self.model.get_dimension(),
                "is_loaded": True,
            }
        except Exception as e:
            logger.error("Error getting model info: %s", e)
            return {
                "model_path": self.model_path,
                "is_loaded": False,
                "error": str(e),
            }
