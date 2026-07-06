#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import time
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
PHASE = "H2W-PACK2"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_pack2_full_stack_startup_rehearsal"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_PACK2_FULL_STACK_STARTUP_REHEARSAL.md"
COMPOSE_PILOT = ROOT / "deploy/docker-compose.pilot.yml"
DEFAULT_DATABASE_URL = "postgresql+psycopg://wanfa_ops:change-me-before-pilot@127.0.0.1:5432/wanfa_ops"

CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _run_command(command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout, check=False)


def _command_ok(command: list[str], runner: CommandRunner = _run_command) -> tuple[bool, str]:
    try:
        result = runner(command)
    except Exception as exc:  # pragma: no cover - local CLI differences
        return False, str(exc)
    output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    return result.returncode == 0, output[:1200]


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _safe_db_name() -> str:
    return f"wanfa_ops_pack2_{int(time.time())}_{os.getpid()}"


def _assert_safe_identifier(value: str) -> None:
    if not re.fullmatch(r"[a-z][a-z0-9_]{2,62}", value):
        raise ValueError(f"unsafe database identifier: {value}")


def _admin_url(database_url: str) -> str:
    return make_url(database_url).set(database="postgres").render_as_string(hide_password=False)


def _database_url(database_url: str, db_name: str) -> str:
    return make_url(database_url).set(database=db_name).render_as_string(hide_password=False)


def _create_database(admin_database_url: str, db_name: str) -> None:
    _assert_safe_identifier(db_name)
    engine = create_engine(admin_database_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)'))
            connection.execute(text(f'CREATE DATABASE "{db_name}"'))
    finally:
        engine.dispose()


def _drop_database(admin_database_url: str, db_name: str) -> None:
    _assert_safe_identifier(db_name)
    engine = create_engine(admin_database_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)'))
    finally:
        engine.dispose()


