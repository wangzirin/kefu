from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_PROJECT = Path("/Users/ericlee/Desktop/Workspace/Project_012_智能客服方案研究")
REFERENCE_REPO = WORKSPACE_PROJECT / "assets/open_source_references/AI-Customer-Service"
RELEASE_DIR = WORKSPACE_PROJECT / "assets/open_source_references/AI-Customer-Service-release"
MATRIX_PATH = ROOT / "research/rpa_browser_reply_feasibility/aijiakefu_platform_research_matrix.json"
MOCK_PAGE_PATH = ROOT / "research/rpa_browser_reply_feasibility/mock_platform_workbench.html"
MATRIX_RUNNER_PATH = ROOT / "scripts/run_p3_06u_12j_aijiakefu_platform_mock_matrix.mjs"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    require(REFERENCE_REPO.exists(), f"missing reference repo: {REFERENCE_REPO}")
    require((REFERENCE_REPO / "README.md").exists(), "AI-Customer-Service README missing")
    repo_files = [p.relative_to(REFERENCE_REPO).as_posix() for p in REFERENCE_REPO.rglob("*") if p.is_file() and ".git/" not in p.as_posix()]
    require(repo_files == ["README.md"], f"unexpected source files in reference repo: {repo_files}")

    archive = RELEASE_DIR / "default.rar"
    archive_list = RELEASE_DIR / "archive_file_list.txt"
    require(archive.exists(), "release archive missing")
    require(archive.stat().st_size > 200_000_000, "release archive unexpectedly small")
    require(archive_list.exists(), "archive file list missing")
    archive_text = archive_list.read_text(encoding="utf-8")
    for expected in [
        "爱嘉客服 v1.0.8/爱嘉客服.exe",
        "爱嘉客服 v1.0.8/WebDriver.exe",
        "爱嘉客服 v1.0.8/WindowsDriver.exe",
        "爱嘉客服 v1.0.8/Tool/config.json",
        "爱嘉客服 v1.0.8/Tool/config.yaml",
        "爱嘉客服 v1.0.8/Static/ProgramImage/douyin.png",
        "爱嘉客服 v1.0.8/Static/ProgramImage/doudian.png",
        "爱嘉客服 v1.0.8/Static/ProgramImage/qianniu.png",
        "爱嘉客服 v1.0.8/Static/ProgramImage/jingmai.png",
        "爱嘉客服 v1.0.8/Static/ProgramImage/pdd.png",
    ]:
        require(expected in archive_text, f"archive evidence missing: {expected}")

    require(MATRIX_PATH.exists(), f"missing matrix: {MATRIX_PATH}")
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    require(matrix["schema_version"] == "aijiakefu_platform_research_matrix.v1", "matrix schema mismatch")
    policy = matrix["global_delivery_policy"]
    for key in [
        "send_allowed",
        "auto_send_allowed",
        "external_write_enabled",
        "cookie_token_reuse_allowed",
        "private_protocol_allowed",
        "anti_detection_or_evasion_allowed",
    ]:
        require(policy[key] is False, f"global policy {key} must be false")

    platforms = {item["platform_id"]: item for item in matrix["platforms"]}
    require(set(platforms) == {"douyin", "qianniu", "jingmai", "pdd"}, "platform ids mismatch")
    for platform_id, item in platforms.items():
        require(item["aijiakefu_claim"], f"{platform_id} missing upstream claim")
        require(item["release_evidence"], f"{platform_id} missing release evidence")
        require("draft-only" in item["rpa_research_route"] or "draft-only" in item["rpa_research_route"].lower(), f"{platform_id} must stay draft-only")
        require(item["not_proven"], f"{platform_id} missing not_proven list")
        require(any("unattended_send_allowed" == value for value in item["not_proven"]), f"{platform_id} must not prove unattended send")

    mock_text = MOCK_PAGE_PATH.read_text(encoding="utf-8")
    for platform_id in platforms:
        require(f"{platform_id}:" in mock_text, f"mock page missing scenario {platform_id}")
    require(MATRIX_RUNNER_PATH.exists(), "matrix runner missing")
    runner_text = MATRIX_RUNNER_PATH.read_text(encoding="utf-8")
    require("RPA_ALLOW_SEND" in runner_text and '"0"' in runner_text, "matrix runner must force draft-only")
    require("externalWritePerformed" in runner_text, "matrix runner must check external write")

    print(
        json.dumps(
            {
                "status": "passed",
                "reference_repo_files": repo_files,
                "release_archive_size": archive.stat().st_size,
                "platforms": sorted(platforms),
                "delivery_mode": policy["delivery_mode"],
                "send_allowed": policy["send_allowed"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}")
        raise SystemExit(1)
