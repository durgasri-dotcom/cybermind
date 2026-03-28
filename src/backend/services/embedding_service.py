from __future__ import annotations

import time
from functools import lru_cache

import numpy as np

from configs.logging_config import get_logger
from configs.settings import settings

logger = get_logger(__name__)


class EmbeddingService:
    def __init__(self) -> None:
        self._model = None
        self._dimension = settings.embedding_dimension

    def _ensure_loaded(self) -> None:
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            start = time.perf_counter()
            self._model = SentenceTransformer(settings.embedding_model)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info("embedding_model_loaded", model=settings.embedding_model, latency_ms=round(elapsed, 2))

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> np.ndarray:
        self._ensure_loaded()
        return self._model.encode(text, normalize_embeddings=True)

    def embed_batch(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        if not texts:
            return np.empty((0, self._dimension), dtype=np.float32)
        self._ensure_loaded()
        return self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 100,
        )

    def compute_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        return float(np.dot(vec_a, vec_b))


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()