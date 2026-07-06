import importlib.util
import sys
import ast
import json
from pathlib import Path
from subprocess import CompletedProcess


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


def _load_script(filename: str):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(filename.removesuffix(".py"), SCRIPTS / filename)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _completed(returncode: int = 0, stdout: str = "", stderr: str = "") -> CompletedProcess[str]:
    return CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def _runner(command: list[str]) -> CompletedProcess[str]:
    if command[:2] == ["docker", "info"]:
        return _completed(1, stderr="docker daemon unavailable in test")
    if command[:2] == ["docker", "compose"]:
        return _completed(0)
    if command[:2] == ["bash", "-n"]:
        return _completed(0)
    return _completed(0)


def test_pack1_accepts_safe_customer_template_without_claiming_runtime_completion(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_pack1_local_delivery_rehearsal.py")
    customer_env = tmp_path / "customer.env.example"
    customer_env.write_text(
        "\n".join(
            [
                "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=false",
                "OUTBOX_EXTERNAL_WRITE_ENABLED=false",
                "ADMIN_BOOTSTRAP_PASSWORD=",
                "KNOWLEDGE_VECTOR_STORE=postgres_pgvector_store_v1",
            ]
        ),
        encoding="utf-8",
    )
    local_summary = tmp_path / "local.json"
    local_summary.write_text(
        '{"api_readiness":{"maturity_status":"ready_for_rehearsal"},"boundaries":{"real_platform_send_performed":false}}',
        encoding="utf-8",
    )
    fe3_summary = tmp_path / "fe3.json"
    fe3_summary.write_text('{"status":"passed"}', encoding="utf-8")
    runtime_summary = tmp_path / "runtime.json"
    runtime_summary.write_text('{"status":"blocked_waiting_for_pgvector_runtime"}', encoding="utf-8")

    result = module.run_h2w_pack1_local_delivery_rehearsal(
        output_dir=tmp_path / "out",
        customer_env=customer_env,
        local_maintenance_summary=local_summary,
        fe3_summary=fe3_summary,
        h2w7d_runtime_summary=runtime_summary,
        runner=_runner,
    )

    assert result["status"] == "passed_local_package_candidate_with_runtime_pending"
    assert result["readiness"]["ready_for_local_pilot_package_candidate"] is True
    assert result["readiness"]["docker_daemon_ready"] is False
    assert result["boundaries"]["real_platform_send_performed"] is False
    assert result["boundaries"]["development_bootstrap_allowed_in_customer_template"] is False


def test_model1_defaults_to_no_external_call_and_no_fake_cost(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_model1_bailian_cost_sample.py")

    result = module.run_h2w_model1_bailian_cost_sample(
        output_dir=tmp_path / "model1",
        allow_external_call=False,
        limit=5,
    )

    assert result["status"] == "guarded_external_call_not_allowed"
    assert result["metrics"]["provider_call_performed"] is False
    assert result["readiness"]["ready_for_model_cost_candidate"] is False
    assert result["boundaries"]["deterministic_reply_counted_as_real_model_cost"] is False


def test_trial1_marks_internal_report_without_customer_signoff(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_trial1_internal_100q_rehearsal_report.py")
    h2w11o = tmp_path / "h2w11o.json"
    h2w11o.write_text(
        '{"status":"passed_internal_rehearsal","metrics":{"row_count":100,"dataset_source_type":"internal_synthetic_rehearsal"},"boundaries":{"formal_accuracy_signoff_performed":false}}',
        encoding="utf-8",
    )
    h2w11p = tmp_path / "h2w11p.json"
    h2w11p.write_text(
        '{"status":"passed","readiness":{"ready_for_internal_quality_report_candidate":true,"ready_for_formal_accuracy_signoff":false},"metrics":{"sample_count":100,"final_answer_factuality_rate":1.0,"citation_sufficient_rate":1.0,"forbidden_commitment_pass_rate":1.0,"handoff_correct_rate":1.0},"boundaries":{"retrieval_only_metric_used_as_accuracy":false}}',
        encoding="utf-8",
    )

    result = module.run_h2w_trial1_internal_100q_rehearsal_report(
        output_dir=tmp_path / "out",
        h2w11o_summary=h2w11o,
        h2w11p_summary=h2w11p,
        fe3_summary=tmp_path / "missing_fe3.json",
        pack1_summary=tmp_path / "missing_pack1.json",
        model1_summary=tmp_path / "missing_model1.json",
        h2w7d_runtime_summary=tmp_path / "missing_runtime.json",
    )

    assert result["status"] == "passed_internal_rehearsal_report_with_open_gaps"
    assert result["readiness"]["internal_quality_report_candidate"] is True
    assert result["readiness"]["customer_quality_report_candidate"] is False
    assert result["readiness"]["formal_accuracy_signoff"] is False
    assert result["boundaries"]["internal_rehearsal_not_customer_signoff"] is True
    assert (tmp_path / "out/internal_trial_report.md").exists()


def test_pack2_pilot_compose_keeps_customer_dangerous_switches_off() -> None:
    module = _load_script("check_p3_06u_26h2w_pack2_full_stack_startup_rehearsal.py")

    safe, missing = module._compose_pilot_safe()

    assert safe is True
    assert missing == []


def test_pack2_database_url_helpers_keep_runtime_password_available() -> None:
    module = _load_script("check_p3_06u_26h2w_pack2_full_stack_startup_rehearsal.py")
    source = "postgresql+psycopg://wanfa_ops:secret-value@127.0.0.1:5432/wanfa_ops"

    admin_url = module._admin_url(source)
    temp_url = module._database_url(source, "wanfa_ops_pack2_test")

    assert "***" not in admin_url
    assert "***" not in temp_url
    assert admin_url.endswith("/postgres")
    assert temp_url.endswith("/wanfa_ops_pack2_test")


def test_all_alembic_revision_ids_fit_default_version_column() -> None:
    bad: list[tuple[str, str, str, int]] = []
    for path in sorted((ROOT / "backend/app/migrations/versions").glob("*.py")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not (line.startswith("revision =") or line.startswith("down_revision =")):
                continue
            key, raw_value = line.split("=", 1)
            value = ast.literal_eval(raw_value.strip())
            if isinstance(value, str) and len(value) > 32:
                bad.append((path.name, key.strip(), value, len(value)))

    assert bad == []


def test_pack3_aggregates_ready_evidence_without_customer_signoff(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_pack3_local_pilot_candidate_readiness.py")

    def write_summary(name: str, payload: dict) -> Path:
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    pack2 = write_summary(
        "pack2",
        {
            "status": "passed_full_stack_backend_startup_rehearsal",
            "boundaries": {
                "real_platform_send_performed": False,
                "formal_customer_signoff_performed": False,
                "development_bootstrap_allowed": False,
            },
        },
    )
    pack1 = write_summary("pack1", {"status": "passed_local_package_runtime_rehearsal_ready"})
    fe3 = write_summary("fe3", {"status": "passed"})
    runtime = write_summary("runtime", {"status": "ready_for_runtime_rehearsal"})
    model1 = write_summary(
        "model1",
        {"status": "passed_real_small_sample_cost_rehearsal", "boundaries": {"real_platform_send_performed": False}},
    )
    trial1 = write_summary(
        "trial1",
        {
            "status": "passed_internal_rehearsal_report",
            "metrics": {"dataset_source_type": "internal_synthetic_rehearsal", "question_count": 100},
            "boundaries": {
                "customer_quality_report_candidate": False,
                "formal_accuracy_signoff_performed": False,
                "internal_rehearsal_not_customer_signoff": True,
            },
        },
    )
    customer_env = tmp_path / "customer.env.example"
    customer_env.write_text(
        "\n".join(
            [
                "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=false",
                "OUTBOX_EXTERNAL_WRITE_ENABLED=false",
                "ADMIN_BOOTSTRAP_PASSWORD=",
                "KNOWLEDGE_VECTOR_STORE=postgres_pgvector_store_v1",
            ]
        ),
        encoding="utf-8",
    )
    pilot_compose = tmp_path / "docker-compose.pilot.yml"
    pilot_compose.write_text(
        '\n'.join(
            [
                'STANDARD_OPS_DEV_BOOTSTRAP_ENABLED: "false"',
                'OUTBOX_EXTERNAL_WRITE_ENABLED: "false"',
                'TRUSTED_INBOUND_WORKER_ENABLED: "false"',
            ]
        ),
        encoding="utf-8",
    )

    result = module.run_h2w_pack3_local_pilot_candidate_readiness(
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "pack3.md",
        pack2_summary=pack2,
        pack1_summary=pack1,
        fe3_summary=fe3,
        h2w7d_runtime_summary=runtime,
        model1_summary=model1,
        trial1_summary=trial1,
        customer_env=customer_env,
        pilot_compose=pilot_compose,
    )

    assert result["status"] == "ready_for_local_controlled_pilot_candidate"
    assert result["readiness"]["ready_for_local_controlled_pilot_candidate"] is True
    assert result["readiness"]["formal_customer_signoff_ready"] is False
    assert result["readiness"]["real_platform_send_ready"] is False
    assert result["boundaries"]["internal_rehearsal_not_customer_signoff"] is True


def test_pack3_blocks_when_required_phase_or_safety_boundary_is_missing(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_pack3_local_pilot_candidate_readiness.py")

    bad_pack2 = tmp_path / "pack2.json"
    bad_pack2.write_text(
        json.dumps(
            {
                "status": "passed_full_stack_backend_startup_rehearsal",
                "boundaries": {
                    "real_platform_send_performed": True,
                    "formal_customer_signoff_performed": False,
                    "development_bootstrap_allowed": False,
                },
            }
        ),
        encoding="utf-8",
    )
    customer_env = tmp_path / "customer.env.example"
    customer_env.write_text("STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=true\n", encoding="utf-8")
    pilot_compose = tmp_path / "docker-compose.pilot.yml"
    pilot_compose.write_text('OUTBOX_EXTERNAL_WRITE_ENABLED: "false"\n', encoding="utf-8")

    result = module.run_h2w_pack3_local_pilot_candidate_readiness(
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "pack3.md",
        pack2_summary=bad_pack2,
        pack1_summary=tmp_path / "missing-pack1.json",
        fe3_summary=tmp_path / "missing-fe3.json",
        h2w7d_runtime_summary=tmp_path / "missing-runtime.json",
        model1_summary=tmp_path / "missing-model.json",
        trial1_summary=tmp_path / "missing-trial.json",
        customer_env=customer_env,
        pilot_compose=pilot_compose,
    )

    assert result["status"] == "blocked"
    assert result["readiness"]["ready_for_local_controlled_pilot_candidate"] is False
    assert result["boundary_checks"]["pack2_no_real_platform_send"] is False
    assert result["boundary_checks"]["customer_env_safe"] is False
    assert result["boundary_checks"]["pilot_compose_safe"] is False


def test_pack4_accepts_safe_start_script_without_claiming_customer_signoff(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_pack4_delivery_checklist_and_startup_rehearsal.py")
    pack3 = tmp_path / "pack3.json"
    pack3.write_text(
        json.dumps(
            {
                "status": "ready_for_local_controlled_pilot_candidate",
                "readiness": {
                    "ready_for_local_controlled_pilot_candidate": True,
                    "formal_customer_signoff_ready": False,
                },
                "boundaries": {"real_platform_send_performed": False},
            }
        ),
        encoding="utf-8",
    )
    start_script = tmp_path / "start-local-pilot.sh"
    start_script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                'TEMPLATE_ENV_FILE="customer.env.example"',
                'DEFAULT_ENV_FILE="customer.env"',
                'require_value "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"',
                'require_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"',
                'require_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"',
                'require_value "KNOWLEDGE_VECTOR_STORE" "postgres_pgvector_store_v1"',
                'require_empty "ADMIN_BOOTSTRAP_PASSWORD"',
                'if [[ "$DATABASE_URL_VALUE" == *"replace-with-local-random-password"* ]]; then',
                '  if [[ "${WANFA_ALLOW_TEMPLATE_PASSWORD_FOR_REHEARSAL:-false}" != "true" ]]; then exit 1; fi',
                "fi",
                "python -m alembic -c alembic.ini upgrade head",
                "docker compose up -d --build postgres redis",
                "docker compose up -d --build backend frontend",
            ]
        ),
        encoding="utf-8",
    )
    start_script.chmod(0o755)
    customer_env = tmp_path / "customer.env.example"
    customer_env.write_text(
        "\n".join(
            [
                "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=false",
                "OUTBOX_EXTERNAL_WRITE_ENABLED=false",
                "TRUSTED_INBOUND_WORKER_ENABLED=false",
                "ADMIN_BOOTSTRAP_PASSWORD=",
                "KNOWLEDGE_VECTOR_STORE=postgres_pgvector_store_v1",
                "STANDARD_OPS_POSTGRES_PASSWORD=replace-with-local-random-password",
                "DATABASE_URL=postgresql+psycopg://wanfa_ops:replace-with-local-random-password@postgres:5432/wanfa_ops",
                "BAILIAN_API_KEY=",
                "DEEPSEEK_API_KEY=",
            ]
        ),
        encoding="utf-8",
    )
    compose_base = tmp_path / "docker-compose.yml"
    compose_base.write_text(
        "\n".join(
            [
                "services:",
                "  postgres:",
                "    image: pgvector/pgvector:pg16",
                "  redis:",
                "    image: redis:7-alpine",
                "  backend:",
                "    image: backend",
                "  frontend:",
                "    image: frontend",
            ]
        ),
        encoding="utf-8",
    )
    compose_pilot = tmp_path / "docker-compose.pilot.yml"
    compose_pilot.write_text(
        "\n".join(
            [
                "services:",
                "  backend:",
                '    environment:',
                '      OUTBOX_EXTERNAL_WRITE_ENABLED: "false"',
                '      TRUSTED_INBOUND_WORKER_ENABLED: "false"',
                "  trusted-inbound-worker:",
                '    profiles: ["worker"]',
            ]
        ),
        encoding="utf-8",
    )

    result = module.run_h2w_pack4_delivery_checklist_and_startup_rehearsal(
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "pack4.md",
        pack3_summary=pack3,
        start_script=start_script,
        customer_env_template=customer_env,
        compose_files=[compose_base, compose_pilot],
        runner=_runner,
    )

    assert result["status"] == "ready_for_customer_local_pilot_startup_rehearsal"
    assert result["readiness"]["ready_for_customer_local_pilot_startup_rehearsal"] is True
    assert result["readiness"]["formal_customer_signoff_ready"] is False
    assert result["readiness"]["real_platform_send_ready"] is False
    assert result["readiness"]["worker_profile_excluded_by_default"] is True
    assert result["boundaries"]["desktop_installer_ready"] is False
    assert (tmp_path / "pack4.md").exists()


def test_pack4_blocks_worker_profile_and_unsafe_customer_template(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_pack4_delivery_checklist_and_startup_rehearsal.py")
    pack3 = tmp_path / "pack3.json"
    pack3.write_text(
        json.dumps(
            {
                "status": "ready_for_local_controlled_pilot_candidate",
                "readiness": {
                    "ready_for_local_controlled_pilot_candidate": True,
                    "formal_customer_signoff_ready": False,
                },
                "boundaries": {"real_platform_send_performed": False},
            }
        ),
        encoding="utf-8",
    )
    bad_start = tmp_path / "start-local-pilot.sh"
    bad_start.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                'TEMPLATE_ENV_FILE="customer.env.example"',
                'DEFAULT_ENV_FILE="customer.env"',
                'require_value "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"',
                'require_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"',
                'require_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"',
                'require_value "KNOWLEDGE_VECTOR_STORE" "postgres_pgvector_store_v1"',
                'require_empty "ADMIN_BOOTSTRAP_PASSWORD"',
                "docker compose --profile worker up -d postgres redis backend frontend",
            ]
        ),
        encoding="utf-8",
    )
    customer_env = tmp_path / "customer.env.example"
    customer_env.write_text(
        "\n".join(
            [
                "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=true",
                "OUTBOX_EXTERNAL_WRITE_ENABLED=true",
                "TRUSTED_INBOUND_WORKER_ENABLED=true",
                "ADMIN_BOOTSTRAP_PASSWORD=default-password",
                "KNOWLEDGE_VECTOR_STORE=json",
                "STANDARD_OPS_POSTGRES_PASSWORD=replace-with-local-random-password",
                "DATABASE_URL=postgresql+psycopg://wanfa_ops:replace-with-local-random-password@postgres:5432/wanfa_ops",
                "BAILIAN_API_KEY=",
                "DEEPSEEK_API_KEY=",
            ]
        ),
        encoding="utf-8",
    )
    compose_base = tmp_path / "docker-compose.yml"
    compose_base.write_text("services:\n  postgres:\n    image: pgvector/pgvector:pg16\n", encoding="utf-8")
    compose_pilot = tmp_path / "docker-compose.pilot.yml"
    compose_pilot.write_text('services:\n  backend:\n    environment:\n      OUTBOX_EXTERNAL_WRITE_ENABLED: "true"\n', encoding="utf-8")

    result = module.run_h2w_pack4_delivery_checklist_and_startup_rehearsal(
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "pack4.md",
        pack3_summary=pack3,
        start_script=bad_start,
        customer_env_template=customer_env,
        compose_files=[compose_base, compose_pilot],
        runner=_runner,
    )

    assert result["status"] == "blocked"
    assert result["readiness"]["ready_for_customer_local_pilot_startup_rehearsal"] is False
    assert result["readiness"]["worker_profile_excluded_by_default"] is False
    assert result["checks"]["customer_env_template"]["dev_bootstrap_disabled"] is False
    assert result["checks"]["customer_env_template"]["external_write_disabled"] is False


def test_ops2_generates_customer_monthly_ops_report_without_sla_overclaim(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_ops2_customer_monthly_ops_report.py")

    def write_summary(name: str, payload: dict) -> Path:
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    ops1 = write_summary(
        "ops1",
        {
            "status": "ready_for_after_sales_ops_handoff_rehearsal",
            "readiness": {
                "local_maintenance_rehearsal_ready": True,
                "production_sla_ready": False,
                "formal_customer_signoff_ready": False,
                "real_platform_send_ready": False,
            },
            "boundaries": {
                "real_platform_send_performed": False,
                "formal_customer_signoff_performed": False,
                "remote_control_performed": False,
                "silent_update_performed": False,
            },
        },
    )
    kb2 = write_summary(
        "kb2",
        {
            "status": "ready_for_customer_specific_knowledge_retest_template",
            "readiness": {"formal_customer_signoff_ready": False, "real_platform_send_ready": False},
            "signoff_boundary": {"customer_confirmed": False},
            "boundaries": {"real_platform_send_performed": False, "formal_customer_signoff_performed": False},
        },
    )
    model1 = write_summary(
        "model1",
        {
            "status": "passed_real_small_sample_cost_rehearsal",
            "metrics": {"provider_call_performed": True},
            "boundaries": {"real_platform_send_performed": False, "formal_customer_signoff_performed": False},
        },
    )
    trial1 = write_summary(
        "trial1",
        {
            "status": "passed_internal_rehearsal_report",
            "metrics": {"question_count": 100, "dataset_source_type": "internal_synthetic_rehearsal"},
            "boundaries": {"real_platform_send_performed": False, "formal_accuracy_signoff_performed": False},
        },
    )
    fe4 = write_summary(
        "fe4",
        {
            "status": "ready_for_customer_visible_ui_candidate",
            "boundaries": {"real_platform_send_performed": False, "formal_customer_signoff_performed": False},
        },
    )

    result = module.run_h2w_ops2_customer_monthly_ops_report(
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "ops2.md",
        ops1_summary=ops1,
        kb2_summary=kb2,
        model1_summary=model1,
        trial1_summary=trial1,
        fe4_summary=fe4,
    )

    assert result["status"] == "ready_for_customer_monthly_ops_report_rehearsal"
    assert result["readiness"]["production_sla_ready"] is False
    assert result["readiness"]["formal_customer_signoff_ready"] is False
    assert result["readiness"]["real_platform_send_ready"] is False
    assert result["boundaries"]["raw_customer_text_exported"] is False
    assert (tmp_path / "out/customer_monthly_ops_report.md").exists()
    assert (tmp_path / "out/internal_evidence_summary.json").exists()
    customer_report = (tmp_path / "out/customer_monthly_ops_report.md").read_text(encoding="utf-8")
    assert "生产 SLA 已完成" not in customer_report
    assert "正式客户签收已完成" not in customer_report
    assert "真实外发已开启" not in customer_report


def test_ops2_blocks_real_send_or_sla_overclaim(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_ops2_customer_monthly_ops_report.py")

    bad_ops1 = tmp_path / "ops1.json"
    bad_ops1.write_text(
        json.dumps(
            {
                "status": "ready_for_after_sales_ops_handoff_rehearsal",
                "readiness": {"production_sla_ready": True, "real_platform_send_ready": True},
                "boundaries": {"real_platform_send_performed": True, "remote_control_performed": False},
            }
        ),
        encoding="utf-8",
    )
    safe = tmp_path / "safe.json"
    safe.write_text(
        json.dumps(
            {
                "status": "ready_for_customer_specific_knowledge_retest_template",
                "readiness": {"formal_customer_signoff_ready": False, "real_platform_send_ready": False},
                "boundaries": {"real_platform_send_performed": False, "formal_customer_signoff_performed": False},
            }
        ),
        encoding="utf-8",
    )
    model1 = tmp_path / "model1.json"
    model1.write_text(
        json.dumps({"status": "passed_real_small_sample_cost_rehearsal", "metrics": {"provider_call_performed": True}}),
        encoding="utf-8",
    )
    trial1 = tmp_path / "trial1.json"
    trial1.write_text(
        json.dumps({"status": "passed_internal_rehearsal_report", "metrics": {"question_count": 100}}),
        encoding="utf-8",
    )
    fe4 = tmp_path / "fe4.json"
    fe4.write_text(json.dumps({"status": "ready_for_customer_visible_ui_candidate"}), encoding="utf-8")

    result = module.run_h2w_ops2_customer_monthly_ops_report(
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "ops2.md",
        ops1_summary=bad_ops1,
        kb2_summary=safe,
        model1_summary=model1,
        trial1_summary=trial1,
        fe4_summary=fe4,
    )

    assert result["status"] == "blocked"
    assert result["readiness"]["ready_for_customer_monthly_ops_report_rehearsal"] is False
    assert any("真实平台外发" in item for item in result["blockers"])
    assert any("生产 SLA" in item for item in result["blockers"])


def _write_install2_fixture(tmp_path: Path, *, unsafe: bool = False) -> dict[str, Path]:
    macos = tmp_path / "installers/macos"
    windows = tmp_path / "installers/windows"
    deploy = tmp_path / "deploy"
    macos.mkdir(parents=True)
    windows.mkdir(parents=True)
    deploy.mkdir()
    (macos / "README.md").write_text("候选包装，不是已签名的正式包。\n", encoding="utf-8")
    (macos / "preflight.sh").write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "docker info >/dev/null 2>&1",
                "echo Docker Desktop",
                "echo deploy/customer.env",
                'require_env_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"',
                'require_env_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"',
                'require_env_value "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"',
                'require_env_value "KNOWLEDGE_VECTOR_STORE" "postgres_pgvector_store_v1"',
                'require_env_empty "ADMIN_BOOTSTRAP_PASSWORD"',
                "replace-with-local-random-password",
                "OUTBOX_EXTERNAL_WRITE_ENABLED=true" if unsafe else "echo ok",
            ]
        ),
        encoding="utf-8",
    )
    (macos / "WanfaCustomerService.command").write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "preflight.sh",
                "deploy/start-local-pilot.sh",
                "read -r -p done _",
            ]
        ),
        encoding="utf-8",
    )
    (macos / "uninstall-notes.md").write_text("手动清理，不静默删除客户数据。\n", encoding="utf-8")
    (windows / "README.md").write_text("Windows 候选包装，不是已签名 exe。\n", encoding="utf-8")
    (windows / "Start-WanfaCustomerService.ps1").write_text(
        "\n".join(
            [
                "docker info | Out-Null",
                'throw "Docker Desktop"',
                'throw "deploy\\customer.env"',
                'Require-EnvValue "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"',
                'Require-EnvValue "TRUSTED_INBOUND_WORKER_ENABLED" "false"',
                'Require-EnvValue "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"',
                'Require-EnvValue "KNOWLEDGE_VECTOR_STORE" "postgres_pgvector_store_v1"',
                'Require-EnvEmpty "ADMIN_BOOTSTRAP_PASSWORD"',
                "replace-with-local-random-password",
                "docker-compose.yml",
                "docker-compose.pilot.yml",
            ]
        ),
        encoding="utf-8",
    )
    (windows / "start-wanfa-customer-service.bat").write_text(
        "powershell -File Start-WanfaCustomerService.ps1\n", encoding="utf-8"
    )
    (windows / "uninstall-notes.md").write_text("手动清理，不静默删除客户数据。\n", encoding="utf-8")
    (deploy / "customer.env.example").write_text(
        "\n".join(
            [
                "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=false",
                "OUTBOX_EXTERNAL_WRITE_ENABLED=false",
                "TRUSTED_INBOUND_WORKER_ENABLED=false",
                "ADMIN_BOOTSTRAP_PASSWORD=",
                "KNOWLEDGE_VECTOR_STORE=postgres_pgvector_store_v1",
                "STANDARD_OPS_POSTGRES_PASSWORD=replace-with-local-random-password",
                "DATABASE_URL=postgresql+psycopg://wanfa_ops:replace-with-local-random-password@postgres:5432/wanfa_ops",
                "BAILIAN_API_KEY=",
                "DEEPSEEK_API_KEY=",
            ]
        ),
        encoding="utf-8",
    )
    (deploy / "start-local-pilot.sh").write_text(
        'require_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"\n', encoding="utf-8"
    )
    install1 = tmp_path / "install1.json"
    install1.write_text(
        json.dumps(
            {
                "status": "ready_for_nontechnical_customer_startup_rehearsal",
                "readiness": {"desktop_installer_ready": False},
            }
        ),
        encoding="utf-8",
    )
    return {
        "macos": macos,
        "windows": windows,
        "deploy": deploy,
        "install1": install1,
        "template": deploy / "customer.env.example",
        "customer_env": deploy / "customer.env",
        "start": deploy / "start-local-pilot.sh",
    }


