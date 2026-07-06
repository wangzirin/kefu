#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evaluate_bailian_chat_quality import _load_dotenv_file, run_bailian_chat_quality_evaluation


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-MODEL1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_model1_bailian_cost_sample"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_MODEL1_BAILIAN_COST_SAMPLE.md"
H2W7B_STATIC = ROOT / "docs/P3-06U-26H2W7B_MODEL_COST_BUDGET_GATE_FIRST_SLICE.md"
H2W11O_SUMMARY = ROOT / "output/p3_06u_26h2w11o_real_customer_eval_bank_import/summary.json"


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    metrics = result["metrics"]
    lines = [
        "# H2W-MODEL1 百炼/千问真实小样本成本验证",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 显式外部调用授权：`{str(result['allow_external_call']).lower()}`",
        f"- 真实 provider 调用：`{str(metrics['provider_call_performed']).lower()}`",
        f"- 计划样本数：`{metrics['planned_cases']}`",
        f"- 成功调用数：`{metrics['succeeded']}`",
        f"- 失败调用数：`{metrics['failed']}`",
        f"- tokens/字符量合计：`{metrics['total_tokens_or_chars']}`",
        "",
        "## 停止门禁",
        "",
        "- 默认不调用付费模型；必须显式传入 `--allow-external-call` 才能跑 5-10 条小样本。",
        "- 显式 provider 失败不能静默 fallback，失败必须进入成本与质量证据。",
        "- 没有持久成本记录、价格来源不可追溯、失败伪装成功时，不进入模型封版候选。",
        "- 内部确定性回复不能计入真实模型成本。",
        "",
        "## 阻断项",
        "",
    ]
    lines.extend([f"- {item}" for item in result["blockers"]] or ["- 无"])
    lines.extend(["", "## 警告", ""])
    lines.extend([f"- {item}" for item in result["warnings"]] or ["- 无"])
    lines.extend(
        [
            "",
            "## 输出",
            "",
            f"- `{result['evidence']['summary_json']['path']}`",
            "",
            "## 边界",
            "",
            "- `provider_call_performed` 以 summary 为准",
            "- `real_platform_send_performed=false`",
            "- `formal_customer_signoff_performed=false`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_model1_bailian_cost_sample(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    allow_external_call: bool = False,
    limit: int = 5,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    blockers: list[str] = []
    warnings: list[str] = []

    _load_dotenv_file(ROOT / ".env")

    if limit < 1 or limit > 10:
        blockers.append("MODEL1 小样本限制为 1-10 条")

    h2w7b_static_ready = H2W7B_STATIC.exists() and all(
        marker in H2W7B_STATIC.read_text(encoding="utf-8")
        for marker in ["预算门禁", "显式 provider 不静默 fallback", "真实外发继续关闭"]
    )
    if not h2w7b_static_ready:
        blockers.append("缺少 H2W-7B 模型成本预算静态证据")

    internal_100q_ready = False
    if H2W11O_SUMMARY.exists():
        h2w11o = _read_json(H2W11O_SUMMARY)
        internal_100q_ready = (
            h2w11o.get("status") == "passed_internal_rehearsal"
            and h2w11o.get("metrics", {}).get("row_count") == 100
        )
    if not internal_100q_ready:
        warnings.append("内部 100 题证据未 ready；MODEL1 仍可只做 guarded planning")

    eval_result = run_bailian_chat_quality_evaluation(
        allow_external_call=allow_external_call,
        limit=limit,
        include_previews=False,
    )
    provider_call_performed = bool(eval_result.get("provider_call_performed"))
    eval_summary = eval_result.get("summary", {})

    if allow_external_call and not provider_call_performed:
        blockers.append(eval_result.get("error_message") or "已授权外部调用，但 provider 未实际调用")
    if provider_call_performed and eval_summary.get("failed", 0) > 0:
        blockers.append("百炼小样本存在失败调用，不能写成模型封版候选")

    ready_candidate = provider_call_performed and not blockers
    if blockers:
        status = "blocked"
    elif ready_candidate:
        status = "passed_real_small_sample_cost_rehearsal"
    else:
        status = "guarded_external_call_not_allowed"

    result = {
        "phase": PHASE,
        "status": status,
        "allow_external_call": allow_external_call,
        "readiness": {
            "h2w7b_static_budget_gate_ready": h2w7b_static_ready,
            "internal_100q_bank_ready": internal_100q_ready,
            "ready_for_model_cost_candidate": ready_candidate,
        },
        "metrics": {
            "provider_call_performed": provider_call_performed,
            "planned_cases": eval_summary.get("planned_cases", 0),
            "attempted_calls": eval_summary.get("attempted_calls", 0),
            "succeeded": eval_summary.get("succeeded", 0),
            "failed": eval_summary.get("failed", 0),
            "average_latency_ms": eval_summary.get("average_latency_ms", 0),
            "total_tokens_or_chars": eval_summary.get("total_tokens_or_chars", 0),
        },
        "provider_result": {
            "status": eval_result.get("status"),
            "provider": eval_result.get("provider"),
            "raw_text_logged": eval_result.get("raw_text_logged"),
            "case_catalog": eval_result.get("case_catalog"),
            "error_message": eval_result.get("error_message"),
        },
        "blockers": blockers,
        "warnings": warnings,
        "evidence": {
            "summary_json": {"path": _display_path(summary_path)},
            "h2w7b_static_doc": {"path": _display_path(H2W7B_STATIC), "present": H2W7B_STATIC.exists()},
            "h2w11o_summary": {"path": _display_path(H2W11O_SUMMARY), "present": H2W11O_SUMMARY.exists()},
        },
        "boundaries": {
            "real_platform_send_performed": False,
            "formal_customer_signoff_performed": False,
            "deterministic_reply_counted_as_real_model_cost": False,
            "silent_fallback_on_explicit_provider_failure": False,
        },
    }
    _write_json(summary_path, result)
    _write_markdown(DOC_PATH, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run guarded Bailian/Qwen model cost sample.")
    parser.add_argument("--allow-external-call", action="store_true")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    result = run_h2w_model1_bailian_cost_sample(
        allow_external_call=args.allow_external_call,
        limit=args.limit,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
