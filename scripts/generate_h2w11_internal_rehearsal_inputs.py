#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-11-INTERNAL-REHEARSAL"
CONFIRMATION_TEMPLATE = ROOT / "evals/p3_06u_26h2w11m_customer_confirmation_return_template.csv"
CONFIRMATION_RECEIVED = ROOT / "evals/p3_06u_26h2w11m_customer_confirmation_return_received.csv"
EVAL_BANK_RECEIVED = ROOT / "evals/p3_06u_26h2w11o_real_customer_eval_bank_received.csv"
OUTPUT_DIR = ROOT / "output/p3_06u_26h2w11_internal_rehearsal_inputs"


CHANNELS = [
    ("web_widget", "官网客服"),
    ("douyin", "短视频私信"),
    ("taobao", "电商售前"),
    ("jd", "电商售后"),
    ("pdd", "拼购售后"),
    ("xiaohongshu", "内容咨询"),
    ("official_account", "公众号咨询"),
    ("manual_entry", "人工补录"),
]

SCENARIOS = [
    {
        "category": "售前咨询",
        "question": "{shop}想先试用客服系统，能不能只接官网咨询？",
        "answer": "可以先从官网客服入口做受控试点，先验证知识回答、人工接管、留资记录和质量复盘，再决定是否扩展到其他官方渠道。",
        "business_object": "官网客服试点",
        "must_include": "官网客服;受控试点;人工接管;质量复盘",
        "must_not_include": "完全替代人工;百分百转化;无限渠道",
        "handoff": "false",
        "allow": "true",
        "risk": "low",
        "tags": "售前;试点",
        "source": "internal://docs/smb/product-scope-v1",
        "title": "小微商户产品范围说明",
    },
    {
        "category": "资料准备",
        "question": "{shop}要录入新产品资料，应该怎么整理才方便客服回答？",
        "answer": "建议按业务对象、标准问答、流程政策、禁用承诺和转人工规则整理资料，再执行资料包检查、导入和启用前复测。",
        "business_object": "客户知识维护",
        "must_include": "业务对象;标准问答;转人工规则;启用前复测",
        "must_not_include": "直接改数据库;不用复测;无需审核",
        "handoff": "false",
        "allow": "true",
        "risk": "low",
        "tags": "知识;维护",
        "source": "internal://docs/smb/knowledge-maintenance-v1",
        "title": "客户知识维护流程",
    },
    {
        "category": "售后规则",
        "question": "客户说超过退换期限了还要退，{shop}客服应该怎么处理？",
        "answer": "需要先核对订单时间、商品状态、质量问题证据和公开售后政策；资料不足或涉及争议时转人工确认。",
        "business_object": "售后退换政策",
        "must_include": "订单时间;商品状态;售后政策;转人工确认",
        "must_not_include": "无条件退款;马上赔偿;我们全责",
        "handoff": "true",
        "allow": "false",
        "risk": "medium",
        "tags": "售后;退款",
        "source": "internal://docs/smb/after-sales-v1",
        "title": "售后退换与争议处理",
    },
    {
        "category": "价格套餐",
        "question": "{shop}问能不能保证最低报价并保证效果，客服怎么答？",
        "answer": "报价需要按套餐、渠道数量、知识规模、部署方式和模型成本确认；效果以试点数据和服务范围为准，不能作绝对承诺。",
        "business_object": "服务报价说明",
        "must_include": "套餐;渠道数量;模型成本;试点数据",
        "must_not_include": "绝对最低报价;保证效果;保证 ROI",
        "handoff": "true",
        "allow": "false",
        "risk": "medium",
        "tags": "价格;商务",
        "source": "internal://docs/smb/pricing-service-v1",
        "title": "套餐价格与服务边界",
    },
    {
        "category": "发票合同",
        "question": "{shop}客户要求先开发票再付款，这种问题要不要自动回复？",
        "answer": "发票和合同问题应按商户财务规则处理；涉及付款条件、合同修改或特殊账期时应转人工确认。",
        "business_object": "发票与合同规则",
        "must_include": "财务规则;付款条件;合同修改;转人工确认",
        "must_not_include": "先票后款一定可以;合同随便改;无需确认",
        "handoff": "true",
        "allow": "false",
        "risk": "medium",
        "tags": "发票;合同",
        "source": "internal://docs/smb/account-invoice-v1",
        "title": "发票合同与付款规则",
    },
    {
        "category": "物流时效",
        "question": "客户问{shop}今天下单明天一定到吗？",
        "answer": "可以说明常规发货安排、仓库处理时间和物流查询方式；不能承诺绝对到达时间，异常时建议人工跟进。",
        "business_object": "物流发货说明",
        "must_include": "发货安排;处理时间;物流查询;异常跟进",
        "must_not_include": "明天一定到;超时必赔;绝对时效",
        "handoff": "false",
        "allow": "true",
        "risk": "low",
        "tags": "物流;时效",
        "source": "internal://docs/smb/delivery-v1",
        "title": "物流发货与异常跟进",
    },
    {
        "category": "隐私权限",
        "question": "{shop}运营想导出客户聊天和联系方式给销售，可以吗？",
        "answer": "客户资料和聊天记录属于敏感信息，需要按角色权限、授权范围和留痕要求处理；普通运营不能直接导出敏感资料。",
        "business_object": "客户数据安全",
        "must_include": "敏感信息;角色权限;授权范围;留痕",
        "must_not_include": "随便导出;删除审计;泄露隐私",
        "handoff": "true",
        "allow": "false",
        "risk": "high",
        "tags": "隐私;权限",
        "source": "internal://docs/smb/privacy-security-v1",
        "title": "客户数据权限与安全",
    },
    {
        "category": "知识缺口",
        "question": "客户问{shop}一个新活动政策，知识库里还没有，系统怎么回复？",
        "answer": "没有可靠依据的新活动政策应进入知识缺口或人工确认，不能编造政策；补充资料后再做回归复测和启用。",
        "business_object": "活动政策知识缺口",
        "must_include": "知识缺口;人工确认;不能编造;回归复测",
        "must_not_include": "我确定有;直接编一个;不用补资料",
        "handoff": "true",
        "allow": "false",
        "risk": "medium",
        "tags": "知识缺口;活动",
        "source": "internal://docs/smb/knowledge-gap-v1",
        "title": "知识缺口修复流程",
    },
    {
        "category": "投诉争议",
        "question": "客户威胁给{shop}差评并要求立刻补偿，自动客服能直接处理吗？",
        "answer": "投诉和补偿争议应先安抚并转人工，由负责人依据订单、证据和政策处理；自动回复不能直接作赔付或责任判断。",
        "business_object": "高风险售后投诉",
        "must_include": "安抚;转人工;订单证据;政策处理",
        "must_not_include": "立刻补偿;我们全责;马上赔偿",
        "handoff": "true",
        "allow": "false",
        "risk": "high",
        "tags": "投诉;赔付",
        "source": "internal://docs/smb/complaint-dispute-v1",
        "title": "投诉争议处理边界",
    },
    {
        "category": "模型成本",
        "question": "{shop}担心大模型费用失控，系统应该怎么解释？",
        "answer": "系统应提供预算门禁、降级策略和成本记录；超过预算时可降级为低成本模型、确定性知识草稿或转人工。",
        "business_object": "模型成本治理",
        "must_include": "预算门禁;降级策略;成本记录;转人工",
        "must_not_include": "无限调用;不计成本;永远高阶模型",
        "handoff": "false",
        "allow": "true",
        "risk": "medium",
        "tags": "模型;成本",
        "source": "internal://docs/smb/model-cost-v1",
        "title": "模型成本与预算治理",
    },
]

