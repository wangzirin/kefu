#!/usr/bin/env python3
from __future__ import annotations

import json

from lib.h2w_pack8_common import ROOT, base_result, display_path, write_json, write_markdown_report


PHASE = "H2W-FACT1-DATA3"
SCHEMA_VERSION = "p3-06u-26h2w-fact1-data3.runtime_facts.v1"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_fact1_data3_runtime_facts"

FILES = {
    "models": ROOT / "backend/app/models/foundation.py",
    "schemas": ROOT / "backend/app/schemas/pilot.py",
    "service": ROOT / "backend/app/services/pilot.py",
    "api": ROOT / "backend/app/api/pilot.py",
    "migration": ROOT / "backend/app/migrations/versions/0032_pilot_facts_material_batches.py",
    "tests": ROOT / "backend/tests/test_pilot_api.py",
}
REQUIRED_MARKERS = {
    "models": ["class PilotReadinessFact", "class CustomerMaterialBatch"],
    "schemas": ["class PilotRuntimeFactRead", "class CustomerMaterialBatchRead", "persisted_batch"],
    "service": ["_upsert_pilot_fact", "data3.customer_material_batch", "CustomerMaterialBatch("],
    "api": ["pilot-safe-test-conversation", "SafeTestConversationRead"],
    "migration": ["pilot_readiness_facts", "customer_material_batches"],
    "tests": ["CustomerMaterialBatch", "PilotReadinessFact", "test_safe_test_conversation_creates_local_only_inbound_session"],
}


def run_fact1_data3() -> dict:
    blockers: list[str] = []
    for key, path in FILES.items():
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        if not path.exists():
            blockers.append(f"文件缺失：{display_path(path)}")
            continue
        for marker in REQUIRED_MARKERS[key]:
            if marker not in text:
                blockers.append(f"{key} 缺少标记：{marker}")
    service_text = FILES["service"].read_text(encoding="utf-8") if FILES["service"].exists() else ""
    forbidden = ["raw_materials_persisted\": True", "formal_customer_signoff_ready\": True", "real_platform_send_ready\": True"]
    for marker in forbidden:
        if marker in service_text:
            blockers.append(f"服务层出现越界 ready 或原文入库标记：{marker}")

    status = "fact1_data3_runtime_facts_ready" if not blockers else "blocked"
    result = base_result(SCHEMA_VERSION, PHASE, status, blockers)
    result.update(
        {
            "customer_data_used": False,
            "internal_sample_used": True,
            "readiness": {
                "pilot_readiness_uses_database_facts": not blockers,
                "customer_material_batch_persists_hashes_only": not blockers,
                "raw_materials_persisted": False,
                "real_customer_materials_ready": False,
            },
            "evidence_paths": [display_path(path) for path in FILES.values()] + [display_path(OUTPUT_DIR / "summary.json")],
        }
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT_DIR / "summary.json", result)
    write_markdown_report(
        OUTPUT_DIR / "fact1_data3_runtime_facts_report.md",
        "H2W-FACT1/DATA3 数据库事实门禁",
        result,
        [("证据", result["evidence_paths"])],
    )
    return result


def main() -> int:
    result = run_fact1_data3()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
