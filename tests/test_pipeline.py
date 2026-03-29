from src.backend.services.mitre_loader import (
    _base_score,
    _extract_tactics,
    _extract_technique_id,
    parse_techniques,
)
from src.backend.services.threat_scoring import bulk_score
from src.pipeline.transform_threats import clean_text, deduplicate, transform

SAMPLE_ATTACK_PATTERN = {
    "type": "attack-pattern",
    "id": "attack-pattern--01234567-89ab-cdef-0123-456789abcdef",
    "name": "PowerShell",
    "description": "Adversaries may abuse PowerShell commands. (Citation: MITRE T1059)",
    "x_mitre_platforms": ["Windows"],
    "x_mitre_deprecated": False,
    "revoked": False,
    "kill_chain_phases": [
        {"kill_chain_name": "mitre-attack", "phase_name": "execution"}
    ],
    "external_references": [
        {"source_name": "mitre-attack", "external_id": "T1059.001"}
    ],
    "x_mitre_detection": "Monitor PowerShell logs",
    "x_mitre_data_sources": ["Process: Process Creation"],
}


def test_extract_technique_id():
    tid = _extract_technique_id(SAMPLE_ATTACK_PATTERN)
    assert tid == "T1059.001"


def test_extract_technique_id_missing():
    tid = _extract_technique_id({"external_references": []})
    assert tid is None


def test_extract_tactics():
    tactics = _extract_tactics(SAMPLE_ATTACK_PATTERN)
    assert "Execution" in tactics


def test_extract_tactics_empty():
    tactics = _extract_tactics({})
    assert tactics == []


def test_base_score_with_detection():
    score = _base_score(SAMPLE_ATTACK_PATTERN)
    assert 0.0 <= score <= 1.0


def test_base_score_no_detection():
    score = _base_score({"x_mitre_detection": "", "x_mitre_data_sources": []})
    assert score > 0.3


def test_parse_techniques():
    raw = {"objects": [SAMPLE_ATTACK_PATTERN]}
    techniques = parse_techniques(raw)
    assert len(techniques) == 1
    assert techniques[0]["threat_id"] == "T1059.001"
    assert techniques[0]["source"] == "MITRE ATT&CK"


def test_parse_techniques_skips_deprecated():
    deprecated = {**SAMPLE_ATTACK_PATTERN, "x_mitre_deprecated": True}
    raw = {"objects": [deprecated]}
    techniques = parse_techniques(raw)
    assert len(techniques) == 0


def test_parse_techniques_skips_revoked():
    revoked = {**SAMPLE_ATTACK_PATTERN, "revoked": True}
    raw = {"objects": [revoked]}
    techniques = parse_techniques(raw)
    assert len(techniques) == 0


def test_deduplicate():
    threats = [
        {"threat_id": "T1059", "name": "PowerShell"},
        {"threat_id": "T1059", "name": "PowerShell duplicate"},
        {"threat_id": "T1078", "name": "Valid Accounts"},
    ]
    result = deduplicate(threats)
    assert len(result) == 2


def test_deduplicate_empty():
    assert deduplicate([]) == []


def test_clean_text_removes_citations():
    text = "Adversaries use PowerShell (Citation: MITRE T1059) for execution."
    cleaned = clean_text(text)
    assert "Citation" not in cleaned
    assert "PowerShell" in cleaned


def test_clean_text_normalizes_whitespace():
    text = "Too   many    spaces\n\nand newlines"
    cleaned = clean_text(text)
    assert "  " not in cleaned


def test_transform_fills_missing_name():
    threats = [{"threat_id": "T1059", "name": "", "description": "test", "text": "test"}]
    result = transform(threats)
    assert result[0]["name"] == "T1059"


def test_bulk_score_adds_fields():
    threats = [
        {"threat_id": "T1059", "base_score": 0.4, "platforms": ["Windows"], "mitigations": []},
    ]
    result = bulk_score(threats)
    assert "risk_score" in result[0]
    assert "severity" in result[0]
