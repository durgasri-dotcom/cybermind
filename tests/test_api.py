from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.database.engine import Base, get_db
from src.backend.database import db_models  # noqa: F401
from src.backend.main import app

DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


API_KEY = "cybermind-dev-key-change-in-prod"
AUTH = {"X-API-Key": API_KEY}
PREFIX = "/api/v1"


# ── Health ────────────────────────────────────────────────────────────────────

def test_health_returns_healthy(client):
    r = client.get(f"{PREFIX}/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert "services" in data
    assert "database" in data["services"]


def test_health_db_connected(client):
    r = client.get(f"{PREFIX}/health")
    assert r.status_code == 200
    assert r.json()["services"]["database"]["connected"] is True


# ── Alerts ────────────────────────────────────────────────────────────────────

def test_create_alert_requires_auth(client):
    r = client.post(f"{PREFIX}/alerts", json={
        "threat_id": "T1059",
        "title": "Test Alert",
        "description": "Test description",
    })
    assert r.status_code == 401


def test_create_alert_success(client):
    r = client.post(f"{PREFIX}/alerts", headers=AUTH, json={
        "threat_id": "T1059",
        "title": "PowerShell Execution Detected",
        "description": "Suspicious PowerShell activity on host",
        "priority": "P2",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["threat_id"] == "T1059"
    assert data["priority"] == "P2"
    assert data["status"] == "open"
    assert "id" in data


def test_list_alerts_returns_created(client):
    r = client.get(f"{PREFIX}/alerts")
    assert r.status_code == 200
    data = r.json()
    assert "alerts" in data
    assert data["total"] >= 1


def test_get_alert_by_id(client):
    r = client.post(f"{PREFIX}/alerts", headers=AUTH, json={
        "threat_id": "T1078",
        "title": "Valid Account Abuse",
        "description": "Suspicious login from unknown location",
    })
    assert r.status_code == 201
    alert_id = r.json()["id"]
    r2 = client.get(f"{PREFIX}/alerts/{alert_id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == alert_id


def test_get_alert_not_found(client):
    r = client.get(f"{PREFIX}/alerts/99999")
    assert r.status_code == 404


def test_update_alert_status_requires_auth(client):
    r = client.patch(f"{PREFIX}/alerts/1/status", params={"status": "resolved"})
    assert r.status_code == 401


def test_update_alert_status_success(client):
    r = client.post(f"{PREFIX}/alerts", headers=AUTH, json={
        "threat_id": "T1003",
        "title": "Credential Dump",
        "description": "LSASS access detected",
    })
    assert r.status_code == 201
    alert_id = r.json()["id"]
    r2 = client.patch(
        f"{PREFIX}/alerts/{alert_id}/status",
        headers=AUTH,
        params={"status": "resolved"},
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "resolved"


def test_delete_alert_requires_auth(client):
    r = client.post(f"{PREFIX}/alerts", headers=AUTH, json={
        "threat_id": "T1003",
        "title": "Alert to delete",
        "description": "Test",
    })
    alert_id = r.json()["id"]
    r2 = client.delete(f"{PREFIX}/alerts/{alert_id}")
    assert r2.status_code == 401


# ── Entities ──────────────────────────────────────────────────────────────────

def test_create_entity_success(client):
    r = client.post(f"{PREFIX}/entities", headers=AUTH, json={
        "entity_id": "apt29-test",
        "name": "APT29",
        "entity_type": "threat_actor",
        "description": "Russian SVR-linked threat actor",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["entity_id"] == "apt29-test"
    assert data["entity_type"] == "threat_actor"


def test_create_entity_duplicate_returns_409(client):
    client.post(f"{PREFIX}/entities", headers=AUTH, json={
        "entity_id": "apt28-test",
        "name": "APT28",
        "entity_type": "threat_actor",
        "description": "Russian GRU-linked threat actor",
    })
    r = client.post(f"{PREFIX}/entities", headers=AUTH, json={
        "entity_id": "apt28-test",
        "name": "APT28 Duplicate",
        "entity_type": "threat_actor",
        "description": "Duplicate",
    })
    assert r.status_code == 409


def test_list_entities(client):
    r = client.get(f"{PREFIX}/entities")
    assert r.status_code == 200
    data = r.json()
    assert "entities" in data
    assert data["total"] >= 1


def test_get_entity_by_id(client):
    r = client.get(f"{PREFIX}/entities/apt29-test")
    assert r.status_code == 200
    assert r.json()["entity_id"] == "apt29-test"


def test_get_entity_not_found(client):
    r = client.get(f"{PREFIX}/entities/nonexistent-entity")
    assert r.status_code == 404


# ── CVEs ──────────────────────────────────────────────────────────────────────

def test_list_cves_empty(client):
    r = client.get(f"{PREFIX}/cves")
    assert r.status_code == 200
    data = r.json()
    assert "cves" in data
    assert "total" in data


def test_cve_stats(client):
    r = client.get(f"{PREFIX}/cves/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total" in data
    assert "avg_cvss_score" in data
    assert "by_severity" in data


def test_get_cve_not_found(client):
    r = client.get(f"{PREFIX}/cves/CVE-9999-99999")
    assert r.status_code == 404


# ── Analytics ─────────────────────────────────────────────────────────────────

def test_analytics_request_stats(client):
    r = client.get(f"{PREFIX}/analytics/requests")
    assert r.status_code == 200
    data = r.json()
    assert "total_requests" in data
    assert "avg_latency_ms" in data
    assert "top_endpoints" in data
    assert "by_method" in data


def test_analytics_recent_requests(client):
    r = client.get(f"{PREFIX}/analytics/requests/recent")
    assert r.status_code == 200
    data = r.json()
    assert "requests" in data
    assert "total" in data