from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


ACTIVE_BROWSER_SCRIPTS = [
    "scripts/check_p3_06u_26b_wechat_first_workbench.mjs",
    "scripts/check_p3_06u_26c_channel_account_configuration.mjs",
    "scripts/check_p3_06u_26d_knowledge_three_pages.mjs",
    "scripts/check_p3_06u_26e_answer_quality_evaluation.mjs",
    "scripts/check_p3_06u_26g_channel_sandbox_rpa_boundary.mjs",
    "scripts/check_p3_06u_24_knowledge_split_and_channel_accounts.mjs",
    "scripts/check_p3_06t_03_bi_overview.mjs",
]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def assert_contains(text: str, needle: str, label: str, failures: list[str]) -> None:
    if needle not in text:
        failures.append(f"{label}: missing {needle}")


def assert_not_contains(text: str, needle: str, label: str, failures: list[str]) -> None:
    if needle in text:
        failures.append(f"{label}: still contains {needle}")


def main() -> None:
    failures: list[str] = []

    styles = read("frontend/src/styles.css")
    assert_contains(styles, "--console-min-width: 1180px", "styles.css", failures)
    assert_contains(styles, "width: max(100vw, var(--console-min-width))", "styles.css", failures)
    assert_contains(styles, "grid-template-columns: 224px minmax(956px, 1fr)", "styles.css", failures)
    for blocked in [
        "@media (max-width: 960px)",
        "@media (min-width: 721px) and (max-width: 960px)",
        "@media (max-width: 560px)",
        "@media (max-width: 980px)",
        "@media (max-width: 900px)",
    ]:
        assert_not_contains(styles, blocked, "styles.css", failures)

    for script in ACTIVE_BROWSER_SCRIPTS:
        text = read(script)
        for blocked in ["mobile-390", "mobile: true", "channels-mobile", "viewport.mobile", "width: 390"]:
            assert_not_contains(text, blocked, script, failures)
        for required in ["width: 1440", "mobile: false"]:
            assert_contains(text, required, script, failures)

    doc = read("docs/P3-06U-26G1_DESKTOP_ONLY_CONSOLE_POLICY.md")
    for required in ["桌面中台", "1180px", "不再设计、优化或验收手机端", "历史文档", "P3-06U-26H"]:
        assert_contains(doc, required, "desktop-only policy doc", failures)

    readme = read("README.md")
    for required in ["P3-06U-26G1", "桌面中台模式收口", "旧手机/390 视口记录仅作为历史归档"]:
        assert_contains(readme, required, "README.md", failures)

    if failures:
        print("FAIL p3_06u_26g1_desktop_only_console")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("PASS p3_06u_26g1_desktop_only_console")


if __name__ == "__main__":
    main()
