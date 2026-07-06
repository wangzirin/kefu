from __future__ import annotations

import base64
import io
import json
import zipfile

from app.models import (
    AuditEvent,
    BusinessObject,
    Conversation,
    CustomerMaterialBatch,
    KnowledgeDocument,
    KnowledgeEvaluationCase,
    KnowledgeEvaluationRun,
    KnowledgeEvaluationSet,
    Message,
    PilotReadinessFact,
)


def _create_tenant(client, slug: str) -> dict:
    res = client.post("/api/tenants", json={"name": f"{slug} 客户", "slug": slug})
    assert res.status_code == 201
    return res.json()


def _bootstrap_user(
    client,
    tenant: dict,
    *,
    role_code: str = "owner",
    email: str = "owner@example.com",
) -> str:
    role_res = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        json={"code": role_code, "name": role_code},
    )
    assert role_res.status_code == 201
    role = role_res.json()

    user_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        json={"name": f"{role_code} 用户", "email": email, "password": "ChangeMe123!"},
    )
    assert user_res.status_code == 201
    assign_res = client.post(f"/api/users/{user_res.json()['id']}/roles", json={"role_id": role["id"]})
    assert assign_res.status_code == 201

    login_res = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": email, "password": "ChangeMe123!"},
    )
    assert login_res.status_code == 200
    return login_res.json()["access_token"]


def _material_csv() -> str:
    rows = [
        "record_type,item_id,business_object,title,question,standard_answer,source_uri,expected_behavior,forbidden_terms,handoff_condition,desensitization_note",
        "business_object,OBJ-001,标准套餐,套餐说明,标准套餐包含什么,标准套餐包含基础接待和知识维护,customer-doc://fixture/product,引用来源后回答,最低价;百分百保证,资料不足转人工,已脱敏",
        "standard_qa,QA-001,标准套餐,价格咨询,多少钱,以合同确认价格为准,customer-doc://fixture/price,引用来源后回答,最低价,价格争议转人工,已脱敏",
        "process_policy,POL-001,售后流程,售后政策,售后怎么处理,先登记问题类型再按政策处理,customer-doc://fixture/policy,引用来源后回答,无条件退款,售后纠纷转人工,已脱敏",
        "forbidden_commitment,BAN-001,服务边界,禁用承诺,能保证效果吗,不能承诺绝对效果,customer-doc://fixture/forbidden,触发边界转人工,百分百保证,绝对化诉求转人工,已脱敏",
        "handoff_rule,HAND-001,人工处理,转人工规则,我要投诉,投诉付款异常退款争议转人工,customer-doc://fixture/handoff,转人工,无,投诉转人工,已脱敏",
    ]
    return "\n".join(rows)


def _questions_csv(count: int = 50, *, first_action: str = "answer_with_reference", first_question: str = "客户脱敏问题 001") -> str:
    rows = [
        "question_id,question,expected_answer,expected_action,source_uri,business_object,desensitization_note",
    ]
    actions = ["answer_with_reference", "handoff", "reject_forbidden_commitment", "ask_clarifying_question"]
    for index in range(1, count + 1):
        action = first_action if index == 1 else actions[index % len(actions)]
        question = first_question if index == 1 else f"客户脱敏问题 {index:03d}"
        rows.append(
            f"Q-{index:03d},{question},按已发布资料回答或转人工,{action},customer-doc://fixture/product,标准套餐,已脱敏"
        )
    return "\n".join(rows)


def _manifest_json(**overrides) -> str:
    manifest = {
        "customer_alias": "资料预检客户",
        "provided_by_role": "业务负责人",
        "provided_at": "2026-07-05",
        "desensitization_owner_role": "运营负责人",
        "desensitization_statement": "已移除手机号、邮箱、订单号、平台 payload、密钥和 token。",
        "customer_data_used": True,
        "real_platform_send_enabled": False,
        "formal_customer_signoff_ready": False,
    }
    manifest.update(overrides)
    return json.dumps(manifest, ensure_ascii=False)


def _audit_payload(audit: AuditEvent) -> dict:
    return json.loads(audit.payload) if isinstance(audit.payload, str) else audit.payload


