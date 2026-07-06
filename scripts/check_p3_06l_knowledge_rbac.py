#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    rbac = (ROOT / "backend/app/core/rbac.py").read_text(encoding="utf-8")
    api = (ROOT / "backend/app/api/knowledge.py").read_text(encoding="utf-8")
    test = (ROOT / "backend/tests/test_p3_06l_knowledge_rbac.py").read_text(encoding="utf-8")
    doc = (ROOT / "docs/P3-06L_KNOWLEDGE_RBAC.md").read_text(encoding="utf-8")

    require('"knowledge.read"' in rbac, "knowledge.read missing from RBAC")
    require('"knowledge.manage"' in rbac, "knowledge.manage missing from RBAC")
    require('"agent": {' in rbac and '"knowledge.read"' in rbac, "agent read permission missing")

    require('KNOWLEDGE_READ_PERMISSION = "knowledge.read"' in api, "read constant missing")
    require('KNOWLEDGE_MANAGE_PERMISSION = "knowledge.manage"' in api, "manage constant missing")
    require("require_permission(KNOWLEDGE_READ_PERMISSION)" in api, "read dependency missing")
    require("require_permission(KNOWLEDGE_MANAGE_PERMISSION)" in api, "manage dependency missing")
    require("require_current_principal" not in api, "old auth dependency remains in knowledge API")

    for phrase in [
        "knowledge-cards",
        "knowledge-searches",
        "knowledge-documents",
        "knowledge-document-searches",
        "knowledge-vector-index/rebuilds",
        "knowledge-embedding-provider-smoke-runs",
        "knowledge-gaps",
        "knowledge-evaluation-sets",
    ]:
        require(phrase in api, f"expected endpoint marker missing: {phrase}")

    for phrase in [
        "allowed_roles_for_permission",
        "knowledge.read",
        "knowledge.manage",
        "viewer_list_res.status_code == 403",
        "cross_list_res.status_code == 404",
    ]:
        require(phrase in test, f"expected test marker missing: {phrase}")

    for phrase in [
        "P3-06L",
        "知识库业务动作权限",
        "knowledge.read",
        "knowledge.manage",
        "viewer 当前不能读取知识原文",
        "外部 embedding provider smoke",
    ]:
        require(phrase in doc, f"expected doc marker missing: {phrase}")

    print("P3-06L knowledge RBAC checks passed.")


if __name__ == "__main__":
    main()
