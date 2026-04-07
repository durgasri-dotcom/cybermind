from __future__ import annotations

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
            from fastembed import TextEmbedding
            logger.info("loading_fastembed_model", model=settings.embedding_model)
            self._model = TextEmbedding(model_name=settings.embedding_model)
            logger.info("fastembed_model_loaded", model=settings.embedding_model)

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> np.ndarray:
        self._ensure_loaded()
        vectors = list(self._model.embed([text]))
        return np.array(vectors[0], dtype=np.float32)

    def embed_batch(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        if not texts:
            return np.empty((0, self._dimension), dtype=np.float32)
        self._ensure_loaded()
        vectors = list(self._model.embed(texts))
        return np.array(vectors, dtype=np.float32)

    def compute_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        return float(np.dot(vec_a, vec_b))


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
