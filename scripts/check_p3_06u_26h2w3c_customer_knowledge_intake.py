#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require_contains(path: str, needles: list[str]) -> None:
    content = read(path)
    missing = [needle for needle in needles if needle not in content]
    if missing:
        raise AssertionError(f"{path} missing required markers: {missing}")


def require_absent(path: str, needles: list[str]) -> None:
    content = read(path)
    found = [needle for needle in needles if needle in content]
    if found:
        raise AssertionError(f"{path} contains overclaiming markers: {found}")


def main() -> None:
    require_contains(
        "frontend/src/App.tsx",
        [
            "DEFAULT_CUSTOMER_KNOWLEDGE_INTAKE_CSV",
            "buildCustomerKnowledgeUpdatePackageFromCsv",
            "parseCustomerKnowledgeCsv",
            'data-h2w3c-customer-intake="true"',
            'data-h2w3c-customer-intake-field="csv"',
            'data-h2w3c-action="download-customer-intake-csv"',
            'data-h2w3c-action="convert-customer-intake"',
            "客户资料整理",
            "生成资料包",
            "检查资料包",
            "PDF、DOCX、XLSX 原件先作为来源留档，不自动解析入库",
            "导入不等于启用",
        ],
    )
    require_contains(
        "frontend/src/styles.css",
        [
            ".customer-knowledge-intake-card",
            ".customer-intake-grid",
            ".customer-intake-actions",
        ],
    )
    require_contains(
        "docs/P3-06U-26H2W3C_CUSTOMER_KNOWLEDGE_INTAKE_TEMPLATE.md",
            [
                "# P3-06U-26H2W3C 客户资料导入模板与预检第一片",
            "CSV/JSON 可以进入现有知识更新包预检",
            "PDF/DOCX/XLSX 暂不自动解析",
            "真实外发继续关闭",
            "导入不等于启用",
        ],
    )
    require_contains(
        "docs/FRONTEND_FUNCTION_REALITY_MATRIX.md",
            [
                "P3-06U-26H2W3C",
            "客户资料整理",
            "CSV 模板转换",
            "PDF/DOCX/XLSX 暂不自动解析",
            ],
    )
    require_absent(
        "docs/P3-06U-26H2W3C_CUSTOMER_KNOWLEDGE_INTAKE_TEMPLATE.md",
        [
            "PDF/DOCX/XLSX 已自动解析",
            "无需预检直接导入",
            "导入后自动外发",
        ],
    )
    print("P3-06U-26H2W3C customer knowledge intake static check passed.")


if __name__ == "__main__":
    main()
