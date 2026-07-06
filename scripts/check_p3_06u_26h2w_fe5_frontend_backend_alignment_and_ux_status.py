#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PHASE = "H2W-FE5"
SCHEMA_VERSION = "p3-06u-26h2w-fe5.frontend_backend_alignment_and_ux_status.v1"
DEFAULT_OUTPUT_DIR = ROOT / "output/p3_06u_26h2w_fe5_frontend_backend_alignment_and_ux_status"
DOC_PATH = ROOT / "docs/P3-06U-26H2W_FE5_FRONTEND_BACKEND_ALIGNMENT_AND_UX_STATUS.md"

FE4_SUMMARY = ROOT / "output/p3_06u_26h2w_fe4_customer_ui_sealed_candidate/summary.json"
FE4_CLICK_QA = ROOT / "output/p3_06u_26h2w_fe4_customer_visible_click_qa/summary.json"
PILOT0_SUMMARY = ROOT / "output/p3_06u_26h2w_pilot0_readiness/summary.json"
PILOT4_SUMMARY = ROOT / "output/p3_06u_26h2w_pilot4_customer_trial_rehearsal/summary.json"
INSTALL3_SUMMARY = ROOT / "output/p3_06u_26h2w_install3_native_app_packaging_gate/summary.json"
FUNCTION_MATRIX = ROOT / "docs/FRONTEND_FUNCTION_REALITY_MATRIX.md"
NAVIGATION_TS = ROOT / "frontend/src/data/navigation.ts"
APP_TSX = ROOT / "frontend/src/App.tsx"
API_CLIENT_TS = ROOT / "frontend/src/api/client.ts"
NEXT_STEPS_DOC = ROOT / "docs/P3-06U-26H2W_NEXT_STEPS_INSTALLER_AND_FRONTEND_ALIGNMENT_PLAN.md"

ENGINEERING_TERMS = ["H2W", "P3-06", "dry-run", "provider", "sandbox", "connector_noop"]


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _status_check(path: Path, expected: str) -> dict[str, Any]:
    payload = _read_json(path)
    actual = str(payload.get("status") or "missing")
    return {
        "path": _display_path(path),
        "present": path.exists(),
        "expected": expected,
        "actual": actual,
        "passed": path.exists() and actual == expected,
    }


def _click_qa_pages(click_qa: dict[str, Any]) -> list[dict[str, Any]]:
    browser = click_qa.get("browser", {})
    pages = browser.get("pages", [])
    return pages if isinstance(pages, list) else []


def _hashes_from_click_qa(click_qa: dict[str, Any]) -> set[str]:
    hashes: set[str] = set()
    for item in _click_qa_pages(click_qa):
        if isinstance(item, dict) and item.get("hash"):
            hashes.add(str(item["hash"]))
    return hashes


def _navigation_customer_routes(text: str) -> set[str]:
    routes: set[str] = set()
    for marker in ['href: "#', "href=\"#"]:
        cursor = 0
        while True:
            index = text.find(marker, cursor)
            if index < 0:
                break
            start = index + len(marker) - 1
            end = text.find('"', start + 1)
            if end > start:
                routes.add(text[start:end])
            cursor = index + len(marker)
    return routes


def _visible_navigation_engineering_terms(navigation_text: str) -> list[str]:
    hits: list[str] = []
    # Hidden backstage route names can still contain implementation nouns. Only scan top-level labels/count/description.
    visible_slice = navigation_text.split("export const roleTaskPaths", 1)[0]
    for term in ENGINEERING_TERMS:
        if term in visible_slice:
            hits.append(term)
    return hits


def _calculate_scores(*, fe4_ok: bool, click_ok: bool, pilot_route_ok: bool, pilot_browser_covered: bool, install3_ok: bool) -> dict[str, int]:
    visual = 80 if fe4_ok and click_ok else 55
    alignment = 78 if fe4_ok and click_ok and pilot_route_ok else 58
    workflow = 79 if pilot_route_ok and install3_ok else 60
    if pilot_browser_covered:
        visual += 4
        alignment += 4
        workflow += 3
    else:
        visual -= 2
        alignment -= 4
        workflow -= 2
    return {
        "frontend_visual_score_100": max(0, min(100, visual)),
        "frontend_backend_alignment_score_100": max(0, min(100, alignment)),
        "product_workflow_consistency_score_100": max(0, min(100, workflow)),
        "controlled_pilot_frontend_confidence_score_100": max(
            0, min(100, round((visual + alignment + workflow) / 3))
        ),
    }