def test_install2_accepts_native_wrapper_candidate_without_signed_installer_claim(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_install2_native_installer_readiness.py")
    paths = _write_install2_fixture(tmp_path)
    module.MACOS_DIR = paths["macos"]
    module.WINDOWS_DIR = paths["windows"]
    module.CUSTOMER_ENV_TEMPLATE = paths["template"]
    module.CUSTOMER_ENV = paths["customer_env"]
    module.START_SCRIPT = paths["start"]

    result = module.run_h2w_install2_native_installer_readiness(
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "install2.md",
        install1_summary=paths["install1"],
        runner=_runner,
    )

    assert result["status"] == "native_wrapper_candidate_ready"
    assert result["readiness"]["native_wrapper_candidate_ready"] is True
    assert result["readiness"]["signed_dmg_exe_ready"] is False
    assert result["readiness"]["desktop_installer_ready"] is False
    assert result["boundaries"]["secret_written_by_installer"] is False
    assert (tmp_path / "install2.md").exists()


def test_install2_blocks_unsafe_wrapper_or_overclaim(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_install2_native_installer_readiness.py")
    paths = _write_install2_fixture(tmp_path, unsafe=True)
    module.MACOS_DIR = paths["macos"]
    module.WINDOWS_DIR = paths["windows"]
    module.CUSTOMER_ENV_TEMPLATE = paths["template"]
    module.CUSTOMER_ENV = paths["customer_env"]
    module.START_SCRIPT = paths["start"]
    (paths["windows"] / "README.md").write_text("正式 exe 已完成\n", encoding="utf-8")

    result = module.run_h2w_install2_native_installer_readiness(
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "install2.md",
        install1_summary=paths["install1"],
        runner=_runner,
    )

    assert result["status"] == "blocked"
    assert result["readiness"]["native_wrapper_candidate_ready"] is False
    assert any("不安全开关" in item for item in result["blockers"])
    assert any("越界承诺" in item for item in result["blockers"])


def test_pilot0_aggregates_internal_candidate_without_overclaim(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_pilot0_readiness.py")

    def write_summary(name: str, payload: dict) -> Path:
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    specs = {
        "pack5": (
            write_summary(
                "pack5",
                {
                    "status": "ready_for_customer_local_pilot_handoff_candidate",
                    "readiness": {"formal_customer_signoff_ready": False, "real_platform_send_ready": False},
                    "boundaries": {"real_platform_send_performed": False},
                },
            ),
            {"ready_for_customer_local_pilot_handoff_candidate"},
        ),
        "fe4": (
            write_summary("fe4", {"status": "ready_for_customer_visible_ui_candidate"}),
            {"ready_for_customer_visible_ui_candidate"},
        ),
        "kb2": (
            write_summary(
                "kb2",
                {
                    "status": "ready_for_customer_specific_knowledge_retest_template",
                    "signoff_boundary": {"customer_confirmed": False},
                },
            ),
            {"ready_for_customer_specific_knowledge_retest_template"},
        ),
        "ops2": (
            write_summary("ops2", {"status": "ready_for_customer_monthly_ops_report_rehearsal"}),
            {"ready_for_customer_monthly_ops_report_rehearsal"},
        ),
        "install2": (
            write_summary(
                "install2",
                {"status": "native_wrapper_candidate_ready", "readiness": {"signed_dmg_exe_ready": False}},
            ),
            {"native_wrapper_candidate_ready"},
        ),
        "trial1": (
            write_summary(
                "trial1",
                {
                    "status": "passed_internal_rehearsal_report",
                    "boundaries": {"internal_rehearsal_not_customer_signoff": True},
                },
            ),
            {"passed_internal_rehearsal_report"},
        ),
        "model1": (
            write_summary("model1", {"status": "passed_real_small_sample_cost_rehearsal"}),
            {"passed_real_small_sample_cost_rehearsal"},
        ),
        "runtime7d": (
            write_summary("runtime", {"status": "ready_for_runtime_rehearsal"}),
            {"ready_for_runtime_rehearsal"},
        ),
    }

    result = module.run_h2w_pilot0_readiness(
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "pilot0.md",
        summary_specs=specs,
    )

    assert result["status"] == "pilot_candidate_ready_with_internal_data"
    assert result["readiness"]["pilot_candidate_ready"] is True
    assert result["readiness"]["internal_data_only"] is True
    assert result["readiness"]["formal_customer_signoff_ready"] is False
    assert result["readiness"]["real_platform_send_ready"] is False
    assert "正式客户验收签收" in result["not_ready_for"]
    assert (tmp_path / "pilot0.md").exists()


def test_pilot0_blocks_real_send_or_signed_installer_overclaim(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_pilot0_readiness.py")
    bad_pack5 = tmp_path / "bad_pack5.json"
    bad_pack5.write_text(
        json.dumps(
            {
                "status": "ready_for_customer_local_pilot_handoff_candidate",
                "readiness": {"real_platform_send_ready": True},
                "boundaries": {"real_platform_send_performed": True},
            }
        ),
        encoding="utf-8",
    )
    safe = tmp_path / "safe.json"
    safe.write_text(json.dumps({"status": "ready_for_customer_visible_ui_candidate"}), encoding="utf-8")
    specs = {
        "pack5": (bad_pack5, {"ready_for_customer_local_pilot_handoff_candidate"}),
        "fe4": (safe, {"ready_for_customer_visible_ui_candidate"}),
    }

    result = module.run_h2w_pilot0_readiness(
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "pilot0.md",
        summary_specs=specs,
    )

    assert result["status"] == "blocked"
    assert result["readiness"]["pilot_candidate_ready"] is False
    assert any("真实平台自动外发" in blocker for blocker in result["blockers"])


def test_pilot2_confirmation_flow_waits_for_customer_return(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_pilot2_customer_confirmation_flow.py")
    template = tmp_path / "template.csv"
    template.write_text(
        "\n".join(
            [
                "signoff_item_id,section,item_name,review_status,confirmed_by,confirmed_at,needs_change",
                "KB2-001,知识范围,业务对象覆盖,pending,,,false",
                "KB2-002,回答策略,售后政策,pending,,,false",
            ]
        ),
        encoding="utf-8",
    )

    result = module.run_h2w_pilot2_customer_confirmation_flow(
        csv_path=template,
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "pilot2.md",
    )

    assert result["status"] == "waiting_customer_confirmation"
    assert result["readiness"]["waiting_customer_confirmation"] is True
    assert result["readiness"]["formal_customer_signoff_ready"] is False
    assert result["boundaries"]["system_prefilled_customer_confirmation"] is False


def test_pilot3_handoff_archive_blocks_secret_assignments(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_pilot3_handoff_archive.py")
    pilot0 = tmp_path / "pilot0.json"
    pilot0.write_text(json.dumps({"status": "pilot_candidate_ready_with_internal_data"}), encoding="utf-8")
    pilot2 = tmp_path / "pilot2.json"
    pilot2.write_text(json.dumps({"status": "waiting_customer_confirmation"}), encoding="utf-8")
    safe_doc = tmp_path / "safe.md"
    safe_doc.write_text("# 说明\n真实外发默认关闭。\n", encoding="utf-8")
    unsafe_doc = tmp_path / "unsafe.env"
    unsafe_doc.write_text("BAILIAN_API_KEY=sk-this-should-not-be-exported\n", encoding="utf-8")

    result = module.run_h2w_pilot3_handoff_archive(
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "pilot3.md",
        pilot0_summary=pilot0,
        pilot2_summary=pilot2,
        include_files=[safe_doc, unsafe_doc],
    )

    assert result["status"] == "blocked"
    assert result["readiness"]["pilot_handoff_archive_candidate"] is False
    assert any("疑似密钥" in blocker for blocker in result["blockers"])


def test_pilot3_handoff_archive_exports_safe_candidate(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_pilot3_handoff_archive.py")
    pilot0 = tmp_path / "pilot0.json"
    pilot0.write_text(json.dumps({"status": "pilot_candidate_ready_with_internal_data"}), encoding="utf-8")
    pilot2 = tmp_path / "pilot2.json"
    pilot2.write_text(json.dumps({"status": "waiting_customer_confirmation"}), encoding="utf-8")
    safe_doc = tmp_path / "safe.md"
    safe_doc.write_text("# 说明\n真实外发默认关闭，当前为试点交付候选。\n", encoding="utf-8")

    result = module.run_h2w_pilot3_handoff_archive(
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "pilot3.md",
        pilot0_summary=pilot0,
        pilot2_summary=pilot2,
        include_files=[safe_doc],
    )

    assert result["status"] == "pilot_handoff_archive_candidate"
    assert result["readiness"]["pilot_handoff_archive_candidate"] is True
    assert result["readiness"]["formal_customer_signoff_ready"] is False
    assert (tmp_path / "out/pilot_handoff_archive_candidate.zip").exists()


def _write_fe4_fixture_files(tmp_path: Path) -> dict[str, Path]:
    required_pages = [
        "运营总览",
        "多渠道对话台",
        "知识库运营",
        "知识缺口",
        "知识评测",
        "质量复盘",
        "渠道接入",
        "运维与告警",
        "自动回复策略",
        "模型路由",
        "账号安全",
    ]
    rows: list[str] = [
        "| 页面 | 区域 | 控件名称 | 控件类型 | 当前可见角色 | 前端文件 | 前端动作 | API client | 后端接口 | 数据变化 | 权限要求 | 成功反馈 | 失败反馈 | 当前状态 | 处理结论 | 验收证据 |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for index in range(55):
        page = required_pages[index % len(required_pages)]
        rows.append(
            "| "
            + " | ".join(
                [
                    page,
                    "主区域",
                    f"控件{index}",
                    "按钮",
                    "负责人",
                    "App.tsx",
                    "真实动作",
                    "client",
                    "GET /api/example",
                    "读取数据",
                    "read",
                    "成功反馈",
                    "失败反馈",
                    "真实可用",
                    "保留",
                    "smoke 证据",
                ]
            )
            + " |"
        )
    matrix = tmp_path / "matrix.md"
    matrix.write_text(
        "# 前端功能真实性矩阵\n\n## 2. 功能真实性明细\n\n" + "\n".join(rows) + "\n\n## 3. 当前阻断项处理结果\n",
        encoding="utf-8",
    )
    workbench = tmp_path / "ConversationWorkbenchPanel.tsx"
    workbench.write_text(
        '<section data-function-reality="no-fake-chat-actions"><div className="service-thread-item">转人工</div><div className="service-message-stream">消息流</div><button>保存接管回复</button></section>',
        encoding="utf-8",
    )
    app = tmp_path / "App.tsx"
    app.write_text("const copy = '真实外发关闭，模型来源，检索与成本门禁';", encoding="utf-8")
    navigation = tmp_path / "navigation.ts"
    navigation.write_text(
        "\n".join(
            [
                '{ label: "运营总览", href: "#overview" }',
                '{ label: "接待工作台", href: "#live" }',
                '{ label: "知识库运营", href: "#knowledge" }',
                '{ label: "质量诊断", href: "#quality" }',
                '{ label: "渠道状态", href: "#channels" }',
                '{ label: "账号安全", href: "#settings" }',
                '{ label: "会话收件箱", href: "#conversations", hiddenFromSidebar: true }',
                '{ label: "人工审核", href: "#reviews", hiddenFromSidebar: true }',
                '{ label: "待发送草稿", href: "#outbox", hiddenFromSidebar: true }',
                '{ label: "工单/SLA", href: "#tickets", hiddenFromSidebar: true }',
            ]
        ),
        encoding="utf-8",
    )
    fe3 = tmp_path / "fe3.json"
    fe3.write_text(
        json.dumps({"status": "passed", "boundaries": {"real_platform_send_performed": False}}),
        encoding="utf-8",
    )
    deep = tmp_path / "deep.json"
    deep.write_text(json.dumps({"issues": [], "runtimeErrors": [], "results": []}), encoding="utf-8")
    pack4 = tmp_path / "pack4.json"
    pack4.write_text(
        json.dumps(
            {
                "status": "ready_for_customer_local_pilot_startup_rehearsal",
                "boundaries": {"formal_customer_signoff_performed": False},
            }
        ),
        encoding="utf-8",
    )
    return {
        "matrix": matrix,
        "workbench": workbench,
        "app": app,
        "navigation": navigation,
        "fe3": fe3,
        "deep": deep,
        "pack4": pack4,
    }


def test_fe4_customer_visible_ui_gate_accepts_real_workflow_boundary(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_fe4_customer_ui_sealed_candidate.py")
    files = _write_fe4_fixture_files(tmp_path)

    result = module.run_h2w_fe4_customer_ui_sealed_candidate(
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "fe4.md",
        fe3_summary=files["fe3"],
        deep_audit_summary=files["deep"],
        pack4_summary=files["pack4"],
        matrix_path=files["matrix"],
        app_path=files["app"],
        workbench_path=files["workbench"],
        navigation_path=files["navigation"],
    )

    assert result["status"] == "ready_for_customer_visible_ui_candidate"
    assert result["readiness"]["ready_for_customer_visible_ui_candidate"] is True
    assert result["readiness"]["ready_for_customer_formal_signoff"] is False
    assert result["boundaries"]["real_platform_send_performed"] is False
    assert (tmp_path / "fe4.md").exists()


def test_fe4_customer_visible_ui_gate_blocks_customer_visible_engineering_terms(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_fe4_customer_ui_sealed_candidate.py")
    files = _write_fe4_fixture_files(tmp_path)
    files["app"].write_text("const copy = '真实外发关闭 Provider：dashscope';", encoding="utf-8")

    result = module.run_h2w_fe4_customer_ui_sealed_candidate(
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "fe4.md",
        fe3_summary=files["fe3"],
        deep_audit_summary=files["deep"],
        pack4_summary=files["pack4"],
        matrix_path=files["matrix"],
        app_path=files["app"],
        workbench_path=files["workbench"],
        navigation_path=files["navigation"],
    )

    assert result["status"] == "blocked"
    assert any("工程词" in blocker for blocker in result["blockers"])


def _write_pack5_fixture_files(tmp_path: Path) -> dict[str, Path]:
    def write_summary(name: str, payload: dict) -> Path:
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    pack2 = write_summary(
        "pack2",
        {
            "status": "passed_full_stack_backend_startup_rehearsal",
            "boundaries": {"real_platform_send_performed": False, "formal_customer_signoff_performed": False},
        },
    )
    pack3 = write_summary(
        "pack3",
        {
            "status": "ready_for_local_controlled_pilot_candidate",
            "readiness": {"formal_customer_signoff_ready": False},
            "boundaries": {"real_platform_send_performed": False},
        },
    )
    pack4 = write_summary(
        "pack4",
        {
            "status": "ready_for_customer_local_pilot_startup_rehearsal",
            "readiness": {"desktop_installer_ready": False},
            "boundaries": {"formal_customer_signoff_performed": False},
        },
    )
    fe4 = write_summary(
        "fe4",
        {
            "status": "ready_for_customer_visible_ui_candidate",
            "boundaries": {"real_platform_send_performed": False},
        },
    )
    fe4_click = write_summary(
        "fe4_click",
        {
            "status": "passed_customer_visible_click_qa",
            "owner_login_performed_through_ui": True,
            "demo_mode_used": False,
            "external_platform_write_performed": False,
        },
    )
    runtime = write_summary("runtime", {"status": "ready_for_runtime_rehearsal"})
    model1 = write_summary("model1", {"status": "passed_real_small_sample_cost_rehearsal"})
    trial1 = write_summary(
        "trial1",
        {
            "status": "passed_internal_rehearsal_report",
            "boundaries": {"internal_rehearsal_not_customer_signoff": True},
        },
    )

    start_script = tmp_path / "start-local-pilot.sh"
    start_script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                'DEFAULT_ENV_FILE="customer.env"',
                'TEMPLATE_ENV_FILE="customer.env.example"',
                'require_value "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"',
                'require_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"',
                'require_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"',
                'require_value "KNOWLEDGE_VECTOR_STORE" "postgres_pgvector_store_v1"',
                'require_empty "ADMIN_BOOTSTRAP_PASSWORD"',
                'if [[ "$DATABASE_URL_VALUE" == *"replace-with-local-random-password"* ]]; then',
                '  if [[ "${WANFA_ALLOW_TEMPLATE_PASSWORD_FOR_REHEARSAL:-false}" != "true" ]]; then exit 1; fi',
                "fi",
                "python -m alembic -c alembic.ini upgrade head",
                "docker compose up -d --build postgres redis",
                "docker compose up -d --build backend frontend",
            ]
        ),
        encoding="utf-8",
    )
    customer_env = tmp_path / "customer.env.example"
    customer_env.write_text(
        "\n".join(
            [
                "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=false",
                "OUTBOX_EXTERNAL_WRITE_ENABLED=false",
                "TRUSTED_INBOUND_WORKER_ENABLED=false",
                "ADMIN_BOOTSTRAP_PASSWORD=",
                "KNOWLEDGE_VECTOR_STORE=postgres_pgvector_store_v1",
                "STANDARD_OPS_POSTGRES_PASSWORD=replace-with-local-random-password",
                "DATABASE_URL=postgresql+psycopg://wanfa_ops:replace-with-local-random-password@postgres:5432/wanfa_ops",
                "MODEL_BUDGET_GUARD_ENABLED=true",
                "BAILIAN_API_KEY=",
                "DEEPSEEK_API_KEY=",
            ]
        ),
        encoding="utf-8",
    )
    compose_base = tmp_path / "docker-compose.yml"
    compose_base.write_text(
        "\n".join(
            [
                "services:",
                "  postgres:",
                "    image: pgvector/pgvector:pg16",
                "  redis:",
                "    image: redis:7-alpine",
                "  backend:",
                "    image: backend",
                "  frontend:",
                "    image: frontend",
            ]
        ),
        encoding="utf-8",
    )
    compose_pilot = tmp_path / "docker-compose.pilot.yml"
    compose_pilot.write_text(
        "\n".join(
            [
                "services:",
                "  backend:",
                "    environment:",
                '      OUTBOX_EXTERNAL_WRITE_ENABLED: "false"',
                '      TRUSTED_INBOUND_WORKER_ENABLED: "false"',
                "  trusted-inbound-worker:",
                '    profiles: ["worker"]',
            ]
        ),
        encoding="utf-8",
    )
    doc_paths: list[Path] = []
    for name in ["产品介绍", "客户使用手册", "服务体系介绍", "正式部署后运营模式手册"]:
        path = tmp_path / f"{name}.md"
        path.write_text(f"# {name}\n", encoding="utf-8")
        doc_paths.append(path)
    internal_docs: list[Path] = []
    for name in ["README.md", "PACK3.md", "PACK4.md", "FE4.md", "MASTER.md"]:
        path = tmp_path / name
        path.write_text(f"# {name}\n", encoding="utf-8")
        internal_docs.append(path)

    return {
        "pack2": pack2,
        "pack3": pack3,
        "pack4": pack4,
        "fe4": fe4,
        "fe4_click": fe4_click,
        "runtime": runtime,
        "model1": model1,
        "trial1": trial1,
        "start_script": start_script,
        "customer_env": customer_env,
        "compose_base": compose_base,
        "compose_pilot": compose_pilot,
        "customer_docs": doc_paths,
        "internal_docs": internal_docs,
    }


def test_pack5_accepts_safe_customer_handoff_package_without_customer_signoff(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_pack5_customer_handoff_package.py")
    files = _write_pack5_fixture_files(tmp_path)

    result = module.run_h2w_pack5_customer_handoff_package(
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "pack5.md",
        pack2_summary=files["pack2"],
        pack3_summary=files["pack3"],
        pack4_summary=files["pack4"],
        fe4_summary=files["fe4"],
        fe4_click_summary=files["fe4_click"],
        runtime_summary=files["runtime"],
        model1_summary=files["model1"],
        trial1_summary=files["trial1"],
        start_script=files["start_script"],
        customer_env_template=files["customer_env"],
        concrete_customer_env=tmp_path / "customer.env",
        compose_files=[files["compose_base"], files["compose_pilot"]],
        required_customer_docs=files["customer_docs"],
        required_internal_docs=files["internal_docs"],
        runner=_runner,
    )

    assert result["status"] == "ready_for_customer_local_pilot_handoff_candidate"
    assert result["readiness"]["ready_for_customer_local_pilot_handoff_candidate"] is True
    assert result["readiness"]["formal_customer_signoff_ready"] is False
    assert result["readiness"]["real_platform_send_ready"] is False
    assert result["readiness"]["desktop_installer_ready"] is False
    assert result["boundaries"]["customer_specific_knowledge_ready"] is False
    assert (tmp_path / "pack5.md").exists()


def test_pack5_blocks_missing_browser_evidence_and_secret_template(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_pack5_customer_handoff_package.py")
    files = _write_pack5_fixture_files(tmp_path)
    files["customer_env"].write_text(
        "\n".join(
            [
                "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=false",
                "OUTBOX_EXTERNAL_WRITE_ENABLED=false",
                "TRUSTED_INBOUND_WORKER_ENABLED=false",
                "ADMIN_BOOTSTRAP_PASSWORD=",
                "KNOWLEDGE_VECTOR_STORE=postgres_pgvector_store_v1",
                "STANDARD_OPS_POSTGRES_PASSWORD=replace-with-local-random-password",
                "DATABASE_URL=postgresql+psycopg://wanfa_ops:replace-with-local-random-password@postgres:5432/wanfa_ops",
                "MODEL_BUDGET_GUARD_ENABLED=true",
                "BAILIAN_API_KEY=should-not-be-in-template",
                "DEEPSEEK_API_KEY=",
            ]
        ),
        encoding="utf-8",
    )

    result = module.run_h2w_pack5_customer_handoff_package(
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "pack5.md",
        pack2_summary=files["pack2"],
        pack3_summary=files["pack3"],
        pack4_summary=files["pack4"],
        fe4_summary=files["fe4"],
        fe4_click_summary=tmp_path / "missing-fe4-click.json",
        runtime_summary=files["runtime"],
        model1_summary=files["model1"],
        trial1_summary=files["trial1"],
        start_script=files["start_script"],
        customer_env_template=files["customer_env"],
        concrete_customer_env=tmp_path / "customer.env",
        compose_files=[files["compose_base"], files["compose_pilot"]],
        required_customer_docs=files["customer_docs"],
        required_internal_docs=files["internal_docs"],
        runner=_runner,
    )

    assert result["status"] == "blocked"
    assert result["readiness"]["ready_for_customer_local_pilot_handoff_candidate"] is False
    assert result["readiness"]["fe4_browser_click_ready"] is False
    assert result["checks"]["customer_env_template"]["model_api_keys_empty"] is False


def test_kb1_runs_customer_specific_knowledge_package_rehearsal_without_formal_signoff(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_kb1_customer_specific_knowledge_package_rehearsal.py")

    result = module.run_h2w_kb1_customer_specific_knowledge_package_rehearsal(
        package_path=tmp_path / "kb1_package.json",
        output_dir=tmp_path / "kb1",
        doc_path=tmp_path / "kb1.md",
        pack5_summary_path=tmp_path / "missing_pack5.json",
    )

    assert result["status"] == "ready_for_customer_specific_knowledge_package_rehearsal"
    assert result["readiness"]["ready_for_customer_specific_knowledge_import_candidate"] is True
    assert result["readiness"]["customer_specific_knowledge_ready"] is False
    assert result["readiness"]["formal_customer_signoff_ready"] is False
    assert result["backend_rehearsal"]["preview"]["operation_counts"]["create"] == 17
    assert result["backend_rehearsal"]["import"]["safety"]["provider_call_performed"] is False
    assert result["backend_rehearsal"]["import"]["safety"]["external_write_performed"] is False
    assert result["backend_rehearsal"]["rollback"]["rollback_status"] == "rolled_back"
    assert result["backend_rehearsal"]["rollback"]["active_document_count_after_rollback"] == 0
    assert (tmp_path / "kb1.md").exists()


def test_kb1_blocks_customer_signoff_overclaim_and_skips_backend(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_kb1_customer_specific_knowledge_package_rehearsal.py")
    package = module._default_customer_specific_package()
    package["notes"] = "客户已经正式签收 customer_confirmed=true"
    package_path = tmp_path / "bad_kb1_package.json"
    package_path.write_text(json.dumps(package, ensure_ascii=False), encoding="utf-8")

    result = module.run_h2w_kb1_customer_specific_knowledge_package_rehearsal(
        package_path=package_path,
        output_dir=tmp_path / "bad_kb1",
        doc_path=tmp_path / "bad_kb1.md",
        run_backend=False,
    )

    assert result["status"] == "blocked"
    assert result["backend_rehearsal"] is None
    assert result["readiness"]["ready_for_customer_specific_knowledge_import_candidate"] is False
    assert result["readiness"]["formal_customer_signoff_ready"] is False
    assert any("customer_confirmed" in blocker for blocker in result["blockers"])


def _write_install1_fixture_files(tmp_path: Path) -> dict[str, Path]:
    pack5 = tmp_path / "pack5.json"
    pack5.write_text(
        json.dumps(
            {
                "status": "ready_for_customer_local_pilot_handoff_candidate",
                "readiness": {
                    "ready_for_customer_local_pilot_handoff_candidate": True,
                    "desktop_installer_ready": False,
                    "formal_customer_signoff_ready": False,
                    "real_platform_send_ready": False,
                },
                "boundaries": {"real_platform_send_performed": False},
            }
        ),
        encoding="utf-8",
    )
    kb1 = tmp_path / "kb1.json"
    kb1.write_text(
        json.dumps(
            {
                "status": "ready_for_customer_specific_knowledge_package_rehearsal",
                "readiness": {
                    "ready_for_customer_specific_knowledge_import_candidate": True,
                    "customer_specific_knowledge_ready": False,
                    "formal_customer_signoff_ready": False,
                },
                "boundaries": {
                    "formal_customer_signoff_performed": False,
                    "real_platform_send_performed": False,
                },
            }
        ),
        encoding="utf-8",
    )
    start_script = tmp_path / "start-local-pilot.sh"
    start_script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                'DEFAULT_ENV_FILE="customer.env"',
                'TEMPLATE_ENV_FILE="customer.env.example"',
                'require_value "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"',
                'require_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"',
                'require_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"',
                'require_empty "ADMIN_BOOTSTRAP_PASSWORD"',
                "python -m alembic -c alembic.ini upgrade head",
                "docker compose up -d --build postgres redis",
                "docker compose up -d --build backend frontend",
            ]
        ),
        encoding="utf-8",
    )
    command_launcher = tmp_path / "start-local-pilot.command"
    command_launcher.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"',
                'echo "正在启动万法常世客服中台本地试点"',
                'echo "请确认 Docker Desktop 已经启动"',
                'echo "如果还没有填写 deploy/customer.env，请先从 customer.env.example 复制"',
                '"$SCRIPT_DIR/start-local-pilot.sh" "$SCRIPT_DIR/customer.env"',
                'echo "前端工作台：http://127.0.0.1:5173"',
                'echo "真实外发默认关闭"',
                'read -r -p "按回车键关闭窗口..." _',
            ]
        ),
        encoding="utf-8",
    )
    command_launcher.chmod(0o755)
    quick_start_doc = tmp_path / "quick-start.md"
    quick_start_doc.write_text(
        "\n".join(
            [
                "# 本地试点启动说明",
                "",
                "1. 安装并启动 Docker Desktop。",
                "2. 复制 `deploy/customer.env.example` 为 `deploy/customer.env`。",
                "3. 替换本地随机数据库密码。",
                "4. 双击 `deploy/start-local-pilot.command`。",
                "5. 打开 `http://127.0.0.1:5173` 创建首任负责人账号。",
                "6. 真实外发默认关闭，入站 worker 默认关闭。",
                "7. 先生成诊断包和备份，再导入知识资料。",
            ]
        ),
        encoding="utf-8",
    )
    customer_env = tmp_path / "customer.env.example"
    customer_env.write_text(
        "\n".join(
            [
                "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=false",
                "OUTBOX_EXTERNAL_WRITE_ENABLED=false",
                "TRUSTED_INBOUND_WORKER_ENABLED=false",
                "ADMIN_BOOTSTRAP_PASSWORD=",
                "KNOWLEDGE_VECTOR_STORE=postgres_pgvector_store_v1",
                "STANDARD_OPS_POSTGRES_PASSWORD=replace-with-local-random-password",
                "DATABASE_URL=postgresql+psycopg://wanfa_ops:replace-with-local-random-password@postgres:5432/wanfa_ops",
                "BAILIAN_API_KEY=",
                "DEEPSEEK_API_KEY=",
            ]
        ),
        encoding="utf-8",
    )
    return {
        "pack5": pack5,
        "kb1": kb1,
        "start_script": start_script,
        "command_launcher": command_launcher,
        "quick_start_doc": quick_start_doc,
        "customer_env": customer_env,
    }


def test_install1_accepts_nontechnical_launcher_without_claiming_native_installer(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_install1_nontechnical_customer_starter.py")
    files = _write_install1_fixture_files(tmp_path)

    result = module.run_h2w_install1_nontechnical_customer_starter(
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "install1.md",
        pack5_summary=files["pack5"],
        kb1_summary=files["kb1"],
        start_script=files["start_script"],
        command_launcher=files["command_launcher"],
        quick_start_doc=files["quick_start_doc"],
        customer_env_template=files["customer_env"],
        concrete_customer_env=tmp_path / "customer.env",
        runner=_runner,
    )

    assert result["status"] == "ready_for_nontechnical_customer_startup_rehearsal"
    assert result["readiness"]["ready_for_nontechnical_customer_startup_rehearsal"] is True
    assert result["readiness"]["desktop_installer_ready"] is False
    assert result["readiness"]["native_installer_ready"] is False
    assert result["readiness"]["formal_customer_signoff_ready"] is False
    assert result["boundaries"]["real_platform_send_performed"] is False
    assert result["boundaries"]["customer_env_created_or_modified"] is False
    assert (tmp_path / "install1.md").exists()


def test_install1_blocks_overclaim_and_unsafe_launcher(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_install1_nontechnical_customer_starter.py")
    files = _write_install1_fixture_files(tmp_path)
    files["command_launcher"].write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                'echo "完整桌面安装器已完成，真实外发已开启"',
                '"$SCRIPT_DIR/start-local-pilot.sh" --profile worker',
            ]
        ),
        encoding="utf-8",
    )
    files["quick_start_doc"].write_text("正式客户签收已完成，真实平台自动外发已接通。", encoding="utf-8")

    result = module.run_h2w_install1_nontechnical_customer_starter(
        output_dir=tmp_path / "out",
        doc_path=tmp_path / "install1.md",
        pack5_summary=files["pack5"],
        kb1_summary=files["kb1"],
        start_script=files["start_script"],
        command_launcher=files["command_launcher"],
        quick_start_doc=files["quick_start_doc"],
        customer_env_template=files["customer_env"],
        concrete_customer_env=tmp_path / "customer.env",
        runner=_runner,
    )

    assert result["status"] == "blocked"
    assert result["readiness"]["ready_for_nontechnical_customer_startup_rehearsal"] is False
    assert result["checks"]["command_launcher"]["does_not_enable_worker_profile"] is False
    assert result["checks"]["customer_copy"]["no_overclaim_phrases"] is False


def _write_ops1_fixture_files(tmp_path: Path) -> dict[str, Path]:
    install1 = tmp_path / "install1.json"
    install1.write_text(
        json.dumps(
            {
                "status": "ready_for_nontechnical_customer_startup_rehearsal",
                "readiness": {
                    "ready_for_nontechnical_customer_startup_rehearsal": True,
                    "formal_customer_signoff_ready": False,
                    "real_platform_send_ready": False,
                    "desktop_installer_ready": False,
                },
                "boundaries": {
                    "real_platform_send_performed": False,
                    "formal_customer_signoff_performed": False,
                    "customer_env_created_or_modified": False,
                },
            }
        ),
        encoding="utf-8",
    )
    pack5 = tmp_path / "pack5.json"
    pack5.write_text(
        json.dumps(
            {
                "status": "ready_for_customer_local_pilot_handoff_candidate",
                "readiness": {
                    "ready_for_customer_local_pilot_handoff_candidate": True,
                    "formal_customer_signoff_ready": False,
                    "real_platform_send_ready": False,
                    "desktop_installer_ready": False,
                },
                "boundaries": {"real_platform_send_performed": False},
            }
        ),
        encoding="utf-8",
    )
    kb1 = tmp_path / "kb1.json"
    kb1.write_text(
        json.dumps(
            {
                "status": "ready_for_customer_specific_knowledge_package_rehearsal",
                "readiness": {
                    "ready_for_customer_specific_knowledge_import_candidate": True,
                    "customer_specific_knowledge_ready": False,
                    "formal_customer_signoff_ready": False,
                },
                "boundaries": {
                    "real_customer_data_used": False,
                    "provider_call_performed": False,
                    "real_platform_send_performed": False,
                    "formal_customer_signoff_performed": False,
                },
            }
        ),
        encoding="utf-8",
    )
    local_maintenance = tmp_path / "local_maintenance.json"
    local_maintenance.write_text(
        json.dumps(
            {
                "api_readiness": {
                    "maturity_status": "ready_for_rehearsal",
                    "ready_for_customer_maintenance_rehearsal": True,
                    "counts": {
                        "diagnostic_intake_accepted": 1,
                        "remediation_request_total": 1,
                        "remediation_update_plan_prepared": 1,
                        "signed_update_package_staged": 1,
                        "local_backup_verified": 1,
                        "restore_dry_run_total": 1,
                        "maintenance_audit_event_total": 8,
                    },
                    "blocker_count": 0,
                    "safety": {
                        "external_write_performed": False,
                        "remote_control_performed": False,
                        "silent_update_performed": False,
                        "automatic_update_performed": False,
                        "automatic_upload_performed": False,
                        "manual_transfer_required": True,
                        "customer_admin_confirmation_required": True,
                    },
                },
                "boundaries": {
                    "real_platform_send_performed": False,
                    "remote_control_performed": False,
                    "silent_update_performed": False,
                },
            }
        ),
        encoding="utf-8",
    )
    remote_sop = tmp_path / "remote_sop.md"
    remote_sop.write_text(
        "诊断包优先\n只读优先\n变更二次授权\n客户确认\n备份\n回滚\n权限回收\n禁止命令\n真实外发默认关闭\n",
        encoding="utf-8",
    )
    internal_ops = tmp_path / "internal_ops.md"
    internal_ops.write_text(
        "诊断包\n知识库更新\n回滚\n备份\nP1\nP2\n月度质量复盘\n客户确认\n",
        encoding="utf-8",
    )
    customer_quick_start = tmp_path / "quick_start.md"
    customer_quick_start.write_text("Docker Desktop\ncustomer.env\n首任负责人\n诊断包\n备份\n真实外发默认关闭\n", encoding="utf-8")
    return {
        "install1": install1,
        "pack5": pack5,
        "kb1": kb1,
        "local_maintenance": local_maintenance,
        "remote_sop": remote_sop,
        "internal_ops": internal_ops,
        "customer_quick_start": customer_quick_start,
    }


def test_ops1_accepts_after_sales_handoff_rehearsal_without_remote_control_claim(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_ops1_after_sales_handoff_rehearsal.py")
    files = _write_ops1_fixture_files(tmp_path)

    result = module.run_h2w_ops1_after_sales_handoff_rehearsal(
        output_dir=tmp_path / "ops1",
        doc_path=tmp_path / "ops1.md",
        install1_summary=files["install1"],
        pack5_summary=files["pack5"],
        kb1_summary=files["kb1"],
        local_maintenance_summary=files["local_maintenance"],
        remote_maintenance_sop=files["remote_sop"],
        internal_ops_plan=files["internal_ops"],
        customer_quick_start_doc=files["customer_quick_start"],
    )

    assert result["status"] == "ready_for_after_sales_ops_handoff_rehearsal"
    assert result["readiness"]["ready_for_after_sales_ops_handoff_rehearsal"] is True
    assert result["readiness"]["local_maintenance_rehearsal_ready"] is True
    assert result["readiness"]["diagnostic_upload_package_ready"] is True
    assert result["readiness"]["backup_rehearsal_ready"] is True
    assert result["readiness"]["restore_dry_run_ready"] is True
    assert result["readiness"]["formal_customer_signoff_ready"] is False
    assert result["readiness"]["production_sla_ready"] is False
    assert result["boundaries"]["remote_control_performed"] is False
    assert result["boundaries"]["silent_update_performed"] is False
    assert result["boundaries"]["real_platform_send_performed"] is False
    assert (tmp_path / "ops1.md").exists()


def test_ops1_blocks_remote_control_silent_update_and_sla_overclaim(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_ops1_after_sales_handoff_rehearsal.py")
    files = _write_ops1_fixture_files(tmp_path)
    local_maintenance = json.loads(files["local_maintenance"].read_text(encoding="utf-8"))
    local_maintenance["api_readiness"]["safety"]["remote_control_performed"] = True
    local_maintenance["api_readiness"]["safety"]["silent_update_performed"] = True
    files["local_maintenance"].write_text(json.dumps(local_maintenance), encoding="utf-8")
    files["remote_sop"].write_text("已经完成远程控制客户电脑，静默自动更新，生产 SLA 已完成。", encoding="utf-8")

    result = module.run_h2w_ops1_after_sales_handoff_rehearsal(
        output_dir=tmp_path / "ops1",
        doc_path=tmp_path / "ops1.md",
        install1_summary=files["install1"],
        pack5_summary=files["pack5"],
        kb1_summary=files["kb1"],
        local_maintenance_summary=files["local_maintenance"],
        remote_maintenance_sop=files["remote_sop"],
        internal_ops_plan=files["internal_ops"],
        customer_quick_start_doc=files["customer_quick_start"],
    )

    assert result["status"] == "blocked"
    assert result["readiness"]["ready_for_after_sales_ops_handoff_rehearsal"] is False
    assert result["readiness"]["remote_control_ready"] is False
    assert result["readiness"]["silent_auto_update_ready"] is False
    assert result["readiness"]["production_sla_ready"] is False
    assert result["checks"]["remote_maintenance_sop"]["no_overclaim_phrases"] is False
    assert any("远程控制" in blocker or "静默" in blocker for blocker in result["blockers"])


def _write_kb2_fixture_files(tmp_path: Path) -> dict[str, Path]:
    kb1_module = _load_script("check_p3_06u_26h2w_kb1_customer_specific_knowledge_package_rehearsal.py")
    package = kb1_module._default_customer_specific_package()
    package_path = tmp_path / "kb1_package.json"
    package_path.write_text(json.dumps(package, ensure_ascii=False), encoding="utf-8")
    kb1_summary = tmp_path / "kb1_summary.json"
    kb1_summary.write_text(
        json.dumps(
            {
                "phase": "H2W-KB1",
                "status": "ready_for_customer_specific_knowledge_package_rehearsal",
                "readiness": {
                    "ready_for_customer_specific_knowledge_import_candidate": True,
                    "customer_specific_knowledge_ready": False,
                    "formal_customer_signoff_ready": False,
                },
                "package": {
                    "path": str(package_path),
                    "package_id": package["package_id"],
                    "package_name": package["package_name"],
                },
                "package_metrics": {
                    "business_object_count": 3,
                    "object_knowledge_card_count": 8,
                    "knowledge_document_count": 5,
                    "evaluation_set_count": 1,
                    "regression_case_count": 8,
                    "knowledge_types": [
                        "business_object",
                        "forbidden_commitment",
                        "handoff_rule",
                        "process_policy",
                        "standard_qa",
                    ],
                    "auto_reply_case_count": 5,
                    "handoff_case_count": 3,
                    "source_uri_count": 5,
                },
                "backend_rehearsal": {
                    "preview": {"can_apply": True, "operation_counts": {"create": 17}},
                    "import": {
                        "can_apply": True,
                        "operation_counts": {"create": 17},
                        "safety": {
                            "external_write_performed": False,
                            "provider_call_performed": False,
                            "rollback_supported": True,
                        },
                    },
                    "rollback": {
                        "rollback_status": "rolled_back",
                        "active_document_count_after_rollback": 0,
                        "active_evaluation_set_count_after_rollback": 0,
                    },
                },
                "signoff_boundary": {
                    "customer_confirmed": False,
                    "formal_contract_signoff_performed": False,
                },
                "boundaries": {
                    "real_customer_data_used": False,
                    "provider_call_performed": False,
                    "real_platform_send_performed": False,
                    "formal_customer_signoff_performed": False,
                    "customer_specific_knowledge_ready": False,
                },
            }
        ),
        encoding="utf-8",
    )
    ops1_summary = tmp_path / "ops1_summary.json"
    ops1_summary.write_text(
        json.dumps(
            {
                "phase": "H2W-OPS1",
                "status": "ready_for_after_sales_ops_handoff_rehearsal",
                "readiness": {
                    "ready_for_after_sales_ops_handoff_rehearsal": True,
                    "formal_customer_signoff_ready": False,
                    "real_platform_send_ready": False,
                },
                "boundaries": {
                    "real_platform_send_performed": False,
                    "formal_customer_signoff_performed": False,
                    "remote_control_performed": False,
                    "silent_update_performed": False,
                },
            }
        ),
        encoding="utf-8",
    )
    return {"package": package_path, "kb1_summary": kb1_summary, "ops1_summary": ops1_summary}


def test_kb2_generates_retest_report_and_blank_signoff_template(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_kb2_post_import_retest_and_signoff_template.py")
    files = _write_kb2_fixture_files(tmp_path)

    result = module.run_h2w_kb2_post_import_retest_and_signoff_template(
        output_dir=tmp_path / "kb2",
        doc_path=tmp_path / "kb2.md",
        kb1_summary=files["kb1_summary"],
        kb1_package=files["package"],
        ops1_summary=files["ops1_summary"],
    )

    assert result["status"] == "ready_for_customer_specific_knowledge_retest_template"
    assert result["readiness"]["ready_for_post_import_retest_report"] is True
    assert result["readiness"]["ready_for_customer_signoff_template"] is True
    assert result["readiness"]["formal_customer_signoff_ready"] is False
    assert result["readiness"]["customer_specific_knowledge_ready"] is False
    assert result["metrics"]["regression_case_count"] == 8
    assert result["metrics"]["signoff_template_row_count"] >= 8
    assert result["metrics"]["filled_customer_confirmation_count"] == 0
    assert result["boundaries"]["internal_rehearsal_not_customer_signoff"] is True
    assert result["boundaries"]["real_customer_data_used"] is False
    assert result["boundaries"]["real_platform_send_performed"] is False
    assert (tmp_path / "kb2/post_import_retest_report.md").exists()
    assert (tmp_path / "kb2/customer_knowledge_retest_signoff_template.csv").exists()
    assert (tmp_path / "kb2.md").exists()


def test_kb2_blocks_kb1_formal_signoff_overclaim(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_kb2_post_import_retest_and_signoff_template.py")
    files = _write_kb2_fixture_files(tmp_path)
    kb1_summary = json.loads(files["kb1_summary"].read_text(encoding="utf-8"))
    kb1_summary["readiness"]["formal_customer_signoff_ready"] = True
    kb1_summary["boundaries"]["formal_customer_signoff_performed"] = True
    files["kb1_summary"].write_text(json.dumps(kb1_summary), encoding="utf-8")

    result = module.run_h2w_kb2_post_import_retest_and_signoff_template(
        output_dir=tmp_path / "bad_kb2",
        doc_path=tmp_path / "bad_kb2.md",
        kb1_summary=files["kb1_summary"],
        kb1_package=files["package"],
        ops1_summary=files["ops1_summary"],
    )

    assert result["status"] == "blocked"
    assert result["readiness"]["ready_for_customer_signoff_template"] is False
    assert result["readiness"]["formal_customer_signoff_ready"] is False
    assert any("正式客户签收" in blocker for blocker in result["blockers"])


def _write_install3_fixture(tmp_path: Path, *, unsafe: bool = False) -> dict[str, Path]:
    installers = tmp_path / "installers"
    macos = installers / "macos"
    windows = installers / "windows"
    logs = installers / "logs"
    app_exec = macos / "WanfaCustomerService.app/Contents/MacOS/WanfaCustomerService"
    app_plist = macos / "WanfaCustomerService.app/Contents/Info.plist"
    for path in [macos, windows, logs, app_exec.parent, app_plist.parent]:
        path.mkdir(parents=True, exist_ok=True)
    (installers / "VERSION.json").write_text(
        json.dumps(
            {
                "schema_version": "p3-06u-26h2w-install3.installer_version.v1",
                "phase": "H2W-INSTALL3",
                "package_version": "0.1.0-local-pilot",
                "boundaries": {
                    "signed_dmg_exe_ready": False,
                    "desktop_installer_ready": False,
                    "native_installer_ready": False,
                    "real_platform_send_ready": False,
                    "silent_update_ready": False,
                    "remote_control_ready": False,
                },
            }
        ),
        encoding="utf-8",
    )
    (logs / ".gitkeep").write_text("", encoding="utf-8")
    (logs / "README.md").write_text("健康检查摘要\n版本号\n禁止保存\n数据库密码\n模型 key\n", encoding="utf-8")
    app_plist.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>com.test.app</string>
<key>CFBundleExecutable</key><string>WanfaCustomerService</string>
<key>CFBundleShortVersionString</key><string>0.1.0</string>
<key>CFBundlePackageType</key><string>APPL</string>
</dict></plist>
""",
        encoding="utf-8",
    )
    app_exec.write_text(
        '#!/usr/bin/env bash\nset -euo pipefail\nexec "$(dirname "$0")/../../../WanfaCustomerService.command" "$@"\n',
        encoding="utf-8",
    )
    (macos / "health-check.sh").write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                'require_env_value "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"',
                'require_env_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"',
                'require_env_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"',
                "docker info # Docker Desktop",
                "curl --fail http://127.0.0.1:18080/health",
            ]
        ),
        encoding="utf-8",
    )
    (macos / "prepare-upgrade-backup.sh").write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                'require_env_value "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"',
                'require_env_value "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"',
                'require_env_value "TRUSTED_INBOUND_WORKER_ENABLED" "false"',
                'echo "manifest.json"',
                '# "database_backup_exported_by_this_script": false',
                'echo "账号与本地维护 生成备份"',
            ]
        ),
        encoding="utf-8",
    )
    (windows / "HealthCheck-WanfaCustomerService.ps1").write_text(
        "\n".join(
            [
                'Require-EnvValue "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"',
                'Require-EnvValue "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"',
                'Require-EnvValue "TRUSTED_INBOUND_WORKER_ENABLED" "false"',
                "docker info # Docker Desktop",
                "Invoke-WebRequest http://127.0.0.1:18080/health",
            ]
        ),
        encoding="utf-8",
    )
    (windows / "Prepare-UpgradeBackup.ps1").write_text(
        "\n".join(
            [
                'Require-EnvValue "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" "false"',
                'Require-EnvValue "OUTBOX_EXTERNAL_WRITE_ENABLED" "false"',
                'Require-EnvValue "TRUSTED_INBOUND_WORKER_ENABLED" "false"',
                'echo "manifest.json"',
                "ConvertTo-Json",
                "database_backup_exported_by_this_script = $false",
                'echo "账号与本地维护 生成本地备份"',
            ]
        ),
        encoding="utf-8",
    )
    (macos / "uninstall-notes.md").write_text("清理说明\n", encoding="utf-8")
    (windows / "uninstall-notes.md").write_text("清理说明\n", encoding="utf-8")
    if unsafe:
        (macos / "health-check.sh").write_text(
            (macos / "health-check.sh").read_text(encoding="utf-8") + "\nOUTBOX_EXTERNAL_WRITE_ENABLED=true\n",
            encoding="utf-8",
        )
        (logs / "README.md").write_text(
            (logs / "README.md").read_text(encoding="utf-8") + "\n签名安装包已完成\n",
            encoding="utf-8",
        )
    install2 = tmp_path / "install2.json"
    install2.write_text(
        json.dumps(
            {
                "status": "native_wrapper_candidate_ready",
                "readiness": {"signed_dmg_exe_ready": False},
            }
        ),
        encoding="utf-8",
    )
    pilot5 = tmp_path / "pilot5.json"
    pilot5.write_text(
        json.dumps(
            {
                "status": "installer_next_fork_decision_ready",
                "decision": {"enter_native_installer_track": True},
            }
        ),
        encoding="utf-8",
    )
    return {
        "installers": installers,
        "macos": macos,
        "windows": windows,
        "logs": logs,
        "version": installers / "VERSION.json",
        "install2": install2,
        "pilot5": pilot5,
    }


def test_install3_accepts_native_app_packaging_candidate_without_signed_claim(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_install3_native_app_packaging_gate.py")
    files = _write_install3_fixture(tmp_path)
    module.INSTALLERS_DIR = files["installers"]
    module.MACOS_DIR = files["macos"]
    module.WINDOWS_DIR = files["windows"]
    module.VERSION_FILE = files["version"]
    module.LOGS_DIR = files["logs"]

    result = module.run_h2w_install3_native_app_packaging_gate(
        output_dir=tmp_path / "install3",
        doc_path=tmp_path / "install3.md",
        install2_summary=files["install2"],
        pilot5_summary=files["pilot5"],
        runner=_runner,
    )

    assert result["status"] == "native_app_packaging_candidate_ready"
    assert result["readiness"]["macos_app_wrapper_candidate_ready"] is True
    assert result["readiness"]["windows_launcher_candidate_ready"] is True
    assert result["readiness"]["health_check_candidate_ready"] is True
    assert result["readiness"]["upgrade_backup_preflight_ready"] is True
    assert result["readiness"]["signed_dmg_exe_ready"] is False
    assert result["readiness"]["native_installer_ready"] is False
    assert result["boundaries"]["real_platform_send_performed"] is False
    assert result["boundaries"]["secret_written_by_installer"] is False
    assert (tmp_path / "install3.md").exists()


def test_install3_blocks_unsafe_switches_or_signed_installer_overclaim(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_install3_native_app_packaging_gate.py")
    files = _write_install3_fixture(tmp_path, unsafe=True)
    module.INSTALLERS_DIR = files["installers"]
    module.MACOS_DIR = files["macos"]
    module.WINDOWS_DIR = files["windows"]
    module.VERSION_FILE = files["version"]
    module.LOGS_DIR = files["logs"]

    result = module.run_h2w_install3_native_app_packaging_gate(
        output_dir=tmp_path / "bad_install3",
        doc_path=tmp_path / "bad_install3.md",
        install2_summary=files["install2"],
        pilot5_summary=files["pilot5"],
        runner=_runner,
    )

    assert result["status"] == "blocked"
    assert result["readiness"]["signed_dmg_exe_ready"] is False
    assert any("不安全开关" in blocker or "越界承诺" in blocker for blocker in result["blockers"])


def _write_fe5_fixture(tmp_path: Path, *, pilot_bound: bool = True, pilot_browser_covered: bool = False) -> dict[str, Path]:
    def write_summary(name: str, payload: dict) -> Path:
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    fe4 = write_summary(
        "fe4",
        {
            "status": "ready_for_customer_visible_ui_candidate",
            "metrics": {
                "visible_engineering_hit_count": 0,
                "overclaim_hit_count": 0,
                "deep_audit_issue_count": 0,
            },
            "boundaries": {"real_platform_send_performed": False, "formal_customer_signoff_performed": False},
        },
    )
    pages = [{"hash": "#overview"}, {"hash": "#live"}, {"hash": "#knowledge"}, {"hash": "#settings"}]
    if pilot_browser_covered:
        pages.append({"hash": "#pilot"})
    click = write_summary(
        "click",
        {
            "status": "passed_customer_visible_click_qa",
            "ok": True,
            "browser": {"pages": pages, "runtimeErrors": []},
            "real_platform_send_performed": False,
            "formal_customer_signoff_performed": False,
        },
    )
    pilot0 = write_summary(
        "pilot0",
        {
            "status": "pilot_candidate_ready_with_internal_data",
            "readiness": {"real_platform_send_ready": False},
        },
    )
    pilot4 = write_summary("pilot4", {"status": "passed_customer_local_trial_rehearsal"})
    install3 = write_summary(
        "install3",
        {
            "status": "native_app_packaging_candidate_ready",
            "readiness": {"signed_dmg_exe_ready": False},
        },
    )
    navigation = tmp_path / "navigation.ts"
    navigation.write_text(
        'export const navigationGroups = [{ label: "管理运维", items: [{ label: "试点准备", href: "#pilot" }] }];\n',
        encoding="utf-8",
    )
    app = tmp_path / "App.tsx"
    app.write_text('switch(activeSection) { case "pilot": return <PilotPreparationPanel />; }\n', encoding="utf-8")
    api = tmp_path / "client.ts"
    api.write_text(
        "export async function getPilotReadiness() { return requestJson('/api/tenants/1/pilot-readiness'); }\n"
        if pilot_bound
        else "export async function getSomethingElse() { return null; }\n",
        encoding="utf-8",
    )
    matrix = tmp_path / "matrix.md"
    matrix.write_text("# 前端功能真实性矩阵\n", encoding="utf-8")
    return {
        "fe4": fe4,
        "click": click,
        "pilot0": pilot0,
        "pilot4": pilot4,
        "install3": install3,
        "navigation": navigation,
        "app": app,
        "api": api,
        "matrix": matrix,
    }


def test_fe5_marks_latest_pilot_page_as_recheck_required_when_not_in_browser_qa(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_fe5_frontend_backend_alignment_and_ux_status.py")
    files = _write_fe5_fixture(tmp_path, pilot_bound=True, pilot_browser_covered=False)

    result = module.run_h2w_fe5_frontend_backend_alignment_and_ux_status(
        output_dir=tmp_path / "fe5",
        doc_path=tmp_path / "fe5.md",
        next_steps_doc_path=tmp_path / "next.md",
        fe4_summary=files["fe4"],
        fe4_click_qa=files["click"],
        pilot0_summary=files["pilot0"],
        pilot4_summary=files["pilot4"],
        install3_summary=files["install3"],
        matrix_path=files["matrix"],
        navigation_path=files["navigation"],
        app_path=files["app"],
        api_client_path=files["api"],
    )

    assert result["status"] == "frontend_aligned_with_latest_recheck_required"
    assert result["readiness"]["core_customer_visible_frontend_ready"] is True
    assert result["readiness"]["latest_pilot_page_route_ready"] is True
    assert result["readiness"]["latest_pilot_page_browser_verified"] is False
    assert result["readiness"]["frontend_ready_for_full_latest_signoff"] is False
    assert any("#pilot" in warning for warning in result["warnings"])
    assert (tmp_path / "fe5.md").exists()
    assert (tmp_path / "next.md").exists()


def test_fe5_blocks_if_pilot_page_is_not_bound_to_api_client(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_fe5_frontend_backend_alignment_and_ux_status.py")
    files = _write_fe5_fixture(tmp_path, pilot_bound=False, pilot_browser_covered=False)

    result = module.run_h2w_fe5_frontend_backend_alignment_and_ux_status(
        output_dir=tmp_path / "bad_fe5",
        doc_path=tmp_path / "bad_fe5.md",
        next_steps_doc_path=tmp_path / "bad_next.md",
        fe4_summary=files["fe4"],
        fe4_click_qa=files["click"],
        pilot0_summary=files["pilot0"],
        pilot4_summary=files["pilot4"],
        install3_summary=files["install3"],
        matrix_path=files["matrix"],
        navigation_path=files["navigation"],
        app_path=files["app"],
        api_client_path=files["api"],
    )

    assert result["status"] == "blocked"
    assert result["readiness"]["latest_pilot_page_route_ready"] is False
    assert any("试点准备页" in blocker for blocker in result["blockers"])


def _write_pack8b_fixture(tmp_path: Path, *, pack8_customer_data: bool) -> dict[str, Path]:
    pack8 = tmp_path / "pack8.json"
    pack8.write_text(
        json.dumps(
            {
                "status": "co_creation_trial_package_v1_1_candidate_with_customer_data"
                if pack8_customer_data
                else "co_creation_trial_package_v1_1_candidate_with_internal_data",
                "customer_data_used": pack8_customer_data,
                "internal_sample_used": not pack8_customer_data,
                "readiness": {
                    "formal_customer_signoff_ready": False,
                    "real_platform_send_ready": False,
                    "signed_dmg_exe_ready": False,
                    "production_sla_ready": False,
                },
            }
        ),
        encoding="utf-8",
    )
    data2 = tmp_path / "data2.json"
    data2.write_text(
        json.dumps(
            {
                "status": "waiting_for_real_customer_materials",
                "customer_data_used": False,
                "internal_sample_used": False,
                "readiness": {
                    "waiting_for_real_customer_materials": True,
                    "customer_real_materials_ready": False,
                },
            }
        ),
        encoding="utf-8",
    )
    app = tmp_path / "App.tsx"
    app.write_text("const real_customer_material_status = '等待真实脱敏资料';\n", encoding="utf-8")
    client = tmp_path / "client.ts"
    client.write_text(
        "type Pilot = { real_customer_material_status?: string; real_customer_material_evidence?: unknown[] };\n",
        encoding="utf-8",
    )
    service = tmp_path / "pilot.py"
    service.write_text(
        "recommended_next_steps = ['将真实客户脱敏资料放入 DATA2 接收目录']\n"
        "real_customer_material_status = 'waiting_for_real_customer_materials'\n",
        encoding="utf-8",
    )
    readme = tmp_path / "README.md"
    readme.write_text("status=waiting_for_real_customer_materials；不伪造客户资料。\n", encoding="utf-8")
    master = tmp_path / "MASTER.md"
    master.write_text("status=waiting_for_real_customer_materials；不伪造客户资料。\n", encoding="utf-8")
    return {
        "pack8": pack8,
        "data2": data2,
        "app": app,
        "client": client,
        "service": service,
        "readme": readme,
        "master": master,
    }


def test_pack8b_locks_internal_pack_when_real_materials_are_waiting(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_pack8b_real_material_boundary_lock.py")
    files = _write_pack8b_fixture(tmp_path, pack8_customer_data=False)

    result = module.run_h2w_pack8b_real_material_boundary_lock(
        output_dir=tmp_path / "pack8b",
        doc_path=tmp_path / "pack8b.md",
        pack8_summary=files["pack8"],
        data2_summary=files["data2"],
        frontend_app=files["app"],
        frontend_client=files["client"],
        pilot_service=files["service"],
        readme_path=files["readme"],
        master_plan=files["master"],
    )

    assert result["status"] == "pack8_boundary_locked_waiting_real_materials"
    assert result["readiness"]["pack8_boundary_locked"] is True
    assert result["readiness"]["waiting_real_customer_materials"] is True
    assert result["customer_data_used"] is False
    assert result["internal_sample_used"] is True
    assert (tmp_path / "pack8b.md").exists()


def test_pack8b_blocks_customer_data_pack_when_real_materials_are_waiting(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_pack8b_real_material_boundary_lock.py")
    files = _write_pack8b_fixture(tmp_path, pack8_customer_data=True)

    result = module.run_h2w_pack8b_real_material_boundary_lock(
        output_dir=tmp_path / "bad_pack8b",
        doc_path=tmp_path / "bad_pack8b.md",
        pack8_summary=files["pack8"],
        data2_summary=files["data2"],
        frontend_app=files["app"],
        frontend_client=files["client"],
        pilot_service=files["service"],
        readme_path=files["readme"],
        master_plan=files["master"],
    )

    assert result["status"] == "blocked"
    assert result["readiness"]["pack8_boundary_locked"] is False
    assert any("PACK8 必须保持内部样板候选" in blocker for blocker in result["blockers"])


def _write_pack9_fixture(
    tmp_path: Path,
    *,
    pack8b_status: str = "pack8_boundary_locked_waiting_real_materials",
    data2_status: str = "waiting_for_real_customer_materials",
    data2_customer_data_used: bool = False,
    data2_ready_flag: bool = False,
) -> dict[str, Path]:
    pack8b = tmp_path / "pack8b.json"
    pack8b.write_text(
        json.dumps(
            {
                "status": pack8b_status,
                "customer_data_used": False,
                "internal_sample_used": True,
                "readiness": {
                    "pack8_boundary_locked": pack8b_status == "pack8_boundary_locked_waiting_real_materials",
                    "formal_customer_signoff_ready": False,
                    "real_platform_send_ready": False,
                    "signed_dmg_exe_ready": False,
                    "production_sla_ready": False,
                },
            }
        ),
        encoding="utf-8",
    )
    data2 = tmp_path / "data2.json"
    data2.write_text(
        json.dumps(
            {
                "status": data2_status,
                "customer_data_used": data2_customer_data_used,
                "internal_sample_used": False,
                "readiness": {
                    "waiting_for_real_customer_materials": data2_status == "waiting_for_real_customer_materials",
                    "customer_real_materials_ready": data2_ready_flag,
                    "real_platform_send_ready": False,
                    "formal_customer_signoff_ready": False,
                },
            }
        ),
        encoding="utf-8",
    )
    scripts: dict[str, Path] = {}
    for name in ["data2", "pack8b", "kb5_internal_line", "trial2_internal_line", "fe8", "pack8"]:
        script = tmp_path / f"{name}.py"
        script.write_text("# fixture\n", encoding="utf-8")
        scripts[f"script_{name}"] = script
    return {"pack8b_summary": pack8b, "data2_summary": data2, **scripts}


def test_pack9_plan_ready_while_waiting_for_real_customer_materials(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_pack9_real_customer_rerun_plan.py")
    files = _write_pack9_fixture(tmp_path)
    scripts = {
        name: files[f"script_{name}"]
        for name in ["data2", "pack8b", "kb5_internal_line", "trial2_internal_line", "fe8", "pack8"]
    }

    result = module.run_h2w_pack9_real_customer_rerun_plan(
        output_dir=tmp_path / "pack9",
        doc_path=tmp_path / "pack9.md",
        pack8b_summary=files["pack8b_summary"],
        data2_summary=files["data2_summary"],
        current_gate_scripts=scripts,
    )

    assert result["status"] == "pack9_plan_ready_waiting_real_customer_materials"
    assert result["readiness"]["ready_for_pack9_planning"] is True
    assert result["readiness"]["waiting_for_real_customer_materials"] is True
    assert result["readiness"]["ready_to_run_customer_data_chain"] is False
    assert result["readiness"]["requires_kb6_trial3_fe9_pack9_implementation"] is True
    assert result["customer_data_used"] is False
    assert result["internal_sample_used"] is True
    assert (tmp_path / "pack9.md").exists()


def test_pack9_blocks_if_data2_waiting_claims_customer_data_ready(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_pack9_real_customer_rerun_plan.py")
    files = _write_pack9_fixture(
        tmp_path,
        data2_status="waiting_for_real_customer_materials",
        data2_customer_data_used=True,
        data2_ready_flag=True,
    )
    scripts = {
        name: files[f"script_{name}"]
        for name in ["data2", "pack8b", "kb5_internal_line", "trial2_internal_line", "fe8", "pack8"]
    }

    result = module.run_h2w_pack9_real_customer_rerun_plan(
        output_dir=tmp_path / "bad_pack9",
        doc_path=tmp_path / "bad_pack9.md",
        pack8b_summary=files["pack8b_summary"],
        data2_summary=files["data2_summary"],
        current_gate_scripts=scripts,
    )

    assert result["status"] == "blocked"
    assert result["readiness"]["ready_for_pack9_planning"] is False
    assert any("DATA2 等待状态" in blocker for blocker in result["blockers"])


def test_pack9_real_materials_ready_requires_pack8b_refresh_before_customer_chain(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_pack9_real_customer_rerun_plan.py")
    files = _write_pack9_fixture(
        tmp_path,
        pack8b_status="pack8_boundary_locked_waiting_real_materials",
        data2_status="customer_real_materials_ready",
        data2_customer_data_used=True,
        data2_ready_flag=True,
    )
    scripts = {
        name: files[f"script_{name}"]
        for name in ["data2", "pack8b", "kb5_internal_line", "trial2_internal_line", "fe8", "pack8"]
    }

    result = module.run_h2w_pack9_real_customer_rerun_plan(
        output_dir=tmp_path / "refresh_pack9",
        doc_path=tmp_path / "refresh_pack9.md",
        pack8b_summary=files["pack8b_summary"],
        data2_summary=files["data2_summary"],
        current_gate_scripts=scripts,
    )

    assert result["status"] == "pack9_plan_ready_real_materials_require_pack8b_refresh"
    assert result["readiness"]["ready_for_pack9_planning"] is True
    assert result["readiness"]["requires_pack8b_refresh"] is True
    assert result["readiness"]["ready_to_run_customer_data_chain"] is False
    assert result["customer_data_used"] is True
    assert result["internal_sample_used"] is False


def _write_pack12_summary(
    tmp_path: Path,
    name: str,
    *,
    status: str,
    customer_data_used: bool = False,
    internal_sample_used: bool = False,
) -> Path:
    path = tmp_path / f"{name}.json"
    path.write_text(
        json.dumps(
            {
                "status": status,
                "customer_data_used": customer_data_used,
                "internal_sample_used": internal_sample_used,
                "readiness": {
                    "real_platform_send_ready": False,
                    "formal_customer_signoff_ready": False,
                    "signed_dmg_exe_ready": False,
                    "production_sla_ready": False,
                },
                "boundaries": {
                    "real_platform_send_ready": False,
                    "formal_customer_signoff_ready": False,
                    "signed_dmg_exe_ready": False,
                    "production_sla_ready": False,
                    "rpa_formal_delivery_enabled": False,
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def _pack12_stage_specs(tmp_path: Path, statuses: dict[str, str]) -> dict[str, dict]:
    specs: dict[str, dict] = {}
    ready_statuses = {
        "data2r": {"customer_real_materials_ready"},
        "kb6": {"customer_knowledge_retest_ready_with_customer_data"},
        "trial3": {"shadow_trial_ready_with_customer_data"},
        "fe9": {"passed_customer_data_browser_qa"},
        "pack10": {"customer_data_local_trial_package_v2_candidate"},
        "pack11": {"customer_data_local_trial_package_v3_candidate"},
    }
    waiting_statuses = {
        "data2r": {"waiting_for_real_customer_materials"},
        "kb6": {"waiting_for_real_customer_materials"},
        "trial3": {"waiting_for_real_customer_materials"},
        "fe9": {"waiting_for_real_customer_materials"},
        "pack10": {"blocked_waiting_real_customer_materials"},
        "pack11": {"blocked_waiting_real_customer_materials"},
    }
    for code in ["data2r", "kb6", "trial3", "fe9", "pack10", "pack11"]:
        status = statuses.get(code, "missing")
        specs[code] = {
            "command": ["fixture", code],
            "summary": _write_pack12_summary(
                tmp_path,
                code,
                status=status,
                customer_data_used=status in ready_statuses[code],
                internal_sample_used=status in waiting_statuses[code],
            ),
            "ready": ready_statuses[code],
            "waiting": waiting_statuses[code],
            "title": code,
        }
    return specs


def test_pack12_waits_cleanly_when_real_customer_materials_are_missing(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_pack12_customer_data_rerun_orchestrator.py")
    specs = _pack12_stage_specs(
        tmp_path,
        {"data2r": "waiting_for_real_customer_materials"},
    )

    result = module.run_h2w_pack12_customer_data_rerun_orchestrator(
        output_dir=tmp_path / "pack12",
        doc_path=tmp_path / "pack12.md",
        stage_specs=specs,
        execute_commands=False,
    )

    assert result["status"] == "waiting_for_real_customer_materials_for_customer_data_rerun"
    assert result["blockers"] == []
    assert result["readiness"]["waiting_for_real_customer_materials"] is True
    assert result["readiness"]["downstream_skipped_until_real_materials_ready"] is True
    assert result["readiness"]["customer_data_rerun_complete"] is False
    assert result["customer_data_used"] is False
    assert result["internal_sample_used"] is True
    assert (tmp_path / "pack12.md").exists()


def test_pack12_requires_downstream_chain_when_real_customer_materials_are_ready(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_pack12_customer_data_rerun_orchestrator.py")
    specs = _pack12_stage_specs(
        tmp_path,
        {
            "data2r": "customer_real_materials_ready",
            "kb6": "waiting_for_real_customer_materials",
            "trial3": "waiting_for_real_customer_materials",
            "fe9": "waiting_for_real_customer_materials",
            "pack10": "blocked_waiting_real_customer_materials",
            "pack11": "blocked_waiting_real_customer_materials",
        },
    )

    result = module.run_h2w_pack12_customer_data_rerun_orchestrator(
        output_dir=tmp_path / "blocked_pack12",
        doc_path=tmp_path / "blocked_pack12.md",
        stage_specs=specs,
        execute_commands=False,
    )

    assert result["status"] == "blocked"
    assert result["readiness"]["waiting_for_real_customer_materials"] is False
    assert result["readiness"]["customer_data_rerun_complete"] is False
    assert any("kb6 状态不满足" in blocker for blocker in result["blockers"])
    assert any("pack11 状态不满足" in blocker for blocker in result["blockers"])


def _write_data2r7_summary(path: Path, status: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "status": status,
                "blockers": [],
                "readiness": {
                    "real_platform_send_ready": False,
                    "formal_customer_signoff_ready": False,
                    "signed_dmg_exe_ready": False,
                    "production_sla_ready": False,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def _prepare_data2r7_intake_dir(tmp_path: Path, *, with_received_files: bool) -> Path:
    intake = tmp_path / "intake"
    intake.mkdir(parents=True)
    for filename in [
        "customer_materials_real_template.csv",
        "customer_trial_questions_real_template.csv",
        "customer_material_manifest_template.json",
        "README.md",
    ]:
        (intake / filename).write_text("template\n", encoding="utf-8")
    if with_received_files:
        (intake / "customer_materials_received.csv").write_text("record_type,item_id\nstandard_qa,QA-1\n", encoding="utf-8")
        (intake / "customer_trial_questions_received.csv").write_text("question_id,question\nQ-1,问法\n", encoding="utf-8")
        (intake / "customer_material_manifest_received.json").write_text('{"customer_data_used":true}', encoding="utf-8")
    return intake


def test_data2r7_waits_for_received_files_without_claiming_customer_data(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_data2r7_received_file_drop_gate.py")
    intake = _prepare_data2r7_intake_dir(tmp_path, with_received_files=False)

    result = module.run_h2w_data2r7_received_file_drop_gate(
        output_dir=tmp_path / "data2r7",
        doc_path=tmp_path / "data2r7.md",
        intake_dir=intake,
        data2_summary=_write_data2r7_summary(tmp_path / "data2.json", "waiting_for_real_customer_materials"),
        handoff_summary=_write_data2r7_summary(tmp_path / "handoff.json", "material_handoff_bundle_ready"),
        pack12_summary=_write_data2r7_summary(
            tmp_path / "pack12.json",
            "waiting_for_real_customer_materials_for_customer_data_rerun",
        ),
    )

    assert result["status"] == "received_file_drop_ready_waiting_customer_files"
    assert result["blockers"] == []
    assert result["readiness"]["waiting_for_customer_files"] is True
    assert result["readiness"]["ready_for_pack12_rerun"] is False
    assert result["customer_data_used"] is False
    assert result["internal_sample_used"] is True
    assert len(result["missing_received_files"]) == 3


def test_data2r7_detects_received_files_that_need_data2_validation_rerun(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_data2r7_received_file_drop_gate.py")
    intake = _prepare_data2r7_intake_dir(tmp_path, with_received_files=True)

    result = module.run_h2w_data2r7_received_file_drop_gate(
        output_dir=tmp_path / "data2r7",
        doc_path=tmp_path / "data2r7.md",
        intake_dir=intake,
        data2_summary=_write_data2r7_summary(tmp_path / "data2.json", "waiting_for_real_customer_materials"),
        handoff_summary=_write_data2r7_summary(tmp_path / "handoff.json", "material_handoff_bundle_ready"),
        pack12_summary=_write_data2r7_summary(
            tmp_path / "pack12.json",
            "waiting_for_real_customer_materials_for_customer_data_rerun",
        ),
    )

    assert result["status"] == "received_files_present_pending_data2r_validation"
    assert result["readiness"]["received_files_present"] is True
    assert result["readiness"]["needs_data2_validation_rerun"] is True
    assert result["readiness"]["ready_for_pack12_rerun"] is False
    assert result["warnings"]


def test_data2r7_allows_pack12_rerun_only_after_data2_ready(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_data2r7_received_file_drop_gate.py")
    intake = _prepare_data2r7_intake_dir(tmp_path, with_received_files=True)

    result = module.run_h2w_data2r7_received_file_drop_gate(
        output_dir=tmp_path / "data2r7",
        doc_path=tmp_path / "data2r7.md",
        intake_dir=intake,
        data2_summary=_write_data2r7_summary(tmp_path / "data2.json", "customer_real_materials_ready"),
        handoff_summary=_write_data2r7_summary(tmp_path / "handoff.json", "material_handoff_bundle_ready"),
        pack12_summary=_write_data2r7_summary(
            tmp_path / "pack12.json",
            "waiting_for_real_customer_materials_for_customer_data_rerun",
        ),
    )

    assert result["status"] == "received_files_validated_ready_for_pack12_rerun"
    assert result["readiness"]["customer_real_materials_ready"] is True
    assert result["readiness"]["ready_for_pack12_rerun"] is True
    assert result["customer_data_used"] is True
    assert result["readiness"]["real_platform_send_ready"] is False


def _write_data2r8_file(path: Path, snippets: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(snippets), encoding="utf-8")
    return path


def _run_data2r8_gate(tmp_path: Path, *, frontend_app_snippets: list[str] | None = None) -> dict:
    module = _load_script("check_p3_06u_26h2w_data2r8_material_drop_gate_api_ui.py")
    frontend_snippets = frontend_app_snippets or [
        "回传文件落位",
        "received_file_drop_ready_waiting_customer_files",
        "received_files_present_pending_data2r_validation",
        "received_internal_sample_files_validated_ready_for_pack12_rerun",
        "文件已落位，待校验",
    ]

    return module.run_h2w_data2r8_material_drop_gate_api_ui(
        output_dir=tmp_path / "data2r8",
        doc_path=tmp_path / "data2r8.md",
        backend_schema=_write_data2r8_file(
            tmp_path / "pilot.py",
            ["material_drop_gate_status", "material_drop_gate_evidence"],
        ),
        backend_service=_write_data2r8_file(
            tmp_path / "service.py",
            [
                "p3_06u_26h2w_data2r7_received_file_drop_gate/summary.json",
                '"material_drop_gate"',
                'material_drop_gate_status=five_gap_evidence["material_drop_gate"][0]',
                'material_drop_gate_evidence=five_gap_evidence["material_drop_gate"][1]',
            ],
        ),
        backend_tests=_write_data2r8_file(
            tmp_path / "test_pilot_api.py",
            ["material_drop_gate_status", "material_drop_gate_evidence"],
        ),
        frontend_client=_write_data2r8_file(
            tmp_path / "client.ts",
            ["material_drop_gate_status", "material_drop_gate_evidence"],
        ),
        frontend_app=_write_data2r8_file(tmp_path / "App.tsx", frontend_snippets),
        data2r7_summary=_write_data2r7_summary(
            tmp_path / "data2r7.json",
            "received_file_drop_ready_waiting_customer_files",
        ),
    )


def test_data2r8_exposes_material_drop_gate_in_api_and_ui(tmp_path: Path) -> None:
    result = _run_data2r8_gate(tmp_path)

    assert result["status"] == "material_drop_gate_api_ui_ready"
    assert result["readiness"]["pilot_readiness_exposes_material_drop_gate"] is True
    assert result["readiness"]["frontend_displays_material_drop_gate"] is True
    assert result["readiness"]["received_file_drop_gate_ready"] is True
    assert result["readiness"]["real_customer_materials_ready"] is False
    assert result["readiness"]["real_platform_send_ready"] is False


def test_data2r8_blocks_when_frontend_hides_material_drop_gate(tmp_path: Path) -> None:
    result = _run_data2r8_gate(tmp_path, frontend_app_snippets=["received_file_drop_ready_waiting_customer_files"])

    assert result["status"] == "blocked"
    assert result["readiness"]["frontend_displays_material_drop_gate"] is False
    assert any("frontend_app 缺少必要片段" in blocker for blocker in result["blockers"])


def test_install7_accepts_customer_mode_prepack_gate_without_signed_installer_claim(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_install7_customer_mode_prepack_gate.py")
    install6 = tmp_path / "install6.json"
    install6.write_text('{"status":"trial_installer_experience_candidate_ready"}', encoding="utf-8")

    result = module.run_h2w_install7_customer_mode_prepack_gate(
        output_dir=tmp_path / "install7",
        doc_path=tmp_path / "install7.md",
        install6_summary=install6,
    )

    assert result["status"] == "customer_mode_prepack_gate_ready"
    assert result["readiness"]["customer_mode_prepack_ready"] is True
    assert result["readiness"]["dev_bootstrap_enabled"] is False
    assert result["readiness"]["default_admin_password_created"] is False
    assert result["readiness"]["real_platform_send_ready"] is False
    assert result["readiness"]["trusted_inbound_worker_default_enabled"] is False
    assert result["readiness"]["signed_dmg_exe_ready"] is False
    assert result["readiness"]["desktop_installer_ready"] is False
    assert result["readiness"]["native_installer_ready"] is False
    assert (tmp_path / "install7.md").exists()


def test_install7_blocks_unsafe_customer_env_template(tmp_path: Path) -> None:
    module = _load_script("check_p3_06u_26h2w_install7_customer_mode_prepack_gate.py")
    bad_env = tmp_path / "customer.env.example"
    bad_env.write_text(
        "\n".join(
            [
                "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED=true",
                "OUTBOX_EXTERNAL_WRITE_ENABLED=false",
                "TRUSTED_INBOUND_WORKER_ENABLED=false",
                "KNOWLEDGE_VECTOR_STORE=postgres_pgvector_store_v1",
                "ADMIN_BOOTSTRAP_EMAIL=",
                "ADMIN_BOOTSTRAP_PASSWORD=admin123",
                "BAILIAN_API_KEY=",
                "DEEPSEEK_API_KEY=",
            ]
        ),
        encoding="utf-8",
    )

    blockers = module._check_env_template(bad_env)

    assert any("STANDARD_OPS_DEV_BOOTSTRAP_ENABLED" in blocker for blocker in blockers)
    assert any("ADMIN_BOOTSTRAP_PASSWORD" in blocker for blocker in blockers)
    assert any("开发入口开启" in blocker for blocker in blockers)
    assert any("预置管理员密码" in blocker for blocker in blockers)
