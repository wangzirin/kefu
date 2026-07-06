from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SRC = ROOT / "frontend" / "src"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(path: str, *needles: str) -> None:
    content = read(path)
    missing = [needle for needle in needles if needle not in content]
    if missing:
        raise SystemExit(f"FAIL {path}: missing {missing}")


def assert_no_frontend_term(term: str) -> None:
    hits: list[str] = []
    for path in sorted(FRONTEND_SRC.rglob("*")):
        if path.suffix not in {".ts", ".tsx"}:
            continue
        content = path.read_text(encoding="utf-8")
        if term in content:
            rel = path.relative_to(ROOT)
            hits.append(str(rel))
    if hits:
        raise SystemExit(f"FAIL frontend/src: forbidden customer-facing term {term!r} in {hits}")


def main() -> None:
    for term in ["演示", "演示模式", "演示样本", "开发演示身份", "开发演示进入", "本地测试进入"]:
        assert_no_frontend_term(term)

    require(
        "frontend/src/components/common/WorkspaceState.tsx",
        'export const PREVIEW_DATA_LABEL = "样例数据"',
        'export const REAL_DATA_LABEL = "真实服务端数据"',
        'export const EXTERNAL_WRITE_OFF_LABEL = "真实外发关闭"',
        "当前是预览工作区",
        "预置会话、知识和队列",
    )
    require(
        "frontend/src/App.tsx",
        "预览工作区",
        "测试账号进入",
        "预览工作台",
        'data-role-smoke="local-dev-login"',
        'data-role-smoke="preview-workspace"',
        "真实外发关闭",
    )
    require(
        "frontend/src/components/conversation/ConversationWorkbenchPanel.tsx",
        "预览工作区",
        "PREVIEW_DATA_LABEL",
        "真实外发关闭",
    )
    require(
        "frontend/src/components/channels/ChannelConnectorCenterPanel.tsx",
        "PREVIEW_DATA_LABEL",
        "REAL_DATA_LABEL",
        "EXTERNAL_WRITE_OFF_LABEL",
    )
    require(
        "frontend/src/components/quality/QualityReviewPanel.tsx",
        "PREVIEW_DATA_LABEL",
        "REAL_DATA_LABEL",
    )
    require(
        "docs/P3-06U-26_ENGINEERING_OPTIMIZATION_MASTER_PLAN.md",
        "P3-06U-26A",
        "对外界面去演示味",
        "真实外发关闭提示被完全移除，导致边界不清",
    )
    print("PASS P3-06U-26A customer-facing copy")


if __name__ == "__main__":
    main()