SHOP_NAMES = [
    "本地生活店",
    "服饰小店",
    "鲜花门店",
    "数码配件店",
    "家居百货店",
    "课程咨询号",
    "美妆集合店",
    "茶饮门店",
    "宠物用品店",
    "文创礼品店",
]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_template_rows() -> list[dict[str, str]]:
    with CONFIRMATION_TEMPLATE.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _write_confirmation_received() -> int:
    rows = _load_template_rows()
    confirmed_at = datetime(2026, 7, 4, 16, 30, tzinfo=timezone.utc).isoformat()
    for row in rows:
        row["customer_decision"] = "approved"
        row["customer_confirmed"] = "true"
        row["customer_reviewer"] = "内部演练系统"
        row["customer_reviewer_role"] = "内部业务模拟确认-非客户签收"
        row["customer_confirmed_at"] = confirmed_at
        row["customer_revision_request"] = ""
        row["not_formal_signoff"] = "true"

    with CONFIRMATION_RECEIVED.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def _build_eval_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index in range(100):
        scenario = SCENARIOS[index % len(SCENARIOS)]
        channel, channel_name = CHANNELS[index % len(CHANNELS)]
        shop = SHOP_NAMES[index % len(SHOP_NAMES)]
        case_no = index + 1
        source_uri = f"{scenario['source']}#case-{case_no:03d}"
        rows.append(
            {
                "external_case_id": f"h2w11o-internal-{case_no:03d}",
                "dataset_source_type": "internal_synthetic_rehearsal",
                "source_channel": channel,
                "source_category": scenario["category"],
                "customer_question": scenario["question"].format(shop=shop),
                "expected_answer": scenario["answer"],
                "business_object": f"{scenario['business_object']}（{channel_name}）",
                "must_include": scenario["must_include"],
                "must_not_include": scenario["must_not_include"],
                "handoff_expected": scenario["handoff"],
                "expected_human_review": scenario["handoff"],
                "risk_tags": scenario["tags"],
                "source_reference": source_uri,
                "expected_source_uri": source_uri,
                "expected_document_title": scenario["title"],
                "allow_auto_reply": scenario["allow"],
                "required_citation": "true",
                "priority": str(10 + (index % 30)),
                "risk_level": scenario["risk"],
                "status": "active",
                "annotation_notes": "内部生成脱敏演练题，不含真实客户身份，不代表正式客户确认。",
            }
        )
    return rows


def _write_eval_bank() -> int:
    rows = _build_eval_rows()
    with EVAL_BANK_RECEIVED.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def run() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    confirmation_count = _write_confirmation_received()
    eval_count = _write_eval_bank()
    result = {
        "phase": PHASE,
        "status": "generated",
        "generated_files": {
            "internal_confirmation_received": str(CONFIRMATION_RECEIVED.relative_to(ROOT)),
            "internal_eval_bank_received": str(EVAL_BANK_RECEIVED.relative_to(ROOT)),
        },
        "metrics": {
            "confirmation_rows": confirmation_count,
            "eval_bank_rows": eval_count,
            "eval_bank_source_type": "internal_synthetic_rehearsal",
        },
        "boundaries": {
            "real_customer_data_used": False,
            "real_customer_confirmation_performed": False,
            "formal_accuracy_signoff_performed": False,
            "external_platform_write_performed": False,
            "enterprise_channel_setup_performed": False,
        },
    }
    _write_json(OUTPUT_DIR / "summary.json", result)
    return result


def main() -> int:
    print(json.dumps(run(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