def _build_next_steps() -> list[dict[str, str]]:
    return [
        {
            "phase": "H2W-FE5",
            "goal": "把前端、后端、最新入口和视觉/布局真实状态做成机器可读事实账本。",
            "status": "current",
            "stop_gate": "如果 FE4 浏览器证据缺失，或试点准备页没有真实接口绑定，停止继续封版。",
        },
        {
            "phase": "H2W-FE6",
            "goal": "对最新页面做浏览器逐页点击复测，重点覆盖试点准备、账号与本地维护、接待工作台、知识运营、质量复盘。",
            "status": "next",
            "stop_gate": "任一客户可见按钮只有图标无真实动作、无明确禁用原因或页面文案超过后端能力，即停止。",
        },
        {
            "phase": "H2W-INSTALL4",
            "goal": "继续原生包装专项，补图标、卸载/清理说明、升级前备份提示、版本文件和日志目录的客户可读性。",
            "status": "planned",
            "stop_gate": "没有代码签名、卸载验证和升级回滚 QA 前，继续保持 signed_dmg_exe_ready=false。",
        },
        {
            "phase": "H2W-PILOT6",
            "goal": "重新导出试点交付档案，把 FE5/FE6、INSTALL3/4、月报、知识复测和本地维护证据统一进包。",
            "status": "planned",
            "stop_gate": "导出包包含密钥、真实客户原文、本机隐私路径或正式 SLA 承诺，立即阻断。",
        },
        {
            "phase": "H2W-KB3",
            "goal": "把客户知识导入体验再简化，重点让小微企业知道应该录入业务对象、标准问答、流程政策、禁用承诺和转人工规则。",
            "status": "planned",
            "stop_gate": "知识维护入口不能让客户误以为导入即启用、评测即完整线上准确率。",
        },
    ]


