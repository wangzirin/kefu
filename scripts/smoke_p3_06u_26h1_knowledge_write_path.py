from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request


BASE_URL = os.getenv("STANDARD_OPS_SMOKE_BASE_URL", "http://127.0.0.1:8081").rstrip("/")
TENANT_SLUG = os.getenv("STANDARD_OPS_SMOKE_TENANT_SLUG", "wanfa-local-dev")
EMAIL = os.getenv("STANDARD_OPS_SMOKE_EMAIL", "real-test@wanfa.local")
PASSWORD = os.getenv("STANDARD_OPS_SMOKE_PASSWORD", "")


def request_json(path: str, *, method: str = "GET", token: str | None = None, payload: dict | None = None) -> dict:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{BASE_URL}{path}", data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed: HTTP {exc.code} {detail[:500]}") from exc


def main() -> None:
    if not PASSWORD:
        raise SystemExit("STANDARD_OPS_SMOKE_PASSWORD is required for this local smoke script")

    login = request_json(
        "/api/auth/login",
        method="POST",
        payload={"tenant_slug": TENANT_SLUG, "email": EMAIL, "password": PASSWORD},
    )
    token = login["access_token"]
    user = login["user"]
    tenant_id = user["tenant"]["id"]
    marker = str(int(time.time()))

    business_object = request_json(
        f"/api/tenants/{tenant_id}/business-objects",
        method="POST",
        token=token,
        payload={
            "type": "service",
            "title": f"本地知识链路验收服务-{marker}",
            "summary": "用于验证知识库运营页新增业务对象、绑定标准问答和文档导入链路。",
            "aliases": [f"知识链路验收-{marker}", "本地客服验收"],
            "status": "active",
        },
    )
    card = request_json(
        f"/api/business-objects/{business_object['id']}/knowledge-cards",
        method="POST",
        token=token,
        payload={
            "question": "本地知识链路验收服务适合什么场景？",
            "answer": "适合验证业务对象、标准问答和知识文档能否进入同一个客服知识运营闭环。",
            "trigger_keywords": ["知识链路", "本地验收", "标准问答"],
            "source": "local_smoke",
            "status": "active",
        },
    )
    document = request_json(
        f"/api/tenants/{tenant_id}/knowledge-documents",
        method="POST",
        token=token,
        payload={
            "title": f"本地知识链路验收文档-{marker}",
            "source_type": "manual_document",
            "source_uri": "local://p3-06u-26h1-smoke",
            "raw_text": (
                "适用问题：客户询问本地知识链路验收服务。\\n"
                "标准答案：该服务用于验证业务对象、标准问答和知识文档能否被客服系统读取。\\n"
                "禁止承诺：不要承诺已经完成真实平台外发。\\n"
                "引用来源：本地工程验收脚本。"
            ),
            "tags": ["本地验收", "知识运营"],
            "status": "active",
            "chunk_size": 120,
            "chunk_overlap": 20,
        },
    )

    objects = request_json(f"/api/tenants/{tenant_id}/business-objects?status=active", token=token)
    cards = request_json(f"/api/business-objects/{business_object['id']}/knowledge-cards?status=active", token=token)
    documents = request_json(f"/api/tenants/{tenant_id}/knowledge-documents?status=active", token=token)
    object_titles = {item["title"] for item in objects["items"]}
    document_titles = {item["title"] for item in documents["items"]}
    if business_object["title"] not in object_titles:
        raise AssertionError("created business object was not returned by list API")
    if card["id"] not in {item["id"] for item in cards["items"]}:
        raise AssertionError("created object knowledge card was not returned by list API")
    if document["title"] not in document_titles:
        raise AssertionError("created knowledge document was not returned by list API")

    print(
        json.dumps(
            {
                "tenant_slug": user["tenant"]["slug"],
                "user": user["email"],
                "business_object_id": business_object["id"],
                "object_knowledge_card_id": card["id"],
                "knowledge_document_id": document["id"],
                "business_object_total": objects["total"],
                "knowledge_document_total": documents["total"],
                "status": "ok",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
