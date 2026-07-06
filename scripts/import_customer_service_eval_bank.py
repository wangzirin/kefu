#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]

LIST_SPLIT_RE = re.compile(r"[;；|]")
PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
CN_ID_RE = re.compile(r"(?<!\d)\d{6}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)")


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def _split_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    else:
        text = str(value).strip()
        if not text:
            return []
        if text.startswith("["):
            try:
                loaded = json.loads(text)
            except json.JSONDecodeError:
                loaded = None
            if isinstance(loaded, list):
                items = loaded
            else:
                items = LIST_SPLIT_RE.split(text)
        else:
            items = LIST_SPLIT_RE.split(text)
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned_item = str(item).strip()
        if not cleaned_item or cleaned_item in seen:
            continue
        cleaned.append(cleaned_item)
        seen.add(cleaned_item)
    return cleaned


def _split_int_list(value) -> list[int]:
    ids: list[int] = []
    seen: set[int] = set()
    for item in _split_list(value):
        try:
            chunk_id = int(item)
        except ValueError:
            continue
        if chunk_id <= 0 or chunk_id in seen:
            continue
        ids.append(chunk_id)
        seen.add(chunk_id)
    return ids


def _first_nonempty(row: dict, *keys: str):
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        if str(value).strip():
            return value
    return ""


