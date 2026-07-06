from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def assert_contains(path: str, needle: str) -> None:
    content = read(path)
    if needle not in content:
        raise AssertionError(f"{path} missing required marker: {needle}")


def assert_not_contains(path: str, needles: list[str]) -> None:
    content = read(path)
    for needle in needles:
        if needle in content:
            raise AssertionError(f"{path} contains forbidden customer-facing copy: {needle}")


def main() -> None:
    forbidden = ["预览工作区", "预览工作台", "预览身份", "测试账号进入", "本地测试账号不可用"]
    for path in [
        "frontend/src/App.tsx",
        "frontend/src/components/common/WorkspaceState.tsx",
        "frontend/src/components/conversation/ConversationWorkbenchPanel.tsx",
        "frontend/src/components/knowledge/KnowledgeWorkspacePage.tsx",
    ]:
        assert_not_contains(path, forbidden)

    assert_contains("backend/app/api/auth.py", '@router.get("/local-setup/status"')
    assert_contains("backend/app/api/auth.py", '@router.post("/local-setup/owner"')
    assert_contains("backend/app/api/auth.py", "DEFAULT_LOCAL_ROLES")
    assert_contains("backend/app/schemas/auth.py", "class LocalSetupStatus")
    assert_contains("backend/app/schemas/auth.py", "class LocalOwnerSetupRequest")
    assert_contains("frontend/src/api/client.ts", "export async function getLocalSetupStatus")
    assert_contains("frontend/src/api/client.ts", "export async function createLocalOwner")
    assert_contains("frontend/src/App.tsx", 'data-local-setup-status="p3-06u-26h2w8a"')
    assert_contains("frontend/src/App.tsx", 'data-h2w3b-customer-knowledge-flow="true"')
    assert_contains("frontend/src/App.tsx", 'data-knowledge-action="create-business-object"')
    assert_contains("frontend/src/App.tsx", 'data-knowledge-action="create-object-card"')
    assert_contains("frontend/src/App.tsx", 'data-knowledge-action="import-document"')
    assert_contains("frontend/src/App.tsx", 'data-knowledge-field="business-object-title"')
    assert_contains("frontend/src/App.tsx", 'data-knowledge-field="object-card-question"')
    assert_contains("frontend/src/App.tsx", 'data-knowledge-field="document-raw-text"')
    assert_contains("frontend/src/App.tsx", "创建负责人并进入")
    assert_contains("frontend/src/App.tsx", "系统不会预置默认密码")
    assert_contains("scripts/repair_local_sqlite_schema.py", "business_objects")
    assert_contains("scripts/smoke_p3_06u_26h1_knowledge_write_path.py", "/business-objects")
    assert_contains("scripts/smoke_p3_06u_26h1_knowledge_write_path.py", "STANDARD_OPS_SMOKE_PASSWORD is required")
    assert_not_contains("scripts/smoke_p3_06u_26h1_knowledge_write_path.py", ["WanfaLocal#2026"])
    assert_contains("scripts/reset_local_admin_password.py", "Create or reset a local admin account")
    assert_contains(
        "docs/P3-06U-26H1_LOCAL_FIRST_RUN_ACCOUNT_AND_KNOWLEDGE_UPDATE_PATH.md",
        "本地库结构修复",
    )
    assert_contains(
        "docs/P3-06U-26H1_LOCAL_FIRST_RUN_ACCOUNT_AND_KNOWLEDGE_UPDATE_PATH.md",
        "知识写入冒烟",
    )


if __name__ == "__main__":
    main()
