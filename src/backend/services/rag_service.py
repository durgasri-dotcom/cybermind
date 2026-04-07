from __future__ import annotations

import json
import time
from pathlib import Path

import faiss
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter

from configs.logging_config import get_logger
from configs.settings import settings
from src.backend.services.embedding_service import EmbeddingService, get_embedding_service

logger = get_logger(__name__)


class RAGService:
    def __init__(self, embedding_svc: EmbeddingService | None = None) -> None:
        self._embedding_svc = embedding_svc or get_embedding_service()
        self._index: faiss.IndexFlatIP | None = None
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
            index_path = Path(settings.faiss_index_path)
            if index_path.exists():
                self._load_faiss()
            else:
                self._load_from_postgres()

    def _load_from_postgres(self) -> None:
        import numpy as np

        from src.backend.database.db_models import EmbeddingDB
        from src.backend.database.engine import SessionLocal
        db = SessionLocal()
        rows = db.query(EmbeddingDB).all()
        db.close()
        if not rows:
            logger.warning("no_embeddings_in_postgres")
            self._is_loaded = False
            return
        self._chunks = [r.chunk_text for r in rows]
        self._metadata = [{"threat_id": r.threat_id, "source": r.source, **r.metadata_} for r in rows]
        vectors = np.array([r.vector for r in rows], dtype=np.float32)
        self._index = faiss.IndexFlatIP(vectors.shape[1])
        self._index.add(vectors)
        self._is_loaded = True
        logger.info("faiss_loaded_from_postgres", num_vectors=self._index.ntotal)

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
            with open(chunks_path, encoding="utf-8") as f:
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

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict]:
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

    def retrieve_chunks(self, query: str, top_k: int | None = None) -> list[str]:
        return [r["chunk"] for r in self.retrieve(query, top_k)]

    def retrieve_with_cves(
        self,
        query: str,
        top_k: int | None = None,
        max_cves: int = 3,
    ) -> dict:
        """
        Hybrid retrieval: MITRE ATT&CK chunks from FAISS + relevant CVEs from SQLite.
        Returns both sources merged for LLM context.
        """
        from sqlalchemy import or_

        from src.backend.database.db_models import CveDB
        from src.backend.database.engine import SessionLocal

        # ── MITRE retrieval from FAISS ────────────────────────────────────
        mitre_results = self.retrieve(query=query, top_k=top_k)

        # ── CVE retrieval from SQLite ─────────────────────────────────────
        cve_chunks = []
        try:
            db = SessionLocal()
            keywords = [w.lower() for w in query.split() if len(w) > 4]
            q = db.query(CveDB).filter(
                or_(
                    CveDB.cvss_severity.in_(["CRITICAL", "HIGH"]),
                    *[CveDB.description.ilike(f"%{kw}%") for kw in keywords[:3]],
                )
            ).order_by(CveDB.risk_score.desc()).limit(max_cves)
            cves = q.all()
            for cve in cves:
                techniques = ", ".join(cve.mitre_techniques or []) or "unknown"
                chunk = (
                    f"CVE {cve.cve_id} [{cve.cvss_severity} · CVSS {cve.cvss_score}]: "
                    f"{cve.description[:300]} "
                    f"(CWE: {', '.join(cve.cwe_ids or ['—'])} · "
                    f"MITRE: {techniques})"
                )
                cve_chunks.append(chunk)
            db.close()
        except Exception as e:
            logger.warning("cve_retrieval_failed", error=str(e))

        mitre_chunks = [r["chunk"] for r in mitre_results]

        return {
            "mitre_chunks": mitre_chunks,
            "cve_chunks": cve_chunks,
            "all_chunks": mitre_chunks + cve_chunks,
            "mitre_results": mitre_results,
            "has_cves": len(cve_chunks) > 0,
        }

    @property
    def is_ready(self) -> bool:
        return self._is_loaded and self._index is not None and self._index.ntotal > 0

    @property
    def num_vectors(self) -> int:
        return self._index.ntotal if self._index else 0


_rag_instance: RAGService | None = None


def get_rag_service() -> RAGService:
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGService()
    return _rag_instance