def _seed_trial_ready_records(db_session, tenant_id: int) -> None:
    db_session.add(
        BusinessObject(
            tenant_id=tenant_id,
            type="product",
            title="标准套餐",
            summary="用于试点事实账本测试的业务对象",
        )
    )
    db_session.add(
        KnowledgeDocument(
            tenant_id=tenant_id,
            title="标准套餐知识文档",
            source_uri="customer-doc://fixture/product",
            raw_text="标准套餐包含基础接待、知识维护和转人工边界。",
            content_hash="fixture-doc-hash",
            status="published",
            chunk_count=1,
        )
    )
    evaluation_set = KnowledgeEvaluationSet(
        tenant_id=tenant_id,
        name=f"客户资料复测 {tenant_id}",
        status="active",
        evaluation_mode="final_answer_quality",
    )
    db_session.add(evaluation_set)
    db_session.flush()
    for index in range(1, 51):
        db_session.add(
            KnowledgeEvaluationCase(
                tenant_id=tenant_id,
                evaluation_set_id=evaluation_set.id,
                external_case_id=f"Q-{index:03d}",
                question=f"脱敏客户问题 {index:03d}",
                expected_terms=["标准套餐"],
                expected_source_uri="customer-doc://fixture/product",
            )
        )
    db_session.add(
        KnowledgeEvaluationRun(
            tenant_id=tenant_id,
            evaluation_set_id=evaluation_set.id,
            run_mode="final_answer_quality",
            total_cases=50,
            answered_cases=50,
            passed_cases=50,
            citation_covered_cases=50,
            hit_rate=1,
            citation_coverage=1,
            expected_term_coverage=1,
            summary_payload={"customer_data_used": True, "internal_sample_used": False},
        )
    )


