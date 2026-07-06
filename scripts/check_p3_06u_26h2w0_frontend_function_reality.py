#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "P3-06U-26H2W0_FRONTEND_FUNCTION_REALITY_GATE_PLAN.md"
MATRIX = ROOT / "docs" / "FRONTEND_FUNCTION_REALITY_MATRIX.md"
WORKBENCH = ROOT / "frontend" / "src" / "components" / "conversation" / "ConversationWorkbenchPanel.tsx"
STYLES = ROOT / "frontend" / "src" / "styles.css"
H2W_STATIC = ROOT / "scripts" / "check_p3_06u_26h2w_chat_ui_and_completion_plan.py"
H2W_VISUAL = ROOT / "scripts" / "check_p3_06u_26h2w_chat_ui_visual.mjs"
OWNER_LOGIN_SMOKE = ROOT / "scripts" / "check_p3_06u_26h2w0_frontend_function_reality_owner_login.mjs"
KNOWLEDGE_OPERATIONS_OWNER_SMOKE = ROOT / "scripts" / "check_p3_06u_26h2w0_knowledge_operations_owner_login.mjs"
PRODUCT_PLAN = ROOT / "docs" / "PRODUCTIZATION_MASTER_PLAN_LITE_AND_STANDARD.md"


REQUIRED_PAGES = {
    "多渠道对话台",
    "知识库运营",
    "知识缺口",
    "知识评测",
    "运营总览",
    "质量复盘",
    "渠道接入",
    "运维与告警",
    "自动回复策略",
    "账号安全",
}

ALLOWED_STATUSES = {"真实可用", "只读可用", "禁用合理", "应隐藏", "仅后端"}


def fail(message: str) -> None:
    raise SystemExit(f"[FAIL] {message}")


def require_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        fail(f"{label} missing: {needle}")


def require_absent(text: str, needle: str, label: str) -> None:
    if needle in text:
        fail(f"{label} still contains banned text: {needle}")


def parse_matrix_rows(matrix_text: str) -> list[list[str]]:
    start = matrix_text.find("## 2. 功能真实性明细")
    end = matrix_text.find("## 3.", start)
    if start < 0 or end < 0:
        fail("matrix detail section missing")
    rows: list[list[str]] = []
    for line in matrix_text[start:end].splitlines():
      stripped = line.strip()
      if not stripped.startswith("|") or stripped.startswith("|---") or "页面 | 区域" in stripped:
          continue
      cells = [cell.strip() for cell in stripped.strip("|").split("|")]
      if len(cells) != 16:
          fail(f"matrix row should have 16 cells, got {len(cells)}: {stripped}")
      rows.append(cells)
    if len(rows) < 30:
        fail(f"matrix should contain at least 30 control-level rows, got {len(rows)}")
    return rows


