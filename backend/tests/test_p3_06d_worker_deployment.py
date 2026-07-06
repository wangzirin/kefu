from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
from types import SimpleNamespace

from app.core.auth import CurrentPrincipal
from app.models import Role, Tenant, User, UserRole, WorkerHeartbeat
from app.workers.trusted_inbound_worker_service import resolve_worker_principal, run_worker_service


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "check_p3_06d_worker_deployment.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("check_p3_06d_worker_deployment", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _copy_required_tree(tmp_path: Path) -> Path:
    root = tmp_path / "standard_ops"
    for relative in [
        ".env.example",
        "deploy/docker-compose.yml",
        "deploy/docker-compose.pilot.yml",
        "backend/app/workers/trusted_inbound_worker_service.py",
        "backend/app/workers/trusted_inbound_loop.py",
        "backend/app/services/worker_heartbeats.py",
        "backend/tests/test_p3_06d_worker_deployment.py",
        "docs/P3-06D_WORKER_PROCESS_DEPLOYMENT.md",
    ]:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    return root


def test_p3_06d_worker_deployment_readiness_passes_on_current_project() -> None:
    module = _load_script()

    result = module.run_p3_06d_worker_deployment_readiness(ROOT)

    assert result["status"] == "passed"
    assert result["phase"] == "P3-06D"
    assert result["check"] == "worker_process_deployment"
    assert result["external_call_performed"] is False
    assert result["external_platform_write_performed"] is False
    assert result["production_database_write_performed"] is False
    assert result["errors"] == []


def test_p3_06d_readiness_rejects_worker_service_without_profile(tmp_path: Path) -> None:
    module = _load_script()
    root = _copy_required_tree(tmp_path)
    compose_path = root / "deploy" / "docker-compose.yml"
    compose_text = compose_path.read_text(encoding="utf-8").replace('    profiles: ["worker"]\n', "")
    compose_path.write_text(compose_text, encoding="utf-8")
    pilot_path = root / "deploy" / "docker-compose.pilot.yml"
    pilot_text = pilot_path.read_text(encoding="utf-8").replace('    profiles: ["worker"]\n', "")
    pilot_path.write_text(pilot_text, encoding="utf-8")

    result = module.run_p3_06d_worker_deployment_readiness(root)

    assert result["status"] == "failed"
    assert "trusted-inbound-worker service must use worker profile" in result["errors"]


def test_p3_06d_readiness_rejects_worker_external_write_enabled(tmp_path: Path) -> None:
    module = _load_script()
    root = _copy_required_tree(tmp_path)
    pilot_path = root / "deploy" / "docker-compose.pilot.yml"
    pilot_text = pilot_path.read_text(encoding="utf-8").replace(
        'OUTBOX_EXTERNAL_WRITE_ENABLED: "false"',
        'OUTBOX_EXTERNAL_WRITE_ENABLED: "true"',
    )
    pilot_path.write_text(pilot_text, encoding="utf-8")

    result = module.run_p3_06d_worker_deployment_readiness(root)

    assert result["status"] == "failed"
    assert "trusted-inbound-worker must force OUTBOX_EXTERNAL_WRITE_ENABLED false" in result["errors"]


def test_resolve_worker_principal_uses_tenant_and_user_without_bearer_token(db_session) -> None:
    tenant = Tenant(name="Worker Tenant", slug="worker-tenant")
    user = User(
        tenant=tenant,
        name="Worker User",
        email="worker@example.com",
        password_hash="not-used-by-worker",
    )
    role = Role(tenant_id=1, code="owner", name="Owner")
    db_session.add_all([tenant, user])
    db_session.flush()
    role.tenant_id = tenant.id
    db_session.add(role)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.commit()

    principal = resolve_worker_principal(
        db_session,
        tenant_slug="worker-tenant",
        user_email="worker@example.com",
    )

    assert isinstance(principal, CurrentPrincipal)
    assert principal.tenant.id == tenant.id
    assert principal.user.email == "worker@example.com"
    assert principal.roles == ["owner"]


def test_worker_service_runs_one_empty_cycle_and_writes_heartbeat(db_session) -> None:
    tenant = Tenant(name="Worker Runtime Tenant", slug="worker-runtime")
    user = User(
        tenant=tenant,
        name="Worker Runtime User",
        email="worker-runtime@example.com",
        password_hash="not-used-by-worker",
    )
    role = Role(tenant_id=1, code="admin", name="Admin")
    db_session.add_all([tenant, user])
    db_session.flush()
    role.tenant_id = tenant.id
    db_session.add(role)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.commit()

    result = run_worker_service(
        db_session,
        args=SimpleNamespace(
            tenant_slug="worker-runtime",
            user_email="worker-runtime@example.com",
            worker_id="runtime-worker-1",
            max_cycles=1,
            sleep_seconds=0,
            batch_size=5,
            rate_limit_per_minute=60,
            lease_seconds=30,
            stale_after_seconds=60,
            mode="model_assisted",
            risk_level="medium",
            intent="general_inquiry",
            knowledge_top_k=3,
            model_provider="deterministic",
        ),
    )

    assert result == 0
    heartbeat = db_session.query(WorkerHeartbeat).filter_by(worker_id="runtime-worker-1").one()
    assert heartbeat.tenant_id == tenant.id
    assert heartbeat.worker_type == "trusted_inbound_orchestrator"
    assert heartbeat.status == "idle"
    assert heartbeat.loops_completed == 1
    assert heartbeat.metadata_payload["last_summary"]["external_write"] is False