def test_owner_reads_pilot_readiness_without_customer_or_channel_overclaim(client) -> None:
    tenant = _create_tenant(client, "pilot-readiness-owner")
    token = _bootstrap_user(client, tenant, email="pilot-owner@example.com")

    res = client.get(
        f"/api/tenants/{tenant['id']}/pilot-readiness",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["schema_version"] == "p3-06u-26h2w-pilot0.readiness.v1"
    assert body["status"] in {"blocked", "pilot_candidate_ready_with_internal_data"}
    assert "正式客户验收签收" in body["not_ready_for"]
    assert "真实平台自动外发" in body["not_ready_for"]
    assert body["safety"]["real_platform_send_enabled"] is False
    assert body["safety"]["rpa_formal_delivery_enabled"] is False
    assert body["material_drop_gate_status"] in {
        "received_file_drop_ready_waiting_customer_files",
        "received_files_present_pending_data2r_validation",
        "received_files_validated_ready_for_pack12_rerun",
        "received_internal_sample_files_validated_ready_for_pack12_rerun",
        "not_checked",
        "missing",
        "blocked",
    }
    assert isinstance(body["material_drop_gate_evidence"], list)
    assert {step["code"] for step in body["steps"]} == {
        "local_environment",
        "owner_account",
        "knowledge_materials",
        "retest_confirmation",
        "quality_monthly_ops",
        "diagnostics_backup_update",
    }


def test_agent_cannot_read_pilot_readiness(client) -> None:
    tenant = _create_tenant(client, "pilot-readiness-agent")
    token = _bootstrap_user(client, tenant, role_code="agent", email="pilot-agent@example.com")

    res = client.get(
        f"/api/tenants/{tenant['id']}/pilot-readiness",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 403


def test_knowledge_confirmation_import_requires_real_customer_fields(client, db_session) -> None:
    tenant = _create_tenant(client, "pilot-confirmation")
    token = _bootstrap_user(client, tenant, email="pilot-confirmation-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    csv_text = "\n".join(
        [
            "signoff_item_id,section,item_name,review_status,confirmed_by,confirmed_at,reviewer_role,customer_comment,needs_change",
            "KB2-SIGNOFF-001,知识范围,业务对象覆盖,confirmed,王经理,2026-07-05T09:00:00+08:00,业务负责人,覆盖当前试点商品,false",
            "KB2-SIGNOFF-002,回答策略,售后政策,needs_revision,李主管,2026-07-05T09:10:00+08:00,客服负责人,售后时效要改,true",
        ]
    )

    res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-confirmations/imports",
        headers=headers,
        json={"filename": "customer_return.csv", "csv_text": csv_text},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["schema_version"] == "p3-06u-26h2w-pilot2.knowledge_confirmation_import.v1"
    assert body["total_rows"] == 2
    assert body["confirmed_count"] == 1
    assert body["needs_revision_count"] == 1
    assert body["ready_for_next_retest"] is True
    assert body["formal_customer_signoff_ready"] is False
    assert body["system_prefilled_customer_confirmation"] is False
    assert body["safety"]["raw_csv_persisted"] is False

    audit = db_session.query(AuditEvent).filter_by(action="knowledge_confirmation.imported").one()
    assert audit.resource_id == "customer_return.csv"
    assert "售后时效要改" not in audit.payload
    fact = db_session.query(PilotReadinessFact).filter_by(
        tenant_id=tenant["id"],
        fact_key="pilot2.knowledge_confirmation_import",
    ).one()
    assert fact.status == "passed_with_notes"
    assert fact.payload["total_rows"] == 2
    assert fact.payload["ready_for_next_retest"] is True
    assert fact.payload["raw_csv_persisted"] is False
    assert "售后时效要改" not in str(fact.payload)


def test_knowledge_confirmation_import_blocks_pending_missing_reviewer_and_sensitive_text(client) -> None:
    tenant = _create_tenant(client, "pilot-confirmation-blocked")
    token = _bootstrap_user(client, tenant, email="pilot-confirmation-blocked-owner@example.com")
    csv_text = "\n".join(
        [
            "signoff_item_id,section,item_name,review_status,confirmed_by,confirmed_at,reviewer_role,customer_comment,needs_change",
            "KB2-SIGNOFF-001,知识范围,业务对象覆盖,confirmed,,2026-07-05T09:00:00+08:00,业务负责人,api_key=sk-this-should-not-pass,false",
            "KB2-SIGNOFF-002,回答策略,售后政策,pending,,,,,false",
        ]
    )

    res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-confirmations/imports",
        headers={"Authorization": f"Bearer {token}"},
        json={"filename": "bad_customer_return.csv", "csv_text": csv_text},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "blocked"
    assert body["ready_for_next_retest"] is False
    assert body["pending_count"] == 1
    assert any("缺少确认人" in blocker for blocker in body["blockers"])
    assert any("疑似密钥" in blocker for blocker in body["blockers"])


def test_pilot_readiness_does_not_promote_customer_ready_from_confirmation_only(client, db_session) -> None:
    tenant = _create_tenant(client, "pilot-fact-authority-confirmation-only")
    token = _bootstrap_user(client, tenant, email="pilot-fact-authority-owner@example.com")
    csv_text = "\n".join(
        [
            "signoff_item_id,section,item_name,review_status,confirmed_by,confirmed_at,reviewer_role,customer_comment,needs_change",
            "KB2-SIGNOFF-001,知识范围,业务对象覆盖,confirmed,王经理,2026-07-05T09:00:00+08:00,业务负责人,确认,false",
        ]
    )
    import_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-confirmations/imports",
        headers={"Authorization": f"Bearer {token}"},
        json={"filename": "customer_return.csv", "csv_text": csv_text},
    )
    assert import_res.status_code == 200

    res = client.get(
        f"/api/tenants/{tenant['id']}/pilot-readiness",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["customer_data_ready"] is False
    assert body["customer_data_readiness_source"] == "database_fact_chain"
    assert any("真实资料批次" in blocker for blocker in body["customer_data_ready_blockers"])
    assert any("真实客户知识复测" in blocker for blocker in body["customer_data_ready_blockers"])
    assert body["summary_evidence_authority"] == "engineering_evidence_only"


def test_pilot_readiness_requires_complete_database_fact_chain_for_customer_data(client, db_session) -> None:
    tenant = _create_tenant(client, "pilot-fact-authority-complete")
    token = _bootstrap_user(client, tenant, email="pilot-fact-authority-complete-owner@example.com")
    _seed_trial_ready_records(db_session, tenant["id"])
    material_batch = CustomerMaterialBatch(
        tenant_id=tenant["id"],
        batch_code="real-material-batch-001",
        status="customer_real_materials_ready",
        material_sha256="m" * 64,
        question_sha256="q" * 64,
        manifest_sha256="n" * 64,
        material_row_count=5,
        question_count=50,
        record_type_coverage=[
            "business_object",
            "standard_qa",
            "process_policy",
            "forbidden_commitment",
            "handoff_rule",
        ],
        question_action_coverage=[
            "answer_with_reference",
            "handoff",
            "reject_forbidden_commitment",
            "ask_clarifying_question",
        ],
        blocker_count=0,
        desensitization_risk_count=0,
        manifest_summary={"customer_data_used_declared": True},
    )
    db_session.add(material_batch)
    db_session.flush()
    db_session.add_all(
        [
            PilotReadinessFact(
                tenant_id=tenant["id"],
                fact_key="data3.customer_material_batch",
                status="customer_real_materials_ready",
                source="database",
                evidence_path=f"customer_material_batches:{material_batch.id}",
                payload={
                    "batch_code": material_batch.batch_code,
                    "material_row_count": material_batch.material_row_count,
                    "question_count": material_batch.question_count,
                    "record_type_coverage": material_batch.record_type_coverage,
                    "question_action_coverage": material_batch.question_action_coverage,
                    "blocker_count": 0,
                    "desensitization_risk_count": 0,
                    "real_customer_materials_ready": True,
                },
                not_ready_for=["正式客户验收签收"],
            ),
            PilotReadinessFact(
                tenant_id=tenant["id"],
                fact_key="kb7.customer_knowledge_retest",
                status="customer_knowledge_retest_ready_with_customer_data",
                source="database",
                evidence_path="knowledge_retest:unit",
                payload={
                    "customer_data_used": True,
                    "internal_sample_used": False,
                    "final_answer_quality_checked": True,
                    "citation_coverage": 1,
                },
                not_ready_for=["正式客户验收签收"],
            ),
        ]
    )
    db_session.commit()
    csv_text = "\n".join(
        [
            "signoff_item_id,section,item_name,review_status,confirmed_by,confirmed_at,reviewer_role,customer_comment,needs_change",
            "KB2-SIGNOFF-001,知识范围,业务对象覆盖,confirmed,王经理,2026-07-05T09:00:00+08:00,业务负责人,确认,false",
        ]
    )
    import_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-confirmations/imports",
        headers={"Authorization": f"Bearer {token}"},
        json={"filename": "customer_return.csv", "csv_text": csv_text},
    )
    assert import_res.status_code == 200

    res = client.get(
        f"/api/tenants/{tenant['id']}/pilot-readiness",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "pilot_candidate_ready_with_customer_data"
    assert body["customer_data_ready"] is True
    assert body["customer_data_ready_blockers"] == []
    assert [item["source"] for item in body["customer_data_ready_evidence"]] == [
        "database_fact",
        "database_fact",
        "database_fact",
    ]


def test_customer_material_precheck_accepts_valid_in_memory_package(client, db_session) -> None:
    tenant = _create_tenant(client, "pilot-material-precheck")
    token = _bootstrap_user(client, tenant, email="pilot-material-owner@example.com")

    res = client.post(
        f"/api/tenants/{tenant['id']}/customer-materials/precheck",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "materials_csv": _material_csv(),
            "trial_questions_csv": _questions_csv(),
            "manifest_json": _manifest_json(),
        },
    )

    assert res.status_code == 200
    body = res.json()
    assert body["schema_version"] == "p3-06u-26h2w-data2r4.customer_material_precheck.v1"
    assert body["status"] == "ready_for_file_drop"
    assert body["metrics"]["material_rows"] == 5
    assert body["metrics"]["trial_question_count"] == 50
    assert body["readiness"]["material_precheck_passed"] is True
    assert body["readiness"]["real_customer_materials_ready"] is False
    assert body["safety"]["raw_materials_persisted"] is False
    assert body["persisted_batch"]["status"] == "precheck_passed_waiting_file_drop"
    assert body["persisted_batch"]["question_count"] == 50

    audit = db_session.query(AuditEvent).filter_by(action="customer_materials.prechecked").one()
    audit_payload = _audit_payload(audit)
    assert audit_payload["status"] == "ready_for_file_drop"
    assert "客户脱敏问题" not in str(audit_payload)
    batch = db_session.query(CustomerMaterialBatch).filter_by(tenant_id=tenant["id"]).one()
    assert batch.material_row_count == 5
    assert batch.question_count == 50
    assert batch.material_sha256
    assert batch.question_sha256
    assert batch.manifest_sha256
    assert "客户脱敏问题" not in str(batch.manifest_summary)
    fact = db_session.query(PilotReadinessFact).filter_by(
        tenant_id=tenant["id"],
        fact_key="data3.customer_material_batch",
    ).one()
    assert fact.status == "waiting_for_real_customer_materials"
    assert fact.payload["raw_materials_persisted"] is False


def test_customer_material_batches_list_starts_empty_then_shows_hash_only_precheck_history(client) -> None:
    tenant = _create_tenant(client, "pilot-material-batches")
    token = _bootstrap_user(client, tenant, email="pilot-material-batches-owner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    empty_res = client.get(f"/api/tenants/{tenant['id']}/customer-materials/batches", headers=headers)
    assert empty_res.status_code == 200
    empty_body = empty_res.json()
    assert empty_body["schema_version"] == "p3-06u-26h2w-nc3.customer_material_batch_list.v1"
    assert empty_body["status"] == "waiting_for_material_precheck"
    assert empty_body["batches"] == []
    assert empty_body["readiness"]["raw_materials_persisted"] is False

    precheck_res = client.post(
        f"/api/tenants/{tenant['id']}/customer-materials/precheck",
        headers=headers,
        json={
            "materials_csv": _material_csv(),
            "trial_questions_csv": _questions_csv(first_question="客户专属隐私问题不应回显"),
            "manifest_json": _manifest_json(customer_alias="只显示别名"),
        },
    )
    assert precheck_res.status_code == 200

    list_res = client.get(f"/api/tenants/{tenant['id']}/customer-materials/batches", headers=headers)
    assert list_res.status_code == 200
    body = list_res.json()
    assert body["status"] == "material_precheck_batches_available"
    assert body["latest_batch"]["status"] == "precheck_passed_waiting_file_drop"
    assert body["counts"]["total"] == 1
    assert body["counts"]["precheck_passed_waiting_file_drop"] == 1
    assert body["readiness"]["has_file_drop_candidate"] is True
    assert body["readiness"]["real_customer_materials_ready"] is False
    assert body["safety"]["raw_materials_persisted"] is False
    assert "客户专属隐私问题不应回显" not in str(body)
    assert "只显示别名" not in str(body)


def test_customer_material_template_package_feeds_precheck_without_marking_customer_ready(client) -> None:
    tenant = _create_tenant(client, "pilot-material-template")
    token = _bootstrap_user(client, tenant, email="pilot-material-template-owner@example.com")

    template_res = client.get(
        f"/api/tenants/{tenant['id']}/customer-materials/template-package",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert template_res.status_code == 200
    template_body = template_res.json()
    assert template_body["schema_version"] == "p3-06u-26h2w-data2r5.customer_material_template_package.v1"
    assert template_body["readiness"]["real_customer_materials_ready"] is False
    assert template_body["readiness"]["raw_materials_persisted"] is False
    assert template_body["required_received_filenames"]["materials_csv"] == "customer_materials_received.csv"
    assert "record_type,item_id,business_object" in template_body["materials_template_csv"]
    assert len(template_body["field_guide"]) >= 10

    precheck_res = client.post(
        f"/api/tenants/{tenant['id']}/customer-materials/precheck",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "materials_csv": template_body["sample_materials_csv"],
            "trial_questions_csv": template_body["sample_trial_questions_csv"],
            "manifest_json": template_body["sample_manifest_json"],
        },
    )

    assert precheck_res.status_code == 200
    precheck_body = precheck_res.json()
    assert precheck_body["status"] == "ready_for_file_drop"
    assert precheck_body["metrics"]["trial_question_count"] == 50
    assert precheck_body["readiness"]["real_customer_materials_ready"] is False


def test_customer_material_handoff_bundle_downloads_fixed_received_filenames_without_customer_data(client) -> None:
    tenant = _create_tenant(client, "pilot-material-handoff-bundle")
    token = _bootstrap_user(client, tenant, email="pilot-material-handoff-owner@example.com")

    res = client.get(
        f"/api/tenants/{tenant['id']}/customer-materials/handoff-bundle",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["schema_version"] == "p3-06u-26h2w-data2r6.customer_material_handoff_bundle.v1"
    assert body["filename"] == "wanfa-customer-material-handoff-bundle.zip"
    assert body["content_type"] == "application/zip"
    assert body["body_encoding"] == "base64"
    assert body["readiness"]["real_customer_materials_ready"] is False
    assert body["safety"]["raw_materials_persisted"] is False
    assert body["safety"]["sample_package_is_customer_data"] is False

    archive_bytes = base64.b64decode(body["body"])
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        names = set(archive.namelist())
        assert names == {
            "customer_materials_received.csv",
            "customer_trial_questions_received.csv",
            "customer_material_manifest_received.json",
            "README.md",
        }
        materials = archive.read("customer_materials_received.csv").decode("utf-8")
        questions = archive.read("customer_trial_questions_received.csv").decode("utf-8")
        manifest = json.loads(archive.read("customer_material_manifest_received.json").decode("utf-8"))
        readme = archive.read("README.md").decode("utf-8")

    assert materials.startswith("record_type,item_id,business_object")
    assert questions.startswith("question_id,question,expected_answer")
    assert manifest["customer_data_used"] is False
    assert manifest["real_platform_send_enabled"] is False
    assert "示例内容" in readme


def test_customer_material_precheck_blocks_bad_package_without_persisting_raw_text(client, db_session) -> None:
    tenant = _create_tenant(client, "pilot-material-precheck-bad")
    token = _bootstrap_user(client, tenant, email="pilot-material-bad-owner@example.com")

    res = client.post(
        f"/api/tenants/{tenant['id']}/customer-materials/precheck",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "materials_csv": _material_csv(),
            "trial_questions_csv": _questions_csv(
                10,
                first_action="auto_send_real_platform",
                first_question="客户手机号 13812345678 想直接联系",
            ),
            "manifest_json": _manifest_json(real_platform_send_enabled=True, api_key="sk_should_not_pass_123456"),
        },
    )

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "blocked"
    assert body["readiness"]["material_precheck_passed"] is False
    assert any("不足 50" in blocker for blocker in body["blockers"])
    assert any("expected_action" in blocker for blocker in body["blockers"])
    assert any("疑似个人联系方式" in blocker for blocker in body["blockers"])
    assert any("疑似密钥" in blocker for blocker in body["blockers"])
    assert any("real_platform_send_enabled=true" in blocker for blocker in body["blockers"])

    audit = db_session.query(AuditEvent).filter_by(action="customer_materials.prechecked").one()
    audit_payload = _audit_payload(audit)
    assert audit_payload["status"] == "blocked"
    assert "13812345678" not in str(audit_payload)
    assert "sk_should_not_pass" not in str(audit_payload)
    batch = db_session.query(CustomerMaterialBatch).filter_by(tenant_id=tenant["id"]).one()
    assert batch.status == "blocked_precheck_failed"
    assert batch.desensitization_risk_count > 0
    assert "13812345678" not in str(batch.manifest_summary)
    fact = db_session.query(PilotReadinessFact).filter_by(
        tenant_id=tenant["id"],
        fact_key="data3.customer_material_batch",
    ).one()
    assert fact.status == "blocked_real_customer_materials_invalid"

    list_res = client.get(
        f"/api/tenants/{tenant['id']}/customer-materials/batches",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_res.status_code == 200
    list_body = list_res.json()
    assert list_body["status"] == "blocked_latest_material_precheck"
    assert list_body["counts"]["blocked_precheck_failed"] == 1
    assert list_body["counts"]["desensitization_risk_count"] > 0
    assert "13812345678" not in str(list_body)
    assert "sk_should_not_pass" not in str(list_body)


def test_safe_test_conversation_creates_local_only_inbound_session(client, db_session) -> None:
    tenant = _create_tenant(client, "pilot-safe-test-conversation")
    token = _bootstrap_user(client, tenant, email="pilot-safe-test-owner@example.com")

    res = client.post(
        f"/api/tenants/{tenant['id']}/pilot-safe-test-conversation",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["schema_version"] == "p3-06u-26h2w-fe11.safe_test_conversation.v1"
    assert body["tenant_id"] == tenant["id"]
    assert body["external_write_performed"] is False
    assert body["safety"]["real_platform_send_enabled"] is False

    conversation = db_session.query(Conversation).filter_by(id=body["conversation_id"]).one()
    assert conversation.tenant_id == tenant["id"]
    assert conversation.subject == "本地安全测试会话"
    message = db_session.query(Message).filter_by(id=body["message_id"]).one()
    assert message.direction == "inbound"
    assert message.sender_type == "customer"
    fact = db_session.query(PilotReadinessFact).filter_by(
        tenant_id=tenant["id"],
        fact_key="fe11.safe_test_conversation",
    ).one()
    assert fact.status == "safe_test_conversation_available"
    assert fact.payload["external_write_performed"] is False