def _parse_bool(value, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if not text:
        return default
    if text in {"1", "true", "yes", "y", "是", "需要", "允许"}:
        return True
    if text in {"0", "false", "no", "n", "否", "不需要", "不允许"}:
        return False
    return default


def _parse_int(value, *, default: int) -> int:
    if value is None or str(value).strip() == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _risk_level_from_tags(value) -> str:
    tags = _split_list(value)
    if not tags:
        return "low"
    joined = " ".join(tags)
    if any(term in joined for term in ("法务", "投诉", "赔付", "监管", "隐私", "封号", "合同", "舆情")):
        return "high"
    if any(term in joined for term in ("退款", "价格", "售后", "渠道", "发票", "权限")):
        return "medium"
    return "low"


def _load_rows(input_path: Path) -> list[dict]:
    if not input_path.exists():
        raise FileNotFoundError(f"input file not found: {input_path}")
    suffix = input_path.suffix.lower()
    if suffix == ".json":
        data = json.loads(input_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            rows = data.get("cases") or data.get("items")
        else:
            rows = data
        if not isinstance(rows, list):
            raise ValueError("JSON input must be a list or an object with cases/items")
        return [dict(row) for row in rows]
    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        return [dict(row) for row in csv.DictReader(file)]


def _sensitive_patterns(row: dict) -> list[str]:
    text = " ".join(
        str(row.get(field) or "")
        for field in ("question", "customer_question", "expected_answer", "annotation_notes", "business_object")
    )
    hits: list[str] = []
    if PHONE_RE.search(text):
        hits.append("mainland_mobile")
    if EMAIL_RE.search(text):
        hits.append("email")
    if CN_ID_RE.search(text):
        hits.append("cn_id")
    return hits


def _build_annotation_notes(row: dict) -> str:
    notes = str(row.get("annotation_notes") or "").strip()
    metadata: list[str] = []
    business_object = str(row.get("business_object") or "").strip()
    expected_answer = str(row.get("expected_answer") or "").strip()
    risk_tags = _split_list(row.get("risk_tags"))
    if business_object:
        metadata.append(f"business_object_hash={_hash_text(business_object)}")
    if expected_answer:
        metadata.append(f"expected_answer_hash={_hash_text(expected_answer)}")
    if risk_tags:
        metadata.append("risk_tags=" + ",".join(risk_tags[:8]))
    if row.get("source_reference"):
        metadata.append("source_reference_present=true")
    if not metadata:
        return notes
    suffix = "；".join(metadata)
    return f"{notes}；{suffix}" if notes else suffix


def _row_to_case(row: dict, *, row_number: int) -> dict:
    question = str(_first_nonempty(row, "question", "customer_question")).strip()
    if not question:
        raise ValueError(f"row {row_number}: question/customer_question is required")
    priority = _parse_int(row.get("priority"), default=100)
    priority = min(max(priority, 1), 9999)
    risk_level = str(row.get("risk_level") or "").strip() or _risk_level_from_tags(row.get("risk_tags"))
    expected_human_review_source = _first_nonempty(row, "expected_human_review", "handoff_expected")
    source_reference = _first_nonempty(row, "expected_source_uri", "source_reference")
    return {
        "external_case_id": str(row.get("external_case_id") or row.get("case_id") or "").strip(),
        "source_channel": str(row.get("source_channel") or "").strip(),
        "source_category": str(row.get("source_category") or row.get("category") or "").strip(),
        "question": question,
        "question_type": str(row.get("question_type") or "standard_customer_question").strip(),
        "expected_terms": _split_list(_first_nonempty(row, "expected_terms", "must_include")),
        "expected_source_uri": str(source_reference or "").strip(),
        "expected_document_title": str(row.get("expected_document_title") or "").strip(),
        "expected_chunk_ids": _split_int_list(row.get("expected_chunk_ids")),
        "must_have_all_evidence": _parse_bool(row.get("must_have_all_evidence"), default=False),
        "expected_human_review": _parse_bool(expected_human_review_source, default=False),
        "allow_auto_reply": _parse_bool(row.get("allow_auto_reply"), default=True),
        "forbidden_terms": _split_list(_first_nonempty(row, "forbidden_terms", "must_not_include")),
        "risk_level": risk_level,
        "annotation_notes": _build_annotation_notes(row),
        "required_citation": _parse_bool(row.get("required_citation"), default=True),
        "priority": priority,
        "status": str(row.get("status") or "active").strip(),
    }


def _summarize_cases(cases: list[dict], sensitive_rows: list[dict]) -> dict:
    risk_level_counts: dict[str, int] = {}
    question_type_counts: dict[str, int] = {}
    source_channel_counts: dict[str, int] = {}
    auto_reply_blocked = 0
    human_review_expected = 0
    full_evidence_cases = 0
    business_object_cases = 0
    expected_answer_rows = 0
    source_reference_covered_cases = 0
    for case in cases:
        risk_level_counts[case["risk_level"]] = risk_level_counts.get(case["risk_level"], 0) + 1
        question_type_counts[case["question_type"]] = question_type_counts.get(case["question_type"], 0) + 1
        channel = case["source_channel"] or "unspecified"
        source_channel_counts[channel] = source_channel_counts.get(channel, 0) + 1
        if not case["allow_auto_reply"]:
            auto_reply_blocked += 1
        if case["expected_human_review"]:
            human_review_expected += 1
        if case["expected_chunk_ids"] and case["must_have_all_evidence"]:
            full_evidence_cases += 1
        if "business_object_hash=" in case["annotation_notes"]:
            business_object_cases += 1
        if "expected_answer_hash=" in case["annotation_notes"]:
            expected_answer_rows += 1
        if case["expected_source_uri"]:
            source_reference_covered_cases += 1
    return {
        "total_cases": len(cases),
        "risk_level_counts": risk_level_counts,
        "question_type_counts": question_type_counts,
        "source_channel_counts": source_channel_counts,
        "auto_reply_blocked_cases": auto_reply_blocked,
        "human_review_expected_cases": human_review_expected,
        "full_evidence_cases": full_evidence_cases,
        "business_object_cases": business_object_cases,
        "expected_answer_rows": expected_answer_rows,
        "source_reference_covered_cases": source_reference_covered_cases,
        "sensitive_row_count": len(sensitive_rows),
        "raw_question_text_in_summary": False,
        "p3_06u_26f_real_customer_template_supported": True,
    }


def _case_catalog(cases: list[dict]) -> list[dict]:
    return [
        {
            "external_case_id": case["external_case_id"],
            "source_channel": case["source_channel"],
            "source_category": case["source_category"],
            "question_hash": _hash_text(case["question"]),
            "question_type": case["question_type"],
            "risk_level": case["risk_level"],
            "expected_terms_count": len(case["expected_terms"]),
            "expected_chunk_ids_count": len(case["expected_chunk_ids"]),
            "business_object_present": "business_object_hash=" in case["annotation_notes"],
            "expected_answer_present": "expected_answer_hash=" in case["annotation_notes"],
            "source_reference_present": bool(case["expected_source_uri"]),
            "expected_human_review": case["expected_human_review"],
            "allow_auto_reply": case["allow_auto_reply"],
        }
        for case in cases
    ]


def _post_payload(*, api_base: str, tenant_id: int, token: str, payload: dict, timeout: float) -> dict:
    url = f"{api_base.rstrip('/')}/api/tenants/{tenant_id}/knowledge-evaluation-sets"
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
        return {
            "status_code": response.status,
            "body": json.loads(body) if body else {},
        }


def run_customer_service_eval_bank_import(
    *,
    input_path: Path | str,
    name: str,
    description: str = "",
    status: str = "active",
    allow_sensitive_rows: bool = False,
    create: bool = False,
    api_base: str = "",
    tenant_id: int | None = None,
    token: str = "",
    timeout: float = 10.0,
) -> dict:
    path = Path(input_path)
    raw_rows = _load_rows(path)
    cases: list[dict] = []
    errors: list[str] = []
    sensitive_rows: list[dict] = []
    for index, row in enumerate(raw_rows, start=2 if path.suffix.lower() == ".csv" else 1):
        patterns = _sensitive_patterns(row)
        if patterns:
            sensitive_rows.append(
                {
                    "row": index,
                    "external_case_id": str(row.get("external_case_id") or row.get("case_id") or ""),
                    "patterns": patterns,
                }
            )
        try:
            cases.append(_row_to_case(row, row_number=index))
        except ValueError as exc:
            errors.append(str(exc))

    summary = _summarize_cases(cases, sensitive_rows)
    base_result = {
        "status": "validated",
        "input_file": str(path),
        "raw_text_logged": False,
        "provider_call_performed": False,
        "external_write_performed": False,
        "summary": summary,
        "case_catalog": _case_catalog(cases),
        "sensitive_rows": sensitive_rows,
        "validation_errors": errors,
        "payload": None,
        "api_result": None,
    }
    if errors:
        base_result["status"] = "validation_failed"
        return base_result
    if sensitive_rows and not allow_sensitive_rows:
        base_result["status"] = "blocked_sensitive_rows"
        return base_result

    payload = {
        "name": name.strip(),
        "description": description.strip(),
        "status": status,
        "evaluation_mode": "customer_service_retrieval",
        "cases": cases,
    }
    base_result["payload"] = payload
    if not create:
        return base_result
    if not api_base or tenant_id is None or not token:
        base_result["status"] = "validation_failed"
        base_result["validation_errors"] = ["create requires api_base, tenant_id and token"]
        base_result["payload"] = None
        return base_result
    try:
        api_result = _post_payload(
            api_base=api_base,
            tenant_id=tenant_id,
            token=token,
            payload=payload,
            timeout=timeout,
        )
    except HTTPError as exc:
        base_result["status"] = "api_failed"
        base_result["payload"] = None
        base_result["api_result"] = {"status_code": exc.code, "error": exc.reason}
        return base_result
    except URLError as exc:
        base_result["status"] = "api_failed"
        base_result["payload"] = None
        base_result["api_result"] = {"error": str(exc.reason)}
        return base_result
    base_result["status"] = "created"
    base_result["external_write_performed"] = True
    base_result["payload"] = None
    base_result["api_result"] = {
        "status_code": api_result["status_code"],
        "evaluation_set_id": api_result["body"].get("id"),
        "case_count": api_result["body"].get("case_count"),
    }
    return base_result


def main() -> int:
    parser = argparse.ArgumentParser(description="Import a desensitized customer-service evaluation bank.")
    parser.add_argument("input_path", type=Path)
    parser.add_argument("--name", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--status", default="active", choices=["draft", "active", "archived"])
    parser.add_argument("--allow-sensitive-rows", action="store_true")
    parser.add_argument("--output-payload", type=Path, default=None)
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--api-base", default="")
    parser.add_argument("--tenant-id", type=int, default=None)
    parser.add_argument("--token", default="")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    result = run_customer_service_eval_bank_import(
        input_path=args.input_path,
        name=args.name,
        description=args.description,
        status=args.status,
        allow_sensitive_rows=args.allow_sensitive_rows,
        create=args.create,
        api_base=args.api_base,
        tenant_id=args.tenant_id,
        token=args.token,
        timeout=args.timeout,
    )
    payload = result.pop("payload")
    if args.output_payload and payload is not None:
        args.output_payload.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        result["payload_written_to"] = str(args.output_payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"validated", "created"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
