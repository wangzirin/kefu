#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPORT_SCRIPT_PATH = ROOT / "scripts" / "import_customer_service_eval_bank.py"
TEMPLATE_CSV = ROOT / "evals" / "p3_06u_26f_real_customer_eval_bank_template.csv"
KNOWLEDGE_TEMPLATE = ROOT / "evals" / "p3_06u_26f_real_customer_knowledge_package_template.json"
P3_REALISTIC_BANK = ROOT / "evals" / "p3_01_realistic_customer_service_eval_bank_62_2026-06-27.csv"
DOC = ROOT / "docs" / "P3-06U-26F_REAL_CUSTOMER_BANK_AND_KNOWLEDGE_PACKAGE_TEMPLATE.md"


def _load_import_script():
    spec = importlib.util.spec_from_file_location("import_customer_service_eval_bank", IMPORT_SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load import_customer_service_eval_bank.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _failures_from_importer() -> list[str]:
    failures: list[str] = []
    script = _load_import_script()
    result = script.run_customer_service_eval_bank_import(
        input_path=TEMPLATE_CSV,
        name="P3-06U-26F 真实客户题库模板样例",
        description="用于验证 26F 字段映射和脱敏边界。",
    )
    if result["status"] != "validated":
        failures.append(f"26F template dry-run status={result['status']}")
    summary = result.get("summary", {})
    expected_pairs = {
        "total_cases": 8,
        "sensitive_row_count": 0,
        "expected_answer_rows": 8,
        "business_object_cases": 8,
        "source_reference_covered_cases": 8,
        "p3_06u_26f_real_customer_template_supported": True,
    }
    for key, expected in expected_pairs.items():
        if summary.get(key) != expected:
            failures.append(f"26F template summary {key}={summary.get(key)!r}, expected {expected!r}")
    if result.get("provider_call_performed") is not False:
        failures.append("26F template unexpectedly performed provider call")
    if result.get("external_write_performed") is not False:
        failures.append("26F template unexpectedly performed external write")
    if result.get("raw_text_logged") is not False:
        failures.append("26F template unexpectedly logs raw text")
    summary_dump = json.dumps({"summary": summary, "case_catalog": result.get("case_catalog")}, ensure_ascii=False)
    forbidden_raw_texts = [
        "我们只有官网吗",
        "可以先选择官网客服作为受控试点入口",
        "企业微信客服能不能直接让 AI 自动回复客户",
    ]
    for text in forbidden_raw_texts:
        if text in summary_dump:
            failures.append(f"raw text leaked in summary/catalog: {text}")

    p3_result = script.run_customer_service_eval_bank_import(
        input_path=P3_REALISTIC_BANK,
        name="P3-01 真实客户式试点题库样例 62题",
        description="兼容性回归。",
    )
    total_cases = p3_result.get("summary", {}).get("total_cases")
    if p3_result["status"] != "validated" or not (50 <= int(total_cases or 0) <= 100):
        failures.append("existing P3 62-case bank no longer validates in 50-100 range")
    return failures


def _failures_from_knowledge_template() -> list[str]:
    failures: list[str] = []
    data = json.loads(KNOWLEDGE_TEMPLATE.read_text(encoding="utf-8"))
    if data.get("template_version") != "p3_06u_26f_real_customer_knowledge_package_v1":
        failures.append("knowledge template version mismatch")
    if data.get("intended_case_count_min") != 50 or data.get("intended_case_count_max") != 100:
        failures.append("knowledge template must declare 50-100 intended case range")
    documents = data.get("documents")
    if not isinstance(documents, list) or len(documents) < 7:
        failures.append("knowledge template must contain at least 7 documents")
        documents = []
    source_uris = set()
    for index, doc in enumerate(documents, start=1):
        for key in ("title", "source_uri", "owner", "version", "applies_to_channels", "tags", "raw_text"):
            if not doc.get(key):
                failures.append(f"knowledge document {index} missing {key}")
        if doc.get("review_required_before_publish") is not True:
            failures.append(f"knowledge document {index} must require review before publish")
        source_uri = str(doc.get("source_uri") or "")
        if source_uri in source_uris:
            failures.append(f"duplicate source_uri: {source_uri}")
        source_uris.add(source_uri)
    csv_text = TEMPLATE_CSV.read_text(encoding="utf-8")
    required_refs = {
        "internal://docs/p3/product-scope-v1",
        "internal://docs/p3/channel-compliance-v1",
        "internal://docs/p3/pricing-package-v1",
        "internal://docs/p3/delivery-deployment-v1",
        "internal://docs/p3/support-refund-v1",
        "internal://docs/p3/account-invoice-security-v1",
    }
    for source_uri in required_refs:
        if source_uri not in source_uris:
            failures.append(f"knowledge template missing source_uri {source_uri}")
        if source_uri not in csv_text:
            failures.append(f"case template missing source_reference {source_uri}")
    privacy = data.get("privacy_boundary") or {}
    if privacy.get("external_write_performed") is not False or privacy.get("provider_call_performed") is not False:
        failures.append("privacy boundary must declare no provider call and no external write")
    return failures


def _failures_from_static_files() -> list[str]:
    failures: list[str] = []
    checks = {
        IMPORT_SCRIPT_PATH: [
            "customer_question",
            "expected_answer_hash",
            "business_object_hash",
            "p3_06u_26f_real_customer_template_supported",
        ],
        DOC: [
            "# P3-06U-26F 真实客户题库与知识包导入模板",
            "50-100",
            "expected_answer",
            "business_object",
            "不调用模型",
            "不打开真实外发",
            "不把 8 条模板样例写成真实 50-100 题验收",
            "P3-06U-26G",
        ],
        ROOT / "backend/tests/test_customer_service_eval_bank_import_script.py": [
            "test_p3_06u_26f_real_customer_template_alias_fields_are_supported",
            "P3_06U_26F_TEMPLATE_PATH",
        ],
    }
    for path, needles in checks.items():
        if not path.exists():
            failures.append(f"missing file: {path.relative_to(ROOT)}")
            continue
        content = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in content:
                failures.append(f"{path.relative_to(ROOT)} missing {needle!r}")
    return failures


def main() -> int:
    failures: list[str] = []
    for check in (_failures_from_importer, _failures_from_knowledge_template, _failures_from_static_files):
        failures.extend(check())
    if failures:
        print("P3-06U-26F template check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("P3-06U-26F template check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