def _run_migrations(database_url: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": database_url,
            "STANDARD_OPS_ENV": "pilot",
            "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED": "false",
            "OUTBOX_EXTERNAL_WRITE_ENABLED": "false",
            "TRUSTED_INBOUND_WORKER_ENABLED": "false",
            "KNOWLEDGE_VECTOR_STORE": "postgres_pgvector_store_v1",
        }
    )
    return _run_command(
        [str(BACKEND_DIR / ".venv/bin/python"), "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
        cwd=BACKEND_DIR,
        env=env,
        timeout=120,
    )


def _start_backend(database_url: str, port: int) -> subprocess.Popen[str]:
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": database_url,
            "REDIS_URL": "redis://127.0.0.1:6379/0",
            "STANDARD_OPS_ENV": "pilot",
            "STANDARD_OPS_ALLOWED_ORIGINS": "http://127.0.0.1:5173,http://localhost:5173",
            "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED": "false",
            "OUTBOX_EXTERNAL_WRITE_ENABLED": "false",
            "TRUSTED_INBOUND_WORKER_ENABLED": "false",
            "KNOWLEDGE_VECTOR_STORE": "postgres_pgvector_store_v1",
        }
    )
    return subprocess.Popen(
        [
            str(BACKEND_DIR / ".venv/bin/uvicorn"),
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=BACKEND_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _http_json(method: str, url: str, payload: dict[str, Any] | None = None, token: str | None = None) -> tuple[int, dict[str, Any]]:
    body = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=5) as response:
            raw = response.read().decode("utf-8")
            return int(response.status), json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            data = {"raw": raw[:300]}
        return int(exc.code), data


def _wait_for_health(base_url: str, process: subprocess.Popen[str], *, timeout_seconds: int = 30) -> tuple[bool, dict[str, Any]]:
    deadline = time.time() + timeout_seconds
    last_error = ""
    while time.time() < deadline:
        if process.poll() is not None:
            return False, {"error": "backend_process_exited", "returncode": process.returncode}
        try:
            status, data = _http_json("GET", f"{base_url}/health")
            if status == 200 and data.get("status") == "ok":
                return True, data
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = str(exc)
        time.sleep(0.5)
    return False, {"error": last_error or "health_timeout"}


def _compose_pilot_safe() -> tuple[bool, list[str]]:
    if not COMPOSE_PILOT.exists():
        return False, ["missing docker-compose.pilot.yml"]
    text = COMPOSE_PILOT.read_text(encoding="utf-8")
    required = [
        'STANDARD_OPS_DEV_BOOTSTRAP_ENABLED: "false"',
        'OUTBOX_EXTERNAL_WRITE_ENABLED: "false"',
        'TRUSTED_INBOUND_WORKER_ENABLED: "false"',
    ]
    missing = [marker for marker in required if marker not in text]
    return not missing, missing


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    readiness = result["readiness"]
    lines = [
        "# H2W-PACK2 全栈首启封版 rehearsal",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- Docker daemon 可用：`{str(readiness['docker_daemon_ready']).lower()}`",
        f"- pilot 配置安全开关完整：`{str(readiness['pilot_compose_safety_ready']).lower()}`",
        f"- 临时 PostgreSQL 数据库创建：`{str(readiness['temporary_database_created']).lower()}`",
        f"- Alembic 迁移完成：`{str(readiness['alembic_migration_passed']).lower()}`",
        f"- 真实后端 HTTP 健康：`{str(readiness['backend_http_healthy']).lower()}`",
        f"- 首任负责人创建完成：`{str(readiness['first_owner_created']).lower()}`",
        f"- 再次创建被锁定：`{str(readiness['second_owner_blocked']).lower()}`",
        f"- 登录与 /me 校验完成：`{str(readiness['login_and_me_passed']).lower()}`",
        f"- 本地部署安全边界通过：`{str(readiness['local_setup_safety_passed']).lower()}`",
        f"- 临时数据库已清理：`{str(readiness['temporary_database_dropped']).lower()}`",
        "",
        "## 停止门禁",
        "",
        "- 首任负责人不能通过真实 HTTP 创建并登录时，不进入客户本地封版候选。",
        "- 开发免登录、真实外发、入站 worker 任一开启时，不进入客户本地封版候选。",
        "- 创建首任负责人后如仍可二次创建管理员，必须阻断。",
        "- 证据文件不得记录密码、token、API key 或真实客户数据。",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(["", "## 警告", ""])
    lines.extend([f"- {item}" for item in result["warnings"]] or ["- 无"])
    lines.extend(
        [
            "",
            "## 输出",
            "",
            f"- `{result['evidence']['summary_json']['path']}`",
            "",
            "## 边界",
            "",
            "- `real_platform_send_performed=false`",
            "- `formal_customer_signoff_performed=false`",
            "- `secrets_logged=false`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_pack2_full_stack_startup_rehearsal(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    database_url: str = DEFAULT_DATABASE_URL,
    runner: CommandRunner = _run_command,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    blockers: list[str] = []
    warnings: list[str] = []
    readiness = {
        "docker_daemon_ready": False,
        "pilot_compose_safety_ready": False,
        "temporary_database_created": False,
        "alembic_migration_passed": False,
        "backend_http_healthy": False,
        "initial_status_open": False,
        "first_owner_created": False,
        "post_setup_locked": False,
        "second_owner_blocked": False,
        "login_and_me_passed": False,
        "local_setup_safety_passed": False,
        "temporary_database_dropped": False,
    }
    observations: dict[str, Any] = {}
    process: subprocess.Popen[str] | None = None
    db_name = _safe_db_name()
    temp_database_url = _database_url(database_url, db_name)
    admin_database_url = _admin_url(database_url)

    docker_ready, docker_output = _command_ok(["docker", "info", "--format", "{{json .ServerVersion}}"], runner)
    readiness["docker_daemon_ready"] = docker_ready
    observations["docker_info"] = docker_output
    if not docker_ready:
        blockers.append("Docker daemon 不可用，无法执行真实 PostgreSQL 首启 rehearsal")

    compose_safe, compose_missing = _compose_pilot_safe()
    readiness["pilot_compose_safety_ready"] = compose_safe
    if not compose_safe:
        blockers.append("pilot compose 缺少安全开关：" + ", ".join(compose_missing))

    try:
        if not blockers:
            _create_database(admin_database_url, db_name)
            readiness["temporary_database_created"] = True

            migration = _run_migrations(temp_database_url)
            observations["alembic_returncode"] = migration.returncode
            observations["alembic_output_tail"] = "\n".join(
                part for part in [migration.stdout[-1000:], migration.stderr[-1000:]] if part
            )
            readiness["alembic_migration_passed"] = migration.returncode == 0
            if migration.returncode != 0:
                blockers.append("Alembic 迁移失败，不能进入首启 HTTP rehearsal")

        if not blockers:
            port = _find_free_port()
            base_url = f"http://127.0.0.1:{port}"
            process = _start_backend(temp_database_url, port)
            healthy, health_payload = _wait_for_health(base_url, process)
            observations["health"] = health_payload
            readiness["backend_http_healthy"] = healthy
            if not healthy:
                blockers.append("真实后端 HTTP 健康检查未通过")

        if not blockers:
            status_code, status_before = _http_json("GET", f"{base_url}/api/auth/local-setup/status")
            observations["status_before"] = {
                key: status_before.get(key)
                for key in [
                    "initialized",
                    "tenant_count",
                    "user_count",
                    "can_create_first_owner",
                    "setup_mode",
                    "local_deployment_ready",
                    "blockers",
                ]
            }
            readiness["initial_status_open"] = (
                status_code == 200
                and status_before.get("can_create_first_owner") is True
                and status_before.get("local_deployment_ready") is True
                and not status_before.get("blockers")
            )
            if not readiness["initial_status_open"]:
                blockers.append("空库首启状态未开放首任负责人创建，或安全边界未 ready")

        token = ""
        if not blockers:
            owner_payload = {
                "tenant_name": "万法常世本地封版演练空间",
                "tenant_slug": "wanfa-pack2-local",
                "owner_name": "本地负责人",
                "email": "owner.pack2@wanfa.local",
                "password": "LocalPack2StrongPassword-202607",
            }
            create_status, create_response = _http_json("POST", f"{base_url}/api/auth/local-setup/owner", owner_payload)
            token = str(create_response.get("access_token") or "")
            readiness["first_owner_created"] = (
                create_status == 201
                and bool(token)
                and create_response.get("user", {}).get("roles") == ["owner"]
            )
            observations["owner_create"] = {
                "status_code": create_status,
                "token_returned": bool(token),
                "roles": create_response.get("user", {}).get("roles"),
                "tenant_slug": create_response.get("user", {}).get("tenant", {}).get("slug"),
            }
            if not readiness["first_owner_created"]:
                blockers.append("首任负责人创建失败")

        if not blockers:
            status_code, status_after = _http_json("GET", f"{base_url}/api/auth/local-setup/status")
            observations["status_after"] = {
                key: status_after.get(key)
                for key in [
                    "initialized",
                    "tenant_count",
                    "user_count",
                    "can_create_first_owner",
                    "setup_mode",
                    "first_owner_creation_locked",
                    "local_deployment_ready",
                    "blockers",
                ]
            }
            readiness["post_setup_locked"] = (
                status_code == 200
                and status_after.get("initialized") is True
                and status_after.get("can_create_first_owner") is False
                and status_after.get("first_owner_creation_locked") is True
                and status_after.get("local_deployment_ready") is True
            )
            if not readiness["post_setup_locked"]:
                blockers.append("首任负责人创建后入口未锁定")

        if not blockers:
            second_status, second_response = _http_json(
                "POST",
                f"{base_url}/api/auth/local-setup/owner",
                {
                    "tenant_name": "重复空间",
                    "tenant_slug": "wanfa-pack2-second",
                    "owner_name": "重复负责人",
                    "email": "owner.second@wanfa.local",
                    "password": "LocalPack2StrongPassword-202607",
                },
            )
            readiness["second_owner_blocked"] = second_status == 409
            observations["second_owner_attempt"] = {
                "status_code": second_status,
                "detail": second_response.get("detail"),
            }
            if not readiness["second_owner_blocked"]:
                blockers.append("系统允许二次创建首任负责人，必须阻断")

        if not blockers:
            login_status, login_response = _http_json(
                "POST",
                f"{base_url}/api/auth/login",
                {
                    "tenant_slug": "wanfa-pack2-local",
                    "email": "owner.pack2@wanfa.local",
                    "password": "LocalPack2StrongPassword-202607",
                },
            )
            login_token = str(login_response.get("access_token") or "")
            me_status, me_response = _http_json("GET", f"{base_url}/api/auth/me", token=login_token)
            readiness["login_and_me_passed"] = (
                login_status == 200
                and bool(login_token)
                and me_status == 200
                and me_response.get("tenant", {}).get("slug") == "wanfa-pack2-local"
                and "owner" in (me_response.get("roles") or [])
            )
            observations["login_and_me"] = {
                "login_status": login_status,
                "login_token_returned": bool(login_token),
                "me_status": me_status,
                "roles": me_response.get("roles"),
                "tenant_slug": me_response.get("tenant", {}).get("slug"),
            }
            if not readiness["login_and_me_passed"]:
                blockers.append("登录或 /me 校验失败")

        readiness["local_setup_safety_passed"] = all(
            [
                readiness["initial_status_open"],
                readiness["first_owner_created"],
                readiness["post_setup_locked"],
                readiness["second_owner_blocked"],
                readiness["login_and_me_passed"],
            ]
        )
    except Exception as exc:
        blockers.append(f"PACK2 rehearsal 异常：{exc}")
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            output = ""
            if process.stdout is not None:
                output = process.stdout.read()[-1600:]
            observations["backend_process"] = {
                "returncode": process.returncode,
                "output_tail": output,
            }
        if readiness["temporary_database_created"]:
            try:
                _drop_database(admin_database_url, db_name)
                readiness["temporary_database_dropped"] = True
            except Exception as exc:
                warnings.append(f"临时数据库清理失败：{exc}")

    if blockers:
        status = "blocked"
    elif not readiness["temporary_database_dropped"]:
        status = "passed_with_cleanup_warning"
    else:
        status = "passed_full_stack_backend_startup_rehearsal"

    result = {
        "phase": PHASE,
        "status": status,
        "readiness": readiness,
        "blockers": blockers,
        "warnings": warnings,
        "observations": observations,
        "evidence": {
            "summary_json": {"path": _display_path(summary_path)},
            "compose_pilot": {"path": _display_path(COMPOSE_PILOT), "present": COMPOSE_PILOT.exists()},
        },
        "boundaries": {
            "temporary_database_used": True,
            "temporary_database_name_logged": False,
            "secrets_logged": False,
            "real_platform_send_performed": False,
            "formal_customer_signoff_performed": False,
            "development_bootstrap_allowed": False,
        },
    }
    _write_json(summary_path, result)
    _write_markdown(DOC_PATH, result)
    return result


def main() -> int:
    result = run_h2w_pack2_full_stack_startup_rehearsal()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
