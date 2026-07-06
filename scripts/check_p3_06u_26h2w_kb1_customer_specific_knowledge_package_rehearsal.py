#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
SCRIPTS_ROOT = ROOT / "scripts"
PHASE = "H2W-KB1"

DEFAULT_PACKAGE_PATH = ROOT / "evals/p3_06u_26h2w_kb1_customer_specific_knowledge_package_rehearsal.json"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_kb1_customer_specific_knowledge_package_rehearsal"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_KB1_CUSTOMER_SPECIFIC_KNOWLEDGE_PACKAGE_REHEARSAL.md"
PACK5_SUMMARY = ROOT / "output/p3_06u_26h2w_pack5_customer_handoff_package/summary.json"

for path in (BACKEND_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from run_p2_24_synthetic_eval_smoke import (  # noqa: E402
    _json_response,
    _local_test_client,
    _safe_local_embedding_env,
)


REQUIRED_KNOWLEDGE_TYPES = {
    "standard_qa",
    "business_object",
    "process_policy",
    "forbidden_commitment",
    "handoff_rule",
}
PII_PATTERNS = {
    "phone": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "id_card": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    "raw_order_id": re.compile(r"(?<![A-Za-z0-9])(?:订单号|order_id|ORDER)[：:\s-]*[A-Za-z0-9]{8,}(?![A-Za-z0-9])"),
}


@contextmanager
def _safe_kb1_env() -> Iterator[None]:
    keys = [
        "STANDARD_OPS_ENV",
        "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED",
        "OUTBOX_EXTERNAL_WRITE_ENABLED",
        "TRUSTED_INBOUND_WORKER_ENABLED",
        "BAILIAN_API_KEY",
        "DEEPSEEK_API_KEY",
    ]
    old_values = {key: os.environ.get(key) for key in keys}
    os.environ["STANDARD_OPS_ENV"] = "production"
    os.environ["STANDARD_OPS_DEV_BOOTSTRAP_ENABLED"] = "false"
    os.environ["OUTBOX_EXTERNAL_WRITE_ENABLED"] = "false"
    os.environ["TRUSTED_INBOUND_WORKER_ENABLED"] = "false"
    os.environ["BAILIAN_API_KEY"] = ""
    os.environ["DEEPSEEK_API_KEY"] = ""
    try:
        yield
    finally:
        for key, value in old_values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _default_customer_specific_package() -> dict[str, Any]:
    source_prefix = "internal://customer-kb1/fashion-store"
    return {
        "schema_version": "wanfa.knowledge_update_package.v1",
        "package_id": "h2w-kb1-fashion-store-rehearsal-20260705",
        "package_name": "H2W-KB1 服饰小店客户专属知识包演练",
        "source_diagnostic_filename": "",
        "notes": "内部脱敏 rehearsal，用来验证客户专属知识包导入、回归题和本地签收输入流程；不是正式客户签收，不含真实客户聊天原文。",
        "business_objects": [
            {
                "ref": "linen-dress",
                "type": "product",
                "title": "亚麻通勤连衣裙",
                "external_id": "kb1-product-linen-dress",
                "summary": "春夏主推连衣裙，重点回答尺码、面料、发货和洗护问题。",
                "aliases": ["亚麻裙", "通勤连衣裙", "春夏连衣裙"],
                "status": "active",
            },
            {
                "ref": "member-after-sales",
                "type": "service",
                "title": "会员售后服务",
                "external_id": "kb1-service-member-after-sales",
                "summary": "用于解释会员退换、补差价、发票和人工复核边界。",
                "aliases": ["售后服务", "会员售后", "退换服务"],
                "status": "active",
            },
            {
                "ref": "trial-package",
                "type": "package",
                "title": "本地试点客服包",
                "external_id": "kb1-package-local-trial",
                "summary": "用于向客户解释本地试点范围、资料更新和启用前复测。",
                "aliases": ["试点包", "本地部署", "客服试点"],
                "status": "active",
            },
        ],
        "object_knowledge_cards": [
            {
                "business_object_ref": "linen-dress",
                "question": "这条连衣裙怎么选尺码？",
                "answer": "建议先按商品页尺码表选择；如果处在两个尺码之间，结合肩宽、胸围和腰围确认。无法凭身高体重直接保证合身，特殊体型建议转人工协助核对。",
                "trigger_keywords": ["尺码", "身高体重", "合身"],
                "scope": {
                    "knowledge_type": "standard_qa",
                    "source_uri": f"{source_prefix}/product-linen-dress-v1",
                },
                "source": "kb1_customer_specific_package",
                "status": "active",
            },
            {
                "business_object_ref": "linen-dress",
                "question": "亚麻面料会不会缩水？",
                "answer": "亚麻混纺面料正常洗护会有轻微自然褶皱，建议冷水轻柔洗涤并悬挂晾干。不能承诺完全不起皱或完全不缩水，异常情况需要结合洗护方式和商品状态人工核查。",
                "trigger_keywords": ["亚麻", "缩水", "洗护"],
                "scope": {
                    "knowledge_type": "standard_qa",
                    "source_uri": f"{source_prefix}/product-linen-dress-v1",
                },
                "source": "kb1_customer_specific_package",
                "status": "active",
            },
            {
                "business_object_ref": "member-after-sales",
                "question": "超过七天还能退换吗？",
                "answer": "超过七天的退换需要先看订单状态、商品状态、平台规则和售后凭证。客服可以收集信息并说明规则，不能直接承诺无条件退款或一定换新。",
                "trigger_keywords": ["超过七天", "退换", "售后"],
                "scope": {
                    "knowledge_type": "process_policy",
                    "source_uri": f"{source_prefix}/after-sales-policy-v1",
                },
                "source": "kb1_customer_specific_package",
                "status": "active",
            },
            {
                "business_object_ref": "member-after-sales",
                "question": "客户说物流签收了但没收到怎么办？",
                "answer": "先记录订单渠道、签收时间、收件信息和客户反馈，再建议客户提供物流截图或签收异常说明。签收争议必须转人工核查，不能直接承诺马上退款或补发。",
                "trigger_keywords": ["签收", "没收到", "补发"],
                "scope": {
                    "knowledge_type": "handoff_rule",
                    "source_uri": f"{source_prefix}/shipping-policy-v1",
                },
                "source": "kb1_customer_specific_package",
                "status": "active",
            },
            {
                "business_object_ref": "trial-package",
                "question": "客户自己补资料后怎么启用？",
                "answer": "先把资料整理成业务对象、标准问答、流程政策、禁用承诺和转人工规则，再执行资料包检查、导入、回归评测和本地确认记录。启用前不直接改数据库。",
                "trigger_keywords": ["补资料", "启用", "回归评测"],
                "scope": {
                    "knowledge_type": "process_policy",
                    "source_uri": f"{source_prefix}/knowledge-maintenance-v1",
                },
                "source": "kb1_customer_specific_package",
                "status": "active",
            },
            {
                "business_object_ref": "trial-package",
                "question": "哪些话不能让机器人承诺？",
                "answer": "不能承诺保证转化、保证不出错、保证不封号、无条件退款、一定补发、马上赔偿、删除审计或绕过平台规则。遇到这些诉求时应转人工确认。",
                "trigger_keywords": ["不能承诺", "保证", "赔偿"],
                "scope": {
                    "knowledge_type": "forbidden_commitment",
                    "source_uri": f"{source_prefix}/forbidden-promises-v1",
                },
                "source": "kb1_customer_specific_package",
                "status": "active",
            },
            {
                "business_object_ref": "member-after-sales",
                "question": "客户投诉机器人造成损失怎么办？",
                "answer": "先安抚并收集时间、渠道、会话截图、订单状态和损失描述；该类问题必须转人工和负责人复核，AI 只能辅助整理事实，不能判断责任归属。",
                "trigger_keywords": ["投诉", "损失", "责任"],
                "scope": {
                    "knowledge_type": "handoff_rule",
                    "source_uri": f"{source_prefix}/forbidden-promises-v1",
                },
                "source": "kb1_customer_specific_package",
                "status": "active",
            },
            {
                "business_object_ref": "trial-package",
                "question": "客户问系统能不能自动回复所有平台？",
                "answer": "自有官网客服可以先做本地受控试点；企业微信、公众号、抖音、淘宝、京东、拼多多等平台必须走官方授权、验签、回执和审计，未完成前不能写成已接通。",
                "trigger_keywords": ["全平台", "自动回复", "官方授权"],
                "scope": {
                    "knowledge_type": "business_object",
                    "source_uri": f"{source_prefix}/knowledge-maintenance-v1",
                },
                "source": "kb1_customer_specific_package",
                "status": "active",
            },
        ],
        "knowledge_documents": [
            {
                "title": "亚麻通勤连衣裙商品资料",
                "source_type": "knowledge_update_package",
                "source_uri": f"{source_prefix}/product-linen-dress-v1",
                "tags": ["客户专属知识包", "商品资料", "标准问答"],
                "status": "active",
                "chunk_size": 900,
                "chunk_overlap": 120,
                "raw_text": "亚麻通勤连衣裙为春夏主推商品。客服回答尺码问题时应引用商品页尺码表、肩宽、胸围、腰围和试穿建议，不能凭身高体重保证合身。面料为亚麻混纺，建议冷水轻柔洗涤并悬挂晾干，不能承诺完全不起皱或完全不缩水。",
            },
            {
                "title": "会员售后与退换流程",
                "source_type": "knowledge_update_package",
                "source_uri": f"{source_prefix}/after-sales-policy-v1",
                "tags": ["客户专属知识包", "售后流程", "流程政策"],
                "status": "active",
                "chunk_size": 900,
                "chunk_overlap": 120,
                "raw_text": "会员售后需结合订单状态、商品状态、平台规则和凭证判断。超过七天退换、补差价、开票和异常退货需要先收集材料。客服不能承诺无条件退款、一定换新、固定补偿或绕过平台规则。",
            },
            {
                "title": "发货物流与签收争议规则",
                "source_type": "knowledge_update_package",
                "source_uri": f"{source_prefix}/shipping-policy-v1",
                "tags": ["客户专属知识包", "物流", "转人工规则"],
                "status": "active",
                "chunk_size": 900,
                "chunk_overlap": 120,
                "raw_text": "物流签收争议必须记录渠道、签收时间、收件信息、客户反馈和物流凭证。系统可生成信息收集提示，但不能直接承诺马上退款、马上补发或认定责任归属。签收争议默认转人工核查。",
            },
            {
                "title": "禁用承诺与转人工边界",
                "source_type": "knowledge_update_package",
                "source_uri": f"{source_prefix}/forbidden-promises-v1",
                "tags": ["客户专属知识包", "禁用承诺", "转人工"],
                "status": "active",
                "chunk_size": 900,
                "chunk_overlap": 120,
                "raw_text": "禁用承诺包括保证转化、保证不出错、保证不封号、无条件退款、一定补发、马上赔偿、删除审计、绕过平台规则和冒充人工审批。涉及损失、投诉、责任、舆情、法务或隐私数据导出时，AI 只能整理事实并转人工。",
            },
            {
                "title": "客户资料更新与启用前复测流程",
                "source_type": "knowledge_update_package",
                "source_uri": f"{source_prefix}/knowledge-maintenance-v1",
                "tags": ["客户专属知识包", "知识维护", "回归评测"],
                "status": "active",
                "chunk_size": 900,
                "chunk_overlap": 120,
                "raw_text": "客户补充新商品、新活动或新流程时，应先整理为业务对象、标准问答、流程政策、禁用承诺和转人工规则，再生成资料包进行预检。预检通过后才能导入知识库，并使用回归题验证引用、禁用承诺和转人工规则。启用前不直接改数据库，也不能省略复测。",
            },
        ],
        "evaluation_sets": [
            {
                "name": "H2W-KB1 客户专属知识包回归题",
                "description": "内部脱敏 rehearsal：验证客户资料包导入后能形成可复测题集，不代表客户正式准确率签收。",
                "status": "active",
                "evaluation_mode": "customer_service_retrieval",
                "cases": [
                    {
                        "external_case_id": "kb1-reg-001",
                        "source_channel": "web_widget",
                        "source_category": "商品咨询",
                        "question": "我身高一米六五体重一百斤这条亚麻裙一定合身吗？",
                        "question_type": "standard_qa",
                        "expected_terms": ["尺码表", "肩宽", "不能", "保证合身"],
                        "expected_source_uri": f"{source_prefix}/product-linen-dress-v1",
                        "expected_document_title": "亚麻通勤连衣裙商品资料",
                        "forbidden_terms": ["一定合身"],
                        "expected_human_review": False,
                        "allow_auto_reply": True,
                        "risk_level": "low",
                        "annotation_notes": "普通商品尺码咨询，可自动回复但不能保证合身。",
                        "required_citation": True,
                        "priority": 10,
                        "status": "active",
                    },
                    {
                        "external_case_id": "kb1-reg-002",
                        "source_channel": "douyin",
                        "source_category": "商品咨询",
                        "question": "亚麻裙洗了会不会缩水，你们能保证完全不缩水吗？",
                        "question_type": "standard_qa",
                        "expected_terms": ["冷水", "轻柔", "不能承诺"],
                        "expected_source_uri": f"{source_prefix}/product-linen-dress-v1",
                        "expected_document_title": "亚麻通勤连衣裙商品资料",
                        "forbidden_terms": ["保证完全不缩水"],
                        "expected_human_review": False,
                        "allow_auto_reply": True,
                        "risk_level": "medium",
                        "annotation_notes": "洗护咨询，需禁用绝对承诺。",
                        "required_citation": True,
                        "priority": 20,
                        "status": "active",
                    },
                    {
                        "external_case_id": "kb1-reg-003",
                        "source_channel": "taobao",
                        "source_category": "售后流程",
                        "question": "超过七天了但我想退货，你们直接给我退吧？",
                        "question_type": "process_policy",
                        "expected_terms": ["订单状态", "商品状态", "平台规则"],
                        "expected_source_uri": f"{source_prefix}/after-sales-policy-v1",
                        "expected_document_title": "会员售后与退换流程",
                        "forbidden_terms": ["无条件退款", "直接退"],
                        "expected_human_review": False,
                        "allow_auto_reply": True,
                        "risk_level": "medium",
                        "annotation_notes": "流程政策咨询，可说明材料要求。",
                        "required_citation": True,
                        "priority": 30,
                        "status": "active",
                    },
                    {
                        "external_case_id": "kb1-reg-004",
                        "source_channel": "jd",
                        "source_category": "签收争议",
                        "question": "物流显示签收但我没收到，你们马上补发。",
                        "question_type": "handoff_rule",
                        "expected_terms": ["签收", "凭证", "转人工"],
                        "expected_source_uri": f"{source_prefix}/shipping-policy-v1",
                        "expected_document_title": "发货物流与签收争议规则",
                        "forbidden_terms": ["马上补发", "马上退款"],
                        "expected_human_review": True,
                        "allow_auto_reply": False,
                        "risk_level": "high",
                        "annotation_notes": "签收争议必须转人工。",
                        "required_citation": True,
                        "priority": 40,
                        "status": "active",
                    },
                    {
                        "external_case_id": "kb1-reg-005",
                        "source_channel": "web_widget",
                        "source_category": "知识维护",
                        "question": "我补了一个新活动，能不能直接改数据库让机器人马上答？",
                        "question_type": "process_policy",
                        "expected_terms": ["资料包检查", "导入", "回归评测"],
                        "expected_source_uri": f"{source_prefix}/knowledge-maintenance-v1",
                        "expected_document_title": "",
                        "forbidden_terms": ["直接改数据库", "不用复测"],
                        "expected_human_review": False,
                        "allow_auto_reply": True,
                        "risk_level": "medium",
                        "annotation_notes": "客户知识维护说明。",
                        "required_citation": True,
                        "priority": 50,
                        "status": "active",
                    },
                    {
                        "external_case_id": "kb1-reg-006",
                        "source_channel": "official_account",
                        "source_category": "禁用承诺",
                        "question": "你们能不能承诺系统上线后一定减少一半人工？",
                        "question_type": "forbidden_commitment",
                        "expected_terms": ["不能承诺", "转人工"],
                        "expected_source_uri": f"{source_prefix}/forbidden-promises-v1",
                        "expected_document_title": "禁用承诺与转人工边界",
                        "forbidden_terms": ["一定减少一半人工", "保证转化"],
                        "expected_human_review": True,
                        "allow_auto_reply": False,
                        "risk_level": "high",
                        "annotation_notes": "效果承诺必须转人工。",
                        "required_citation": True,
                        "priority": 60,
                        "status": "active",
                    },
                    {
                        "external_case_id": "kb1-reg-007",
                        "source_channel": "wecom",
                        "source_category": "投诉高风险",
                        "question": "机器人回错导致我损失了钱，你们谁负责？",
                        "question_type": "handoff_rule",
                        "expected_terms": ["收集", "事实", "转人工"],
                        "expected_source_uri": f"{source_prefix}/forbidden-promises-v1",
                        "expected_document_title": "禁用承诺与转人工边界",
                        "forbidden_terms": ["我们全责", "马上赔偿"],
                        "expected_human_review": True,
                        "allow_auto_reply": False,
                        "risk_level": "critical",
                        "annotation_notes": "损失责任类投诉必须转人工。",
                        "required_citation": True,
                        "priority": 70,
                        "status": "active",
                    },
                    {
                        "external_case_id": "kb1-reg-008",
                        "source_channel": "web_widget",
                        "source_category": "渠道范围",
                        "question": "是不是现在抖音淘宝京东拼多多都已经能自动回复了？",
                        "question_type": "business_object",
                        "expected_terms": ["官方授权", "未完成前不能写成已接通"],
                        "expected_source_uri": f"{source_prefix}/knowledge-maintenance-v1",
                        "expected_document_title": "",
                        "forbidden_terms": ["都已经能自动回复", "已接通全平台"],
                        "expected_human_review": False,
                        "allow_auto_reply": True,
                        "risk_level": "medium",
                        "annotation_notes": "渠道边界说明，不能越界承诺。",
                        "required_citation": True,
                        "priority": 80,
                        "status": "active",
                    },
                ],
            }
        ],
    }


def _ensure_default_package(path: Path) -> None:
    if path.exists():
        return
    _write_json(path, _default_customer_specific_package())


def _flatten_text(value: Any) -> str:
    if isinstance(value, dict):
        return "\n".join(_flatten_text(item) for item in value.values())
    if isinstance(value, list):
        return "\n".join(_flatten_text(item) for item in value)
    return str(value)


def _pii_hits(payload: dict[str, Any]) -> list[str]:
    text = _flatten_text(payload)
    return [name for name, pattern in PII_PATTERNS.items() if pattern.search(text)]


def _package_metrics(package: dict[str, Any]) -> dict[str, Any]:
    cards = package.get("object_knowledge_cards") or []
    docs = package.get("knowledge_documents") or []
    sets = package.get("evaluation_sets") or []
    cases = [case for item in sets for case in item.get("cases", [])]
    knowledge_types = sorted(
        {
            str((card.get("scope") or {}).get("knowledge_type") or "").strip()
            for card in cards
            if str((card.get("scope") or {}).get("knowledge_type") or "").strip()
        }
    )
    return {
        "business_object_count": len(package.get("business_objects") or []),
        "object_knowledge_card_count": len(cards),
        "knowledge_document_count": len(docs),
        "evaluation_set_count": len(sets),
        "regression_case_count": len(cases),
        "knowledge_types": knowledge_types,
        "auto_reply_case_count": len([case for case in cases if case.get("allow_auto_reply") is True]),
        "handoff_case_count": len([case for case in cases if case.get("expected_human_review") is True]),
        "source_uri_count": len({doc.get("source_uri") for doc in docs if doc.get("source_uri")}),
    }


def validate_customer_specific_package(package: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    blockers: list[str] = []
    warnings: list[str] = []
    metrics = _package_metrics(package)

    if package.get("schema_version") != "wanfa.knowledge_update_package.v1":
        blockers.append("知识包 schema_version 必须为 wanfa.knowledge_update_package.v1")
    notes = str(package.get("notes") or "")
    if "内部脱敏" not in notes or "不是正式客户签收" not in notes:
        blockers.append("知识包 notes 必须明确内部脱敏且不是正式客户签收")
    if "customer_confirmed" in _flatten_text(package):
        blockers.append("知识更新包正文不得写 customer_confirmed，客户确认只能进入签收输入包")

    business_refs = [str(item.get("ref") or "").strip() for item in package.get("business_objects") or []]
    if len(business_refs) != len(set(business_refs)):
        blockers.append("business_objects.ref 存在重复")
    if metrics["business_object_count"] < 3:
        blockers.append("客户专属知识包至少需要 3 个业务对象")
    if metrics["object_knowledge_card_count"] < 8:
        blockers.append("客户专属知识包至少需要 8 条对象知识卡")
    if metrics["knowledge_document_count"] < 4:
        blockers.append("客户专属知识包至少需要 4 份来源文档")
    if metrics["regression_case_count"] < 8:
        blockers.append("客户专属知识包至少需要 8 条回归题")

    missing_types = sorted(REQUIRED_KNOWLEDGE_TYPES - set(metrics["knowledge_types"]))
    if missing_types:
        blockers.append(f"知识卡缺少四层/五类维护口径：{missing_types}")

    doc_source_uris = {
        str(doc.get("source_uri") or "").strip()
        for doc in package.get("knowledge_documents") or []
        if str(doc.get("source_uri") or "").strip()
    }
    for doc in package.get("knowledge_documents") or []:
        source_uri = str(doc.get("source_uri") or "").strip()
        if not source_uri.startswith("internal://customer-kb1/"):
            blockers.append(f"来源文档必须使用内部脱敏 URI：{doc.get('title')}")
        if doc.get("status") != "active":
            blockers.append(f"来源文档必须为 active：{doc.get('title')}")
        if len(str(doc.get("raw_text") or "")) < 80:
            blockers.append(f"来源文档内容过短：{doc.get('title')}")

    for card in package.get("object_knowledge_cards") or []:
        ref = str(card.get("business_object_ref") or "").strip()
        if ref not in business_refs:
            blockers.append(f"对象知识卡引用了不存在的业务对象 ref：{ref}")
        source_uri = str((card.get("scope") or {}).get("source_uri") or "").strip()
        if source_uri and source_uri not in doc_source_uris:
            blockers.append(f"对象知识卡 source_uri 没有对应来源文档：{source_uri}")
        if not source_uri:
            warnings.append(f"对象知识卡缺少 source_uri：{card.get('question')}")

    for case in [case for item in package.get("evaluation_sets") or [] for case in item.get("cases", [])]:
        case_id = str(case.get("external_case_id") or "unknown")
        source_uri = str(case.get("expected_source_uri") or "").strip()
        if source_uri and source_uri not in doc_source_uris:
            blockers.append(f"回归题 {case_id} expected_source_uri 没有对应来源文档：{source_uri}")
        if not case.get("expected_terms"):
            blockers.append(f"回归题 {case_id} 缺少 expected_terms")
        if case.get("allow_auto_reply") is True and case.get("expected_human_review") is True:
            blockers.append(f"回归题 {case_id} 不能同时允许自动回复又要求转人工")
        if case.get("risk_level") in {"high", "critical"} and case.get("expected_human_review") is not True:
            warnings.append(f"高风险回归题建议转人工：{case_id}")

    pii = _pii_hits(package)
    if pii:
        blockers.append(f"知识包存在疑似敏感信息：{pii}")

    metrics["warnings"] = warnings
    return blockers, metrics


def _bootstrap_owner(client) -> dict[str, Any]:
    owner_payload = {
        "tenant_slug": "h2w-kb1-local-rehearsal",
        "tenant_name": "H2W-KB1 本地知识包演练空间",
        "owner_name": "本地负责人",
        "email": "h2w-kb1-owner@wanfa.local",
        "password": "H2WKB1Owner123!",
    }
    setup_before = _json_response(
        client.get("/api/auth/local-setup/status"),
        expected_status=200,
        label="local setup status before KB1 owner",
    )
    owner_created = _json_response(
        client.post("/api/auth/local-setup/owner", json=owner_payload),
        expected_status=201,
        label="create KB1 first owner",
    )
    login = _json_response(
        client.post(
            "/api/auth/login",
            json={
                "tenant_slug": owner_payload["tenant_slug"],
                "email": owner_payload["email"],
                "password": owner_payload["password"],
            },
        ),
        expected_status=200,
        label="KB1 owner login",
    )
    setup_after = _json_response(
        client.get("/api/auth/local-setup/status"),
        expected_status=200,
        label="local setup status after KB1 owner",
    )
    return {
        "tenant_id": int(login["user"]["tenant"]["id"]),
        "tenant_slug": login["user"]["tenant"]["slug"],
        "owner_user_id": int(login["user"]["id"]),
        "owner_email_hash": _sha256_text(owner_payload["email"])[:24],
        "token": login["access_token"],
        "checks": {
            "can_create_first_owner_before": setup_before["can_create_first_owner"] is True,
            "owner_role_created": owner_created["user"]["roles"] == ["owner"],
            "login_used_password_endpoint": login["token_type"] == "bearer",
            "first_owner_creation_locked_after": setup_after["first_owner_creation_locked"] is True,
            "dev_bootstrap_disabled": setup_after["dev_bootstrap_enabled"] is False,
            "external_write_disabled": setup_after["external_write_enabled"] is False,
            "trusted_inbound_worker_disabled": setup_after["trusted_inbound_worker_enabled"] is False,
        },
    }


def _run_backend_rehearsal(package: dict[str, Any]) -> dict[str, Any]:
    with _safe_kb1_env(), _safe_local_embedding_env(), _local_test_client() as client:
        owner = _bootstrap_owner(client)
        headers = _auth_headers(owner["token"])
        tenant_id = owner["tenant_id"]

        preview = _json_response(
            client.post(
                f"/api/tenants/{tenant_id}/knowledge-update-package/previews",
                headers=headers,
                json={"package": package},
            ),
            expected_status=200,
            label="preview KB1 customer-specific knowledge package",
        )
        imported = _json_response(
            client.post(
                f"/api/tenants/{tenant_id}/knowledge-update-package-imports",
                headers=headers,
                json={"package": package},
            ),
            expected_status=201,
            label="import KB1 customer-specific knowledge package",
        )
        documents = _json_response(
            client.get(f"/api/tenants/{tenant_id}/knowledge-documents?status=active&page_size=100", headers=headers),
            expected_status=200,
            label="list KB1 imported documents",
        )
        business_objects = _json_response(
            client.get(f"/api/tenants/{tenant_id}/business-objects?status=active&page_size=100", headers=headers),
            expected_status=200,
            label="list KB1 imported business objects",
        )
        evaluation_sets = _json_response(
            client.get(
                f"/api/tenants/{tenant_id}/knowledge-evaluation-sets?status=active&page_size=100",
                headers=headers,
            ),
            expected_status=200,
            label="list KB1 imported evaluation sets",
        )
        chunk_count = 0
        for document in documents["items"]:
            chunks = _json_response(
                client.get(f"/api/knowledge-documents/{document['id']}/chunks", headers=headers),
                expected_status=200,
                label=f"list KB1 document chunks {document['id']}",
            )
            chunk_count += len(chunks)

        rollback = _json_response(
            client.post(
                f"/api/knowledge-update-package-imports/{imported['import_batch_id']}/rollback",
                headers=headers,
                json={"reason": "H2W-KB1 rehearsal rollback"},
            ),
            expected_status=201,
            label="rollback KB1 customer-specific knowledge package",
        )
        documents_after = _json_response(
            client.get(f"/api/tenants/{tenant_id}/knowledge-documents?status=active&page_size=100", headers=headers),
            expected_status=200,
            label="list KB1 documents after rollback",
        )
        evaluation_sets_after = _json_response(
            client.get(
                f"/api/tenants/{tenant_id}/knowledge-evaluation-sets?status=active&page_size=100",
                headers=headers,
            ),
            expected_status=200,
            label="list KB1 evaluation sets after rollback",
        )

    owner_public = {key: value for key, value in owner.items() if key != "token"}
    return {
        "owner": owner_public,
        "preview": {
            "can_apply": preview["can_apply"],
            "operation_counts": preview["operation_counts"],
            "dry_run": preview["dry_run"],
            "import_batch_id": preview["import_batch_id"],
        },
        "import": {
            "can_apply": imported["can_apply"],
            "operation_counts": imported["operation_counts"],
            "import_batch_id": imported["import_batch_id"],
            "safety": imported["safety"],
            "created_counts": {key: len(value) for key, value in imported["created"].items()},
        },
        "active_after_import": {
            "business_object_count": business_objects["total"],
            "knowledge_document_count": documents["total"],
            "evaluation_set_count": evaluation_sets["total"],
            "chunk_count": chunk_count,
        },
        "rollback": {
            "rollback_status": rollback["rollback_status"],
            "archived_counts": rollback["archived_counts"],
            "active_document_count_after_rollback": documents_after["total"],
            "active_evaluation_set_count_after_rollback": evaluation_sets_after["total"],
        },
    }


def _summarize_pack5(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"present": False, "status": "missing", "ready": False}
    payload = _read_json(path)
    return {
        "present": True,
        "status": payload.get("status"),
        "ready": bool((payload.get("readiness") or {}).get("ready_for_customer_local_pilot_handoff_candidate")),
    }


def _write_doc(path: Path, result: dict[str, Any]) -> None:
    readiness = result["readiness"]
    backend = result.get("backend_rehearsal") or {}
    lines = [
        "# H2W-KB1 客户专属知识包导入与签收 rehearsal",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 可进入客户专属知识包本地试点 rehearsal：`{str(readiness['ready_for_customer_specific_knowledge_rehearsal']).lower()}`",
        f"- 可作为客户资料包导入预检候选：`{str(readiness['ready_for_customer_specific_knowledge_import_candidate']).lower()}`",
        f"- 客户专属知识库正式就绪：`{str(readiness['customer_specific_knowledge_ready']).lower()}`",
        f"- 正式客户签收：`{str(readiness['formal_customer_signoff_ready']).lower()}`",
        "",
        "## 本阶段实际验证",
        "",
        "- 使用内部脱敏客户专属知识包，不使用真实客户原始聊天、订单、手机号、邮箱或平台昵称。",
        "- 通过后端真实接口完成首任负责人创建、登录、知识更新包预检、导入、查询、回滚。",
        "- 资料包同时包含业务对象、标准问答、流程政策、禁用承诺、转人工规则和回归题。",
        "- 签收只生成 rehearsal 边界，不生成电子签章、合同签收或客户确认完成态。",
        "",
        "## 资料包结构",
        "",
        f"- 业务对象：{result['package_metrics']['business_object_count']}",
        f"- 对象知识卡：{result['package_metrics']['object_knowledge_card_count']}",
        f"- 来源文档：{result['package_metrics']['knowledge_document_count']}",
        f"- 回归题：{result['package_metrics']['regression_case_count']}",
        f"- 知识类型：{', '.join(result['package_metrics']['knowledge_types'])}",
        "",
        "## 后端 rehearsal 证据",
        "",
    ]
    if backend:
        lines.extend(
            [
                f"- 预检 can_apply：`{str(backend['preview']['can_apply']).lower()}`",
                f"- 导入 can_apply：`{str(backend['import']['can_apply']).lower()}`",
                f"- 导入批次：`{backend['import']['import_batch_id']}`",
                f"- 导入后业务对象：{backend['active_after_import']['business_object_count']}",
                f"- 导入后文档：{backend['active_after_import']['knowledge_document_count']}",
                f"- 导入后回归题集：{backend['active_after_import']['evaluation_set_count']}",
                f"- 文档 chunk：{backend['active_after_import']['chunk_count']}",
                f"- 回滚状态：`{backend['rollback']['rollback_status']}`",
                f"- 回滚后 active 文档：{backend['rollback']['active_document_count_after_rollback']}",
                f"- 回滚后 active 回归题集：{backend['rollback']['active_evaluation_set_count_after_rollback']}",
            ]
        )
    else:
        lines.append("- 后端 rehearsal 未运行。")
    lines.extend(
        [
            "",
            "## 停止门禁",
            "",
            "- 资料包未覆盖业务对象、标准问答、流程政策、禁用承诺、转人工规则时，不能进入客户试点。",
            "- 资料包不能通过后端预检、导入、查询、回滚时，不能写成可交付。",
            "- 回归题少于 8 条、没有引用来源或高风险题不转人工时，不能进入启用前复测。",
            "- 出现手机号、邮箱、身份证、原始订单号等疑似敏感信息时，立即阻断。",
            "- `customer_confirmed=false` 前，不能写成客户专属知识库已正式签收。",
            "",
            "## 固定边界",
            "",
            "- `real_customer_data_used=false`",
            "- `provider_call_performed=false`",
            "- `real_platform_send_performed=false`",
            "- `formal_customer_signoff_performed=false`",
            "- `customer_specific_knowledge_ready=false`",
            "",
            "## 下一步",
            "",
            "- 把该资料包流程映射到前端“知识维护总流程”的客户可操作路径。",
            "- 准备真实客户资料收集模板，但仍需脱敏和客户确认后才能进入正式知识库签收。",
            "- 继续推进非技术客户启动器/安装器和售后运维交接 rehearsal。",
            "",
            "## 阻断项",
            "",
        ]
    )
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(["", "## 警告", ""])
    lines.extend([f"- {item}" for item in result["warnings"]] or ["- 无"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_kb1_customer_specific_knowledge_package_rehearsal(
    *,
    package_path: Path = DEFAULT_PACKAGE_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    pack5_summary_path: Path = PACK5_SUMMARY,
    run_backend: bool = True,
) -> dict[str, Any]:
    _ensure_default_package(package_path)
    package = _read_json(package_path)
    package_blockers, metrics = validate_customer_specific_package(package)
    warnings = list(metrics.pop("warnings", []))
    blockers = list(package_blockers)
    pack5 = _summarize_pack5(pack5_summary_path)
    if pack5["present"] and not pack5["ready"]:
        warnings.append("PACK5 存在但尚未 ready；KB1 可独立 rehearsal，但不能合并为客户试点交付包。")

    backend_rehearsal: dict[str, Any] | None = None
    if run_backend and not blockers:
        backend_rehearsal = _run_backend_rehearsal(package)
        backend_checks = {
            "owner_login_ready": all(backend_rehearsal["owner"]["checks"].values()),
            "preview_can_apply": backend_rehearsal["preview"]["can_apply"] is True,
            "preview_is_dry_run": backend_rehearsal["preview"]["dry_run"] is True,
            "import_can_apply": backend_rehearsal["import"]["can_apply"] is True,
            "import_batch_created": backend_rehearsal["import"]["import_batch_id"] is not None,
            "provider_call_false": backend_rehearsal["import"]["safety"].get("provider_call_performed") is False,
            "external_write_false": backend_rehearsal["import"]["safety"].get("external_write_performed") is False,
            "documents_imported": backend_rehearsal["active_after_import"]["knowledge_document_count"]
            >= metrics["knowledge_document_count"],
            "business_objects_imported": backend_rehearsal["active_after_import"]["business_object_count"]
            >= metrics["business_object_count"],
            "evaluation_sets_imported": backend_rehearsal["active_after_import"]["evaluation_set_count"] >= 1,
            "chunks_created": backend_rehearsal["active_after_import"]["chunk_count"]
            >= metrics["knowledge_document_count"],
            "rollback_completed": backend_rehearsal["rollback"]["rollback_status"] == "rolled_back",
            "rollback_removed_active_documents": backend_rehearsal["rollback"]["active_document_count_after_rollback"] == 0,
            "rollback_removed_active_evaluation_sets": backend_rehearsal["rollback"][
                "active_evaluation_set_count_after_rollback"
            ]
            == 0,
        }
        blockers.extend([f"后端 rehearsal 未通过：{name}" for name, passed in backend_checks.items() if not passed])
    elif not run_backend:
        warnings.append("run_backend=false，仅执行资料包结构门禁。")

    status = "ready_for_customer_specific_knowledge_package_rehearsal" if not blockers else "blocked"
    readiness = {
        "ready_for_customer_specific_knowledge_rehearsal": not blockers,
        "ready_for_customer_specific_knowledge_import_candidate": not blockers and backend_rehearsal is not None,
        "customer_specific_knowledge_ready": False,
        "formal_customer_signoff_ready": False,
        "ready_to_merge_into_customer_pilot_handoff": not blockers and pack5["ready"],
    }
    result = {
        "schema_version": "p3-06u-26h2w-kb1.customer_specific_knowledge_package_rehearsal.v1",
        "phase": PHASE,
        "status": status,
        "readiness": readiness,
        "blockers": blockers,
        "warnings": warnings,
        "package": {
            "path": _display_path(package_path),
            "package_id": package.get("package_id"),
            "package_name": package.get("package_name"),
            "sha256": hashlib.sha256(package_path.read_bytes()).hexdigest(),
        },
        "package_metrics": metrics,
        "pack5_upstream": pack5,
        "backend_rehearsal": backend_rehearsal,
        "signoff_boundary": {
            "customer_confirmed": False,
            "customer_reviewer_required": True,
            "local_record_only": True,
            "electronic_signature_performed": False,
            "formal_contract_signoff_performed": False,
        },
        "boundaries": {
            "real_customer_data_used": False,
            "provider_call_performed": False,
            "real_platform_send_performed": False,
            "external_platform_write_performed": False,
            "formal_customer_signoff_performed": False,
            "customer_specific_knowledge_ready": False,
        },
        "next_actions": [
            "将 KB1 资料包流程映射到前端知识维护总流程。",
            "补非技术客户启动器/安装器 rehearsal。",
            "后续取得真实客户资料时，先脱敏、预检、回归题生成，再进入客户确认。",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "summary.json", result)
    _write_doc(doc_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run H2W-KB1 customer-specific knowledge package rehearsal.")
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--skip-backend", action="store_true")
    args = parser.parse_args()
    result = run_h2w_kb1_customer_specific_knowledge_package_rehearsal(
        package_path=args.package,
        output_dir=args.output_dir,
        run_backend=not args.skip_backend,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