def main() -> None:
    for path in [
        PLAN,
        MATRIX,
        WORKBENCH,
        STYLES,
        H2W_STATIC,
        H2W_VISUAL,
        OWNER_LOGIN_SMOKE,
        KNOWLEDGE_OPERATIONS_OWNER_SMOKE,
        PRODUCT_PLAN,
    ]:
        if not path.exists():
            fail(f"missing required file: {path}")

    plan = PLAN.read_text(encoding="utf-8")
    matrix = MATRIX.read_text(encoding="utf-8")
    workbench = WORKBENCH.read_text(encoding="utf-8")
    styles = STYLES.read_text(encoding="utf-8")
    h2w_static = H2W_STATIC.read_text(encoding="utf-8")
    h2w_visual = H2W_VISUAL.read_text(encoding="utf-8")
    owner_login_smoke = OWNER_LOGIN_SMOKE.read_text(encoding="utf-8")
    knowledge_operations_owner_smoke = KNOWLEDGE_OPERATIONS_OWNER_SMOKE.read_text(encoding="utf-8")
    product_plan = PRODUCT_PLAN.read_text(encoding="utf-8")

    for needle in [
        "P3-06U-26H2W-0 前端功能真实性与前后端契约门禁计划",
        "功能真实性矩阵",
        "停止门禁",
        "多渠道对话台专项门禁",
        "知识运营专项门禁",
    ]:
        require_contains(plan, needle, "H2W0 plan")

    for needle in [
        "前端功能真实性矩阵",
        "多渠道对话台",
        "知识库运营",
        "知识缺口",
        "知识评测",
        "运营总览",
        "质量复盘",
        "渠道接入",
        "运维与告警",
        "自动回复策略",
        "账号安全",
        "当前阻断项处理结果",
    ]:
        require_contains(matrix, needle, "function reality matrix")

    rows = parse_matrix_rows(matrix)
    pages = {row[0] for row in rows}
    missing_pages = REQUIRED_PAGES - pages
    if missing_pages:
        fail(f"matrix missing required pages: {', '.join(sorted(missing_pages))}")

    for row in rows:
        if any(cell == "" for cell in row):
            fail(f"matrix row has empty cell: {row}")
        status = row[13]
        conclusion = row[14]
        evidence = row[15]
        if status not in ALLOWED_STATUSES:
            fail(f"matrix row has invalid status {status}: {row}")
        if status == "应隐藏" and "隐藏" not in conclusion:
            fail(f"hidden row must say it is hidden: {row}")
        if evidence in {"无", "不适用"}:
            fail(f"matrix row must include evidence, got {evidence}: {row}")
        if row[2] in {"历史记录", "设为星标", "转接", "结束", "表情", "发送图片", "添加附件"} and status != "应隐藏":
            fail(f"known fake chat control must be hidden: {row}")

    for needle in [
        'data-function-reality="no-fake-chat-actions"',
        "service-chat-readonly-status",
        "保存接管回复",
    ]:
        require_contains(workbench, needle, "ConversationWorkbenchPanel")
    for banned in [
        "chat-head-action",
        "composer-tool-button",
        "历史记录",
        "设为星标",
        "发送图片",
        "添加附件",
        "已自动发送",
        "已接通全渠道",
        "已完成线上准确率",
        "已上传云端",
        "已正式签收",
    ]:
        require_absent(workbench, banned, "ConversationWorkbenchPanel")

    require_contains(styles, ".service-chat-readonly-status", "styles")
    require_contains(styles, ".composer-send-button", "styles")

    for needle in [
        'data-function-reality="no-fake-chat-actions"',
        "保存接管回复",
        "chat-head-action",
        "composer-tool-button",
    ]:
        require_contains(h2w_static, needle, "H2W static regression")
    require_contains(h2w_visual, "hasNoFakeHeaderActions", "H2W visual regression")
    require_contains(h2w_visual, "hasNoFakeComposerTools", "H2W visual regression")
    require_contains(h2w_visual, "保存接管回复", "H2W visual regression")

    for needle in [
        "owner_login_performed_through_ui",
        "demo_mode_used: false",
        "local-setup/owner",
        "data-role-smoke=\"login-form\"",
        "owner-live-function-reality",
        "external_platform_write_performed: false",
    ]:
        require_contains(owner_login_smoke, needle, "H2W0 owner-login browser gate")

    for needle in [
        "knowledge_operations_performed_through_ui",
        "business_object_create_performed_through_ui",
        "business_object_update_performed_through_ui",
        "object_knowledge_card_create_performed_through_ui",
        "knowledge_document_import_performed_through_ui",
        "knowledge_update_package_preview_performed_through_ui",
        "knowledge_update_package_import_performed_through_ui",
        "server_persistence_verified",
        "data-knowledge-action=\"create-business-object\"",
        "data-knowledge-action=\"edit-business-object\"",
        "data-knowledge-action=\"create-object-card\"",
        "data-knowledge-action=\"import-document\"",
        "data-knowledge-update-package-field=\"json\"",
        "external_platform_write_performed: false",
    ]:
        require_contains(knowledge_operations_owner_smoke, needle, "H2W0 knowledge operations owner-login gate")

    require_contains(product_plan, "P3-06U-26H2W-0", "productization master plan")
    require_contains(product_plan, "前端功能真实性", "productization master plan")
    require_contains(product_plan, "负责人真实登录", "productization master plan")
    require_contains(product_plan, "知识操作真实浏览器门禁", "productization master plan")

    print("[PASS] P3-06U-26H2W-0 frontend function reality static gate passed")


if __name__ == "__main__":
    main()
