import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from src.backend.services.rag_service import RAGService


@pytest.fixture
def rag_service():
    with patch("src.backend.services.rag_service.get_embedding_service") as mock_embed:
        mock_svc = MagicMock()
        mock_svc.dimension = 384
        mock_svc.embed_text.return_value = np.random.rand(384).astype(np.float32)
        mock_svc.embed_batch.return_value = np.random.rand(5, 384).astype(np.float32)
        mock_embed.return_value = mock_svc
        svc = RAGService(embedding_svc=mock_svc)
        yield svc


def test_rag_service_initializes(rag_service):
    assert rag_service is not None
    assert not rag_service.is_ready


def test_build_index_from_documents(rag_service):
    documents = [
        {"threat_id": f"T{i}", "text": f"Threat description number {i}", "source": "MITRE ATT&CK"}
        for i in range(5)
    ]
    total_chunks = rag_service.build_index_from_documents(documents)
    assert total_chunks > 0
    assert rag_service.is_ready
    assert rag_service.num_vectors > 0


def test_retrieve_returns_results(rag_service):
    documents = [
        {"threat_id": "T1059", "text": "PowerShell execution technique used for lateral movement", "source": "MITRE ATT&CK"},
        {"threat_id": "T1078", "text": "Valid accounts used for credential access and persistence", "source": "MITRE ATT&CK"},
    ]
    rag_service.build_index_from_documents(documents)
    results = rag_service.retrieve("PowerShell lateral movement", top_k=2)
    assert isinstance(results, list)
    assert len(results) <= 2
    for r in results:
        assert "chunk" in r
        assert "score" in r
        assert "metadata" in r


def test_retrieve_chunks_returns_strings(rag_service):
    documents = [
        {"threat_id": "T1486", "text": "Ransomware encrypts files for impact", "source": "MITRE ATT&CK"},
    ]
    rag_service.build_index_from_documents(documents)
    chunks = rag_service.retrieve_chunks("ransomware encryption", top_k=1)
    assert isinstance(chunks, list)
    for c in chunks:
        assert isinstance(c, str)


def test_retrieve_empty_when_not_ready():
    with patch("src.backend.services.rag_service.get_embedding_service") as mock_embed:
        mock_svc = MagicMock()
        mock_embed.return_value = mock_svc
        svc = RAGService(embedding_svc=mock_svc)
        results = svc.retrieve("any query")
        assert results == []


def test_build_index_empty_documents(rag_service):
    total = rag_service.build_index_from_documents([])
    assert total == 0