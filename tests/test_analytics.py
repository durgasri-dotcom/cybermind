from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.backend.database.engine import Base
from src.backend.database import db_models  # noqa: F401
from src.backend.database.db_models import RequestLogDB


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _log(db, method="GET", path="/api/v1/health", status=200, latency=5.0):
    row = RequestLogDB(method=method, path=path, status_code=status, latency_ms=latency)
    db.add(row)
    db.commit()
    return row


def test_create_request_log(db):
    log = _log(db)
    assert log.id is not None
    assert log.method == "GET"
    assert log.status_code == 200


def test_request_log_latency_stored(db):
    log = _log(db, latency=42.5)
    db.refresh(log)
    assert log.latency_ms == 42.5


def test_request_log_timestamp_auto_set(db):
    log = _log(db)
    db.refresh(log)
    assert log.timestamp is not None


def test_multiple_logs_stored(db):
    _log(db, path="/api/v1/alerts", method="GET", status=200)
    _log(db, path="/api/v1/alerts", method="POST", status=201)
    _log(db, path="/api/v1/cves", method="GET", status=200)
    total = db.query(RequestLogDB).count()
    assert total == 3


def test_filter_by_method(db):
    _log(db, method="GET")
    _log(db, method="GET")
    _log(db, method="POST", status=201)
    gets = db.query(RequestLogDB).filter(RequestLogDB.method == "GET").all()
    assert len(gets) == 2


def test_filter_by_status_code(db):
    _log(db, status=200)
    _log(db, status=200)
    _log(db, status=404)
    _log(db, status=500)
    ok = db.query(RequestLogDB).filter(RequestLogDB.status_code == 200).all()
    assert len(ok) == 2


def test_filter_by_path(db):
    _log(db, path="/api/v1/alerts")
    _log(db, path="/api/v1/alerts")
    _log(db, path="/api/v1/cves")
    alerts = db.query(RequestLogDB).filter(RequestLogDB.path == "/api/v1/alerts").all()
    assert len(alerts) == 2


def test_order_by_latency(db):
    _log(db, latency=100.0)
    _log(db, latency=5.0)
    _log(db, latency=50.0)
    rows = db.query(RequestLogDB).order_by(RequestLogDB.latency_ms.desc()).all()
    assert rows[0].latency_ms == 100.0
    assert rows[-1].latency_ms == 5.0


def test_avg_latency(db):
    from sqlalchemy import func
    _log(db, latency=10.0)
    _log(db, latency=20.0)
    _log(db, latency=30.0)
    avg = db.query(func.avg(RequestLogDB.latency_ms)).scalar()
    assert avg == 20.0


def test_count_by_method(db):
    from sqlalchemy import func
    _log(db, method="GET")
    _log(db, method="GET")
    _log(db, method="POST", status=201)
    results = (
        db.query(RequestLogDB.method, func.count(RequestLogDB.id))
        .group_by(RequestLogDB.method)
        .all()
    )
    result_dict = {method: count for method, count in results}
    assert result_dict["GET"] == 2
    assert result_dict["POST"] == 1


def test_top_endpoints(db):
    from sqlalchemy import func
    _log(db, path="/api/v1/cves")
    _log(db, path="/api/v1/cves")
    _log(db, path="/api/v1/cves")
    _log(db, path="/api/v1/alerts")
    top = (
        db.query(RequestLogDB.path, func.count(RequestLogDB.id))
        .group_by(RequestLogDB.path)
        .order_by(func.count(RequestLogDB.id).desc())
        .first()
    )
    assert top[0] == "/api/v1/cves"
    assert top[1] == 3