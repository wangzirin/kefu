#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_nc1_pilot_fact_authority"
SCHEMA_VERSION = "p3-06u-26h2w-nc1.pilot_fact_authority.v1"


FILES = {
    "pilot_service": ROOT / "backend/app/services/pilot.py",
    "pilot_schema": ROOT / "backend/app/schemas/pilot.py",
    "frontend_client": ROOT / "frontend/src/api/client.ts",
    "pilot_tests": ROOT / "backend/tests/test_pilot_api.py",
}


REQUIRED_MARKERS = {
    "pilot_service": [
        "_customer_data_readiness_from_database",
        "database_fact_chain",
        "pilot2.knowledge_confirmation_import",
        "summary_evidence_authority=\"engineering_evidence_only\"",
        "authority\": \"engineering_evidence_only\"",
        "_SUMMARY_MAX_AGE_SECONDS",
    ],
    "pilot_schema": [
        "customer_data_ready",
        "customer_data_readiness_source",
        "customer_data_ready_blockers",
        "summary_evidence_authority",
    ],
    "frontend_client": [
        "customer_data_ready?: boolean",
        "customer_data_readiness_source?: string",
        "summary_evidence_authority?: string",
    ],
    "pilot_tests": [
        "test_pilot_readiness_does_not_promote_customer_ready_from_confirmation_only",
        "test_pilot_readiness_requires_complete_database_fact_chain_for_customer_data",
        "fact_key=\"pilot2.knowledge_confirmation_import\"",
    ],
}


FORBIDDEN_MARKERS = {
    "pilot_service": [
        "customer_data_ready = customer_confirmation_ready and retest_ready",
        "customer_confirmation_ready = confirmation_event is not None",
    ]
}


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    blockers: list[str] = []
    evidence_paths: list[str] = []
    for key, path in FILES.items():
        evidence_paths.append(_rel(path))
        if not path.exists():
            blockers.append(f"缺少文件：{_rel(path)}")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in REQUIRED_MARKERS.get(key, []):
            if marker not in text:
                blockers.append(f"{_rel(path)} 缺少标记：{marker}")
        for marker in FORBIDDEN_MARKERS.get(key, []):
            if marker in text:
                blockers.append(f"{_rel(path)} 仍包含旧判定：{marker}")

    status = "nc1_pilot_fact_authority_ready" if not blockers else "blocked"
    report_path = OUTPUT_DIR / "pilot_fact_authority_report.md"
    summary_path = OUTPUT_DIR / "summary.json"
    result = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "blockers": blockers,
        "boundaries": [
            "pilot-readiness 客户资料 ready 只来自数据库事实链",
            "summary.json 只能作为工程证据，不抬高客户现场 ready",
            "客户确认导入只保存 hash、计数和结构化状态，不保存原始 CSV",
            "真实外发、真实渠道、正式客户签收仍关闭",
        ],
        "evidence_paths": evidence_paths + [_rel(report_path), _rel(summary_path)],
        "not_ready_for": [
            "真实平台自动外发",
            "正式客户验收签收",
            "成熟全渠道商用客服系统发布",
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "\n".join(
            [
                "# H2W-NC1 试点事实账本权威化门禁",
                "",
                f"- 状态：`{status}`",
                f"- 阻断项：{len(blockers)}",
                "",
                "## 结论",
                "",
                "客户资料 ready 的现场状态必须由数据库事实链决定；工程 summary 仅作为历史证据和门禁记录。",
                "",
                "## 阻断项",
                "",
                *(f"- {item}" for item in blockers),
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_json(summary_path, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