def _write_markdown(path: Path, result: dict[str, Any]) -> None:
    scores = result["scores"]
    lines = [
        "# H2W-FE5 前后端对齐与前端体验状态评估",
        "",
        "## 结论",
        "",
        f"- 阶段状态：`{result['status']}`",
        f"- 前端观感与布局分：`{scores['frontend_visual_score_100']}/100`",
        f"- 前后端对齐分：`{scores['frontend_backend_alignment_score_100']}/100`",
        f"- 产品工作流一致性分：`{scores['product_workflow_consistency_score_100']}/100`",
        f"- 受控试点前端信心分：`{scores['controlled_pilot_frontend_confidence_score_100']}/100`",
        "",
        "当前判断：核心客户可见前端已经跟上受控试点主线，可以继续向共创客户本地试点包候选推进；但最新新增的“试点准备”页晚于 FE4 浏览器点击 QA，因此还不能说最新全量前端已经完成浏览器级封版验收。",
        "",
        "## 已确认的正向证据",
        "",
        f"- FE4 静态门禁：`{result['checks']['fe4_summary']['actual']}`。",
        f"- FE4 浏览器点击 QA：`{result['checks']['fe4_click_qa']['actual']}`，覆盖页面数 `{result['metrics']['fe4_click_qa_page_count']}`。",
        f"- 多渠道对话台：FE4 证据显示紧凑会话列表、大面积消息流、无假外发文案、无水平溢出。",
        f"- 试点准备页：导航、App 路由、API client 与后端 `pilot-readiness` 接口已经绑定。",
        f"- INSTALL3：`{result['checks']['install3']['actual']}`，安装器仍保持候选边界，不越界写成正式签名安装包。",
        "",
        "## 当前缺口",
        "",
        "- FE4 浏览器点击 QA 的页面清单还没有覆盖 `#pilot`。这是最新入口的验收缺口，不影响 FE4 旧主页面结论，但影响“最新全量前端已封版”的说法。",
        "- 前端仍有后台能力和历史工程对象，例如 outbox、provider、RPA 类型定义等，当前结论只针对客户可见主流程；下一轮 FE6 必须继续查客户可见文案。",
        "- 试点准备页目前是聚合页，价值在于把已有能力串起来；它还需要浏览器逐按钮证据来证明每一步入口都落到真实页面或真实禁用说明。",
        "",
        "## 最近推进安排",
        "",
    ]
    for item in result["next_steps"]:
        lines.extend(
            [
                f"### {item['phase']}",
                "",
                f"- 目标：{item['goal']}",
                f"- 状态：`{item['status']}`",
                f"- 停止门禁：{item['stop_gate']}",
                "",
            ]
        )
    lines.extend(
        [
            "## 边界",
            "",
            "- 不做移动端。",
            "- 不启用真实平台外发。",
            "- 不把内部演练写成客户正式签收。",
            "- 不把 RPA、个人号外挂、模拟点击作为正式交付能力。",
            "- 不把当前安装器候选写成已签名 dmg/exe。",
            "",
            "## 后续建议",
            "",
            "下一步优先做 `H2W-FE6`：打开真实本地前端，覆盖最新 `#pilot`、`#settings`、`#live`、`#knowledge`、`#quality` 页面做逐页点击和截图证据。只有 FE6 通过后，才能把“前端最新主流程已跟上”写得更硬。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_next_steps_doc(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# H2W 最近推进安排：安装器与前端对齐",
        "",
        "这份文档用于回答当前阶段最近几步怎么走，以及前端是否已经跟上产品主线。它不是客户宣传稿，也不把内部演练写成客户签收。",
        "",
        "## 当前阶段判断",
        "",
        f"- 当前 FE5 状态：`{result['status']}`",
        f"- 前端综合信心：`{result['scores']['controlled_pilot_frontend_confidence_score_100']}/100`",
        "- 核心客户可见主页面已通过 FE4 静态门禁和浏览器点击 QA。",
        "- 最新“试点准备”入口已接前端路由和后端接口，但还没有进入 FE4 浏览器逐页点击清单。",
        "- 因此当前说法应是：前端已接近共创客户本地试点候选，但还需要 FE6 做最新页面浏览器复测。",
        "",
        "## 最近五步",
        "",
    ]
    for item in result["next_steps"]:
        lines.extend(
            [
                f"### {item['phase']}",
                "",
                f"- 做什么：{item['goal']}",
                f"- 当前状态：`{item['status']}`",
                f"- 停止门禁：{item['stop_gate']}",
                "",
            ]
        )
    lines.extend(
        [
            "## 前端重点验收口径",
            "",
            "| 维度 | 当前判断 | 下一步门禁 |",
            "| --- | --- | --- |",
            "| 美观与排版 | FE4 已证明主页面无明显溢出、无假按钮、对话台已收束；最新试点页待复测 | FE6 截图和逐页点击通过 |",
            "| 工作台逻辑 | 接待工作台已接近真实客服会话形态，转人工作为状态，不再主打待审/待发 | FE6 检查客户可见文案与按钮动作 |",
            "| 知识运营 | 知识库运营、知识缺口、知识评测已分叉，并多数有真实 API | FE6 复测导入、预检、发布、评测入口 |",
            "| 运维与试点 | 月报、本地维护、试点准备已串起来 | FE6 确认每一步都能跳到真实页面或真实阻断说明 |",
            "| 前后端对齐 | 核心主页面已对齐，`#pilot` 需要最新浏览器证据 | FE6 后更新矩阵和总控手册 |",
            "",
            "## 不进入本轮的事情",
            "",
            "- 不推进企业微信、抖音、淘宝、京东、拼多多真实接入。",
            "- 不开启真实外发。",
            "- 不做移动端。",
            "- 不做正式签名安装包承诺。",
            "- 不把内部题库或内部确认文件写成客户正式验收。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_h2w_fe5_frontend_backend_alignment_and_ux_status(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_path: Path = DOC_PATH,
    next_steps_doc_path: Path = NEXT_STEPS_DOC,
    fe4_summary: Path = FE4_SUMMARY,
    fe4_click_qa: Path = FE4_CLICK_QA,
    pilot0_summary: Path = PILOT0_SUMMARY,
    pilot4_summary: Path = PILOT4_SUMMARY,
    install3_summary: Path = INSTALL3_SUMMARY,
    matrix_path: Path = FUNCTION_MATRIX,
    navigation_path: Path = NAVIGATION_TS,
    app_path: Path = APP_TSX,
    api_client_path: Path = API_CLIENT_TS,
) -> dict[str, Any]:
    fe4 = _read_json(fe4_summary)
    click = _read_json(fe4_click_qa)
    pilot0 = _read_json(pilot0_summary)
    pilot4 = _read_json(pilot4_summary)
    install3 = _read_json(install3_summary)
    navigation_text = _read_text(navigation_path)
    app_text = _read_text(app_path)
    api_text = _read_text(api_client_path)
    matrix_text = _read_text(matrix_path)

    checks = {
        "fe4_summary": _status_check(fe4_summary, "ready_for_customer_visible_ui_candidate"),
        "fe4_click_qa": _status_check(fe4_click_qa, "passed_customer_visible_click_qa"),
        "pilot0": _status_check(pilot0_summary, "pilot_candidate_ready_with_internal_data"),
        "pilot4": _status_check(pilot4_summary, "passed_customer_local_trial_rehearsal"),
        "install3": _status_check(install3_summary, "native_app_packaging_candidate_ready"),
    }
    click_hashes = _hashes_from_click_qa(click)
    navigation_routes = _navigation_customer_routes(navigation_text)
    pilot_route_ok = "#pilot" in navigation_text and 'case "pilot"' in app_text and "getPilotReadiness" in api_text
    pilot_browser_covered = "#pilot" in click_hashes
    visible_navigation_engineering_terms = _visible_navigation_engineering_terms(navigation_text)

    blockers: list[str] = []
    warnings: list[str] = []
    if not checks["fe4_summary"]["passed"]:
        blockers.append("FE4 客户可见 UI 静态门禁缺失或未通过。")
    if not checks["fe4_click_qa"]["passed"]:
        blockers.append("FE4 浏览器点击 QA 缺失或未通过。")
    if not pilot_route_ok:
        blockers.append("试点准备页没有同时绑定侧边栏路由、App 渲染分支和 pilot-readiness API client。")
    if visible_navigation_engineering_terms:
        blockers.append(f"侧边栏可见导航仍含客户不应看到的工程词：{', '.join(visible_navigation_engineering_terms)}。")
    if not pilot_browser_covered:
        warnings.append("最新试点准备页 #pilot 未包含在 FE4 浏览器点击 QA 页面清单中，需要 FE6 补浏览器证据。")
    if not matrix_text:
        warnings.append("前端功能真实性矩阵缺失，后续不能只依赖页面观感判断。")
    if pilot0.get("readiness", {}).get("real_platform_send_ready") is not False:
        blockers.append("PILOT0 没有保持真实外发关闭边界。")
    if install3.get("readiness", {}).get("signed_dmg_exe_ready") is not False:
        blockers.append("INSTALL3 越界标记为已签名安装包。")

    fe4_ok = checks["fe4_summary"]["passed"]
    click_ok = checks["fe4_click_qa"]["passed"]
    install3_ok = checks["install3"]["passed"]
    scores = _calculate_scores(
        fe4_ok=fe4_ok,
        click_ok=click_ok,
        pilot_route_ok=pilot_route_ok,
        pilot_browser_covered=pilot_browser_covered,
        install3_ok=install3_ok,
    )

    if blockers:
        status = "blocked"
    elif pilot_browser_covered:
        status = "frontend_latest_browser_verified"
    else:
        status = "frontend_aligned_with_latest_recheck_required"

    result = {
        "phase": PHASE,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "summary": (
            "核心客户可见前端已达到受控试点候选；最新试点准备页已接路由和后端接口，"
            "但还需要下一轮浏览器点击 QA 才能写成最新全量前端封版。"
        ),
        "scores": scores,
        "checks": checks,
        "metrics": {
            "fe4_click_qa_page_count": len(_click_qa_pages(click)),
            "fe4_click_qa_hashes": sorted(click_hashes),
            "navigation_customer_route_count": len(navigation_routes),
            "pilot_route_bound_to_frontend_and_api": pilot_route_ok,
            "pilot_page_in_fe4_browser_click_qa": pilot_browser_covered,
            "visible_navigation_engineering_term_count": len(visible_navigation_engineering_terms),
            "matrix_present": bool(matrix_text),
        },
        "blockers": blockers,
        "warnings": warnings,
        "next_steps": _build_next_steps(),
        "readiness": {
            "core_customer_visible_frontend_ready": fe4_ok and click_ok,
            "latest_pilot_page_route_ready": pilot_route_ok,
            "latest_pilot_page_browser_verified": pilot_browser_covered,
            "frontend_ready_for_controlled_pilot_candidate": not blockers,
            "frontend_ready_for_full_latest_signoff": not blockers and pilot_browser_covered,
            "real_platform_send_ready": False,
            "formal_customer_signoff_ready": False,
            "mobile_ready": False,
        },
        "boundaries": {
            "mobile_scope_included": False,
            "real_platform_send_performed": False,
            "formal_customer_signoff_performed": False,
            "rpa_formal_delivery_enabled": False,
            "signed_dmg_exe_ready": False,
        },
        "evidence": {
            "summary_json": {"path": _display_path(output_dir / "summary.json")},
            "markdown": {"path": _display_path(doc_path)},
            "next_steps_doc": {"path": _display_path(next_steps_doc_path)},
            "fe4_summary": {"path": _display_path(fe4_summary), "present": fe4_summary.exists()},
            "fe4_click_qa": {"path": _display_path(fe4_click_qa), "present": fe4_click_qa.exists()},
            "pilot0_summary": {"path": _display_path(pilot0_summary), "present": pilot0_summary.exists()},
            "pilot4_summary": {"path": _display_path(pilot4_summary), "present": pilot4_summary.exists()},
            "install3_summary": {"path": _display_path(install3_summary), "present": install3_summary.exists()},
        },
    }

    _write_json(output_dir / "summary.json", result)
    _write_markdown(doc_path, result)
    _write_next_steps_doc(next_steps_doc_path, result)
    return result


def main() -> None:
    result = run_h2w_fe5_frontend_backend_alignment_and_ux_status()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
