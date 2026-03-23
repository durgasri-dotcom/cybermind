from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter

from configs.settings import settings
from configs.logging_config import get_logger
from src.backend.services.embedding_service import EmbeddingService, get_embedding_service

logger = get_logger(__name__)


class RAGService:
    def __init__(self, embedding_svc: Optional[EmbeddingService] = None) -> None:
        self._embedding_svc = embedding_svc or get_embedding_service()
        self._index: Optional[faiss.IndexFlatIP] = None
        self._chunks: list[str] = []
        self._metadata: list[dict] = []
        self._is_loaded = False
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
            separators=["\n\n", "\n", ". ", " "],
        )

    def load_index(self) -> None:
        if settings.use_pinecone:
            self._load_pinecone()
        else:
            self._load_faiss()

    def _load_faiss(self) -> None:
        index_path = Path(settings.faiss_index_path)
        chunks_path = index_path.parent / "faiss_chunks.json"

        if not index_path.exists():
            logger.warning("faiss_index_not_found", path=str(index_path))
            self._index = faiss.IndexFlatIP(settings.embedding_dimension)
            self._is_loaded = False
            return

        start = time.perf_counter()
        self._index = faiss.read_index(str(index_path))

        if chunks_path.exists():
            with open(chunks_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._chunks = data.get("chunks", [])
                self._metadata = data.get("metadata", [])

        elapsed = (time.perf_counter() - start) * 1000
        self._is_loaded = True
        logger.info("faiss_index_loaded", num_vectors=self._index.ntotal, latency_ms=round(elapsed, 2))

    def _load_pinecone(self) -> None:
        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=settings.pinecone_api_key)
            self._pinecone_index = pc.Index(settings.pinecone_index_name)
            self._is_loaded = True
            logger.info("pinecone_connected", index=settings.pinecone_index_name)
        except Exception as e:
            logger.error("pinecone_connection_failed", error=str(e))
            self._is_loaded = False

    def build_index_from_documents(self, documents: list[dict]) -> int:
        all_chunks = []
        all_metadata = []

        for doc in documents:
            text_chunks = self._text_splitter.split_text(doc["text"])
            for i, chunk in enumerate(text_chunks):
                all_chunks.append(chunk)
                all_metadata.append({
                    "threat_id": doc.get("threat_id", "unknown"),
                    "source": doc.get("source", "MITRE ATT&CK"),
                    "chunk_index": i,
                    **doc.get("metadata", {}),
                })

        if not all_chunks:
            return 0

        start = time.perf_counter()
        vectors = self._embedding_svc.embed_batch(all_chunks)
        dimension = vectors.shape[1]

        self._index = faiss.IndexFlatIP(dimension)
        self._index.add(vectors.astype(np.float32))
        self._chunks = all_chunks
        self._metadata = all_metadata

        elapsed = (time.perf_counter() - start) * 1000
        logger.info("faiss_index_built", num_vectors=self._index.ntotal, latency_ms=round(elapsed, 2))

        self._save_faiss()
        self._is_loaded = True
        return len(all_chunks)

    def _save_faiss(self) -> None:
        index_path = Path(settings.faiss_index_path)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(index_path))

        chunks_path = index_path.parent / "faiss_chunks.json"
        with open(chunks_path, "w", encoding="utf-8") as f:
            json.dump({"chunks": self._chunks, "metadata": self._metadata}, f, indent=2)

        logger.info("faiss_index_saved", num_vectors=self._index.ntotal)

    def retrieve(self, query: str, top_k: Optional[int] = None) -> list[dict]:
        k = top_k or settings.rag_top_k

        if not self._is_loaded or self._index is None or self._index.ntotal == 0:
            return []

        query_vector = self._embedding_svc.embed_text(query).reshape(1, -1).astype(np.float32)
        scores, indices = self._index.search(query_vector, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or idx >= len(self._chunks):
                continue
            results.append({
                "chunk": self._chunks[idx],
                "metadata": self._metadata[idx] if idx < len(self._metadata) else {},
                "score": float(score),
            })
        return results

    def retrieve_chunks(self, query: str, top_k: Optional[int] = None) -> list[str]:
        return [r["chunk"] for r in self.retrieve(query, top_k)]

    @property
    def is_ready(self) -> bool:
        return self._is_loaded and self._index is not None and self._index.ntotal > 0

    @property
    def num_vectors(self) -> int:
        return self._index.ntotal if self._index else 0


_rag_instance: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGService()
    return _rag_instance