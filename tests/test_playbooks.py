from src.backend.routers.playbooks import _infer_team, _infer_time, _infer_tools, _parse_steps


def test_parse_steps_numbered():
    raw = """
1. Isolate the affected host immediately
Disconnect from network and disable remote access.

2. Collect forensic evidence
Use EDR tools to capture memory and disk artifacts.

3. Notify the IR team
Escalate to incident response team lead.
"""
    steps = _parse_steps(raw)
    assert len(steps) == 3
    assert steps[0].step_number == 1
    assert "Isolate" in steps[0].action
    assert steps[1].step_number == 2
    assert steps[2].step_number == 3


def test_parse_steps_fallback_on_empty():
    steps = _parse_steps("")
    assert len(steps) == 1
    assert steps[0].step_number == 1


def test_parse_steps_notes_captured():
    raw = """
1. Block malicious IP at firewall
Check firewall logs and create deny rule for identified C2 IPs.
"""
    steps = _parse_steps(raw)
    assert len(steps) == 1
    assert "firewall" in steps[0].notes.lower() or "firewall" in steps[0].action.lower()


def test_infer_team_containment():
    assert _infer_team("Isolate and quarantine the affected system") == "SOC Tier 2"


def test_infer_team_ir():
    assert _infer_team("Remediate and patch the vulnerability") == "IR Team"


def test_infer_team_management():
    assert _infer_team("Notify and escalate to CISO") == "Management"


def test_infer_team_it_ops():
    assert _infer_team("Restore from backup and recover systems") == "IT Operations"


def test_infer_team_default():
    assert _infer_team("Review logs and investigate") == "SOC Tier 1"


def test_infer_tools_splunk():
    tools = _infer_tools("Search Splunk for suspicious activity")
    assert "Splunk" in tools


def test_infer_tools_crowdstrike():
    tools = _infer_tools("Use CrowdStrike EDR to isolate host")
    assert "CrowdStrike" in tools
    assert "EDR" in tools


def test_infer_tools_empty():
    tools = _infer_tools("Review the incident timeline")
    assert tools == []


def test_infer_time_urgent():
    assert _infer_time("Isolate the host immediately") == 15


def test_infer_time_investigation():
    assert _infer_time("Investigate and analyze the logs") == 60


def test_infer_time_recovery():
    assert _infer_time("Restore systems from backup") == 120


def test_infer_time_default():
    assert _infer_time("Document findings") == 30