from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "P3-06U-18_YUNDUO_AI_DEEP_REFERENCE_ENGINEERING_OPTIMIZATION.md"


REQUIRED_PHRASES = [
    "475 张",
    "48 张",
    "33 张",
    "视频不能证明",
    "多平台账号与店铺矩阵",
    "商品学习",
    "业务对象知识库",
    "自动回复策略状态机",
    "统一入站消息信封 v2",
    "渠道账号与店铺实体化",
    "知识修复闭环",
    "RPA 研究线只作为内部研究和 draft-only 副驾驶",
    "不把个人私信、网页后台模拟点击、私有协议或自动发送写成正式交付能力",
    "P3-06U-19 业务对象知识库第一片",
]

REQUIRED_TABLE_TERMS = [
    "channel_accounts",
    "store_accounts",
    "business_objects",
    "object_knowledge_cards",
    "reply_decisions",
    "reply_policy_rules",
]


def main() -> None:
    if not DOC.exists():
        raise SystemExit(f"missing doc: {DOC}")

    text = DOC.read_text(encoding="utf-8")

    missing = [phrase for phrase in REQUIRED_PHRASES if phrase not in text]
    if missing:
        raise SystemExit("missing required phrases:\n" + "\n".join(missing))

    missing_terms = [term for term in REQUIRED_TABLE_TERMS if term not in text]
    if missing_terms:
        raise SystemExit("missing engineering terms:\n" + "\n".join(missing_terms))

    sections = [line for line in text.splitlines() if line.startswith("## ")]
    if len(sections) < 10:
        raise SystemExit(f"too few level-2 sections: {len(sections)}")

    if "## 11. 下一步建议" not in text:
        raise SystemExit("missing next step section")

    print("P3-06U-18 engineering optimization doc check passed.")


if __name__ == "__main__":
    main()
