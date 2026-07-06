from app.models import AuditEvent, KnowledgeImportBatch


def _bootstrap_user(client, *, slug: str, email: str, role_code: str = "owner") -> tuple[dict, dict, str]:
    tenant_res = client.post("/api/tenants", json={"name": f"{slug} 客户", "slug": slug})
    assert tenant_res.status_code == 201
    tenant = tenant_res.json()

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
    user = user_res.json()

    assign_res = client.post(f"/api/users/{user['id']}/roles", json={"role_id": role["id"]})
    assert assign_res.status_code == 201

    login_res = client.post(
        "/api/auth/login",
        json={"tenant_slug": tenant["slug"], "email": email, "password": "ChangeMe123!"},
    )
    assert login_res.status_code == 200
    return tenant, user, login_res.json()["access_token"]


def _sample_package() -> dict:
    return {
        "schema_version": "wanfa.knowledge_update_package.v1",
        "package_id": "pkg-after-sales-20260703",
        "package_name": "售后政策知识修复包",
        "source_diagnostic_filename": "wanfa-diagnostic-local-20260703.json",
        "notes": "补充售后、套餐和回归题，未包含客户聊天原文。",
        "business_objects": [
            {
                "ref": "lite-package",
                "type": "package",
                "title": "AI客服入门验证包",
                "aliases": ["入门版", "官网客服试点"],
                "summary": "适合先验证官网客服、核心问答、留资和转人工的小微企业。",
                "status": "active",
            }
        ],
        "object_knowledge_cards": [
            {
                "business_object_ref": "lite-package",
                "question": "入门验证包适合什么客户？",
                "answer": "适合先验证官网客服、核心问题、留资和转人工流程的小微企业。复杂多渠道自动外发需要后续授权。",
                "trigger_keywords": ["入门验证", "官网客服", "小微企业"],
                "source": "knowledge_update_package",
                "status": "active",
            }
        ],
        "knowledge_documents": [
            {
                "title": "售后退换政策",
                "source_type": "knowledge_update_package",
                "source_uri": "internal://policy/after-sales-20260703",
                "tags": ["售后", "退换"],
                "status": "active",
                "raw_text": "客户咨询七天退换时，应先确认订单状态、商品状态和平台规则。不能承诺无条件退款。",
            }
        ],
        "evaluation_sets": [
            {
                "name": "售后知识回归题集",
                "description": "验证售后政策是否能被检索命中。",
                "status": "active",
                "evaluation_mode": "customer_service_retrieval",
                "cases": [
                    {
                        "external_case_id": "after-sales-001",
                        "question": "超过七天还能退货吗？",
                        "expected_terms": ["订单状态", "商品状态", "平台规则"],
                        "expected_source_uri": "internal://policy/after-sales-20260703",
                        "forbidden_terms": ["无条件退款"],
                        "expected_human_review": False,
                        "allow_auto_reply": True,
                        "status": "active",
                    }
                ],
            }
        ],
    }


def test_owner_can_preview_knowledge_update_package_without_writing(client) -> None:
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-package-preview",
        email="knowledge-package-preview@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    preview_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-update-package/previews",
        headers=headers,
        json={"package": _sample_package()},
    )
    assert preview_res.status_code == 200
    preview = preview_res.json()
    assert preview["dry_run"] is True
    assert preview["can_apply"] is True
    assert preview["operation_counts"]["create"] == 4
    assert preview["operation_counts"]["skip"] == 0
    assert preview["import_batch_id"] is None
    assert preview["backup_snapshot"]["counts"]["knowledge_documents"] == 0
    assert "客户咨询七天退换时" not in str(preview)

    documents_res = client.get(f"/api/tenants/{tenant['id']}/knowledge-documents?status=active", headers=headers)
    assert documents_res.status_code == 200
    assert documents_res.json()["total"] == 0


def test_owner_can_import_knowledge_update_package_and_rollback_created_items(client, db_session) -> None:
    tenant, _, token = _bootstrap_user(
        client,
        slug="knowledge-package-import",
        email="knowledge-package-import@example.com",
    )
    headers = {"Authorization": f"Bearer {token}"}

    import_res = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-update-package-imports",
        headers=headers,
        json={"package": _sample_package()},
    )
    assert import_res.status_code == 201
    imported = import_res.json()
    assert imported["dry_run"] is False
    assert imported["can_apply"] is True
    assert imported["import_batch_id"] is not None
    assert imported["created"]["business_objects"]
    assert imported["created"]["object_knowledge_cards"]
    assert imported["created"]["knowledge_documents"]
    assert imported["created"]["evaluation_sets"]
    assert imported["safety"]["external_write_performed"] is False
    assert imported["safety"]["provider_call_performed"] is False
    assert "客户咨询七天退换时" not in str(imported)

    batch = db_session.get(KnowledgeImportBatch, imported["import_batch_id"])
    assert batch is not None
    assert batch.status == "applied"
    assert batch.result_payload["package_id"] == "pkg-after-sales-20260703"
    assert batch.result_payload["rollback_status"] == "available"

    documents_res = client.get(f"/api/tenants/{tenant['id']}/knowledge-documents?status=active", headers=headers)
    assert documents_res.status_code == 200
    documents = documents_res.json()
    assert documents["total"] == 1
    chunks_res = client.get(f"/api/knowledge-documents/{documents['items'][0]['id']}/chunks", headers=headers)
    assert chunks_res.status_code == 200
    assert len(chunks_res.json()) >= 1

    eval_sets_res = client.get(f"/api/tenants/{tenant['id']}/knowledge-evaluation-sets?status=active", headers=headers)
    assert eval_sets_res.status_code == 200
    assert eval_sets_res.json()["total"] == 1

    audit_actions = [event.action for event in db_session.query(AuditEvent).all()]
    assert "knowledge_update_package.imported" in audit_actions

    rollback_res = client.post(
        f"/api/knowledge-update-package-imports/{imported['import_batch_id']}/rollback",
        headers=headers,
        json={"reason": "回滚测试"},
    )
    assert rollback_res.status_code == 201
    rolled_back = rollback_res.json()
    assert rolled_back["rollback_status"] == "rolled_back"
    assert rolled_back["archived_counts"]["knowledge_documents"] == 1
    assert rolled_back["archived_counts"]["business_objects"] == 1

    active_documents_res = client.get(
        f"/api/tenants/{tenant['id']}/knowledge-documents?status=active",
        headers=headers,
    )
    assert active_documents_res.status_code == 200
    assert active_documents_res.json()["total"] == 0


def test_knowledge_update_package_skips_existing_items_and_blocks_agent(client) -> None:
    tenant, _, owner_token = _bootstrap_user(
        client,
        slug="knowledge-package-agent",
        email="knowledge-package-owner@example.com",
        role_code="owner",
    )
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    first_import = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-update-package-imports",
        headers=owner_headers,
        json={"package": _sample_package()},
    )
    assert first_import.status_code == 201

    second_preview = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-update-package/previews",
        headers=owner_headers,
        json={"package": _sample_package()},
    )
    assert second_preview.status_code == 200
    preview = second_preview.json()
    assert preview["can_apply"] is True
    assert preview["operation_counts"]["create"] == 0
    assert preview["operation_counts"]["skip"] == 4

    agent_role = client.post(
        f"/api/tenants/{tenant['id']}/roles",
        headers=owner_headers,
        json={"code": "agent", "name": "客服坐席"},
    ).json()
    agent_res = client.post(
        f"/api/tenants/{tenant['id']}/users",
        headers=owner_headers,
        json={"name": "客服坐席", "email": "knowledge-package-agent@example.com", "password": "ChangeMe123!"},
    )
    assert agent_res.status_code == 201
    assign_res = client.post(
        f"/api/users/{agent_res.json()['id']}/roles",
        headers=owner_headers,
        json={"role_id": agent_role["id"]},
    )
    assert assign_res.status_code == 201
    agent_login = client.post(
        "/api/auth/login",
        json={
            "tenant_slug": tenant["slug"],
            "email": "knowledge-package-agent@example.com",
            "password": "ChangeMe123!",
        },
    )
    assert agent_login.status_code == 200
    agent_headers = {"Authorization": f"Bearer {agent_login.json()['access_token']}"}

    forbidden = client.post(
        f"/api/tenants/{tenant['id']}/knowledge-update-package-imports",
        headers=agent_headers,
        json={"package": _sample_package()},
    )
    assert forbidden.status_code == 403
