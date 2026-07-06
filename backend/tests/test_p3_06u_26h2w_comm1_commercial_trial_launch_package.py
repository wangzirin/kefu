from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_p3_06u_26h2w_comm1_commercial_trial_launch_package.py"


def load_module():
    spec = importlib.util.spec_from_file_location("comm1_gate", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_comm1_builds_commercial_trial_package_with_internal_sample(tmp_path: Path) -> None:
    module = load_module()
    output_dir = tmp_path / "comm1"
    doc_path = tmp_path / "COMM1.md"

    result = module.run_comm1_commercial_trial_launch_package(
        output_dir=output_dir,
        doc_path=doc_path,
    )

    assert result["status"] == "commercial_trial_launch_package_v1_candidate_with_internal_sample"
    assert result["customer_data_used"] is False
    assert result["internal_sample_used"] is True

    readiness = result["readiness"]
    assert readiness["ready_for_external_pitch_as_controlled_trial"] is True
    assert readiness["ready_for_direct_customer_production"] is False
    assert readiness["ready_for_mature_all_channel_commercial"] is False
    assert readiness["real_channel_closed_loop_ready"] is False
    assert readiness["signed_installer_ready"] is False

    five_items = result["five_fast_items"]
    assert set(five_items) == {
        "真实客户样板资料包",
        "客户知识中心最终流程",
        "前端最终成品级 QA",
        "本地部署交付包 v1",
        "对外试跑商业资料包",
    }
    assert all(item["ready"] for item in five_items.values())

    seven_blocks = result["seven_core_blocks"]
    assert set(seven_blocks) == {
        "真实客户资料闭环",
        "客户知识中心最终产品化",
        "前端最终成品感",
        "真实渠道闭环",
        "安装和交付体验",
        "真实安全与红队报告",
        "商用包装",
    }
    assert seven_blocks["真实渠道闭环"]["status"] == "planned_official_authorization_required"
    assert seven_blocks["真实渠道闭环"]["ready_for_production"] is False

    expected_docs = {
        "COMMERCIAL_TRIAL_PACKAGE_README.md",
        "CUSTOMER_SAMPLE_MATERIALS_PACK.md",
        "CUSTOMER_KNOWLEDGE_CENTER_FINAL_FLOW.md",
        "FRONTEND_FINAL_QA_AND_PRODUCT_POLISH.md",
        "LOCAL_DEPLOYMENT_HANDOFF_V1.md",
        "PRODUCT_INTRO_TRIAL_CUSTOMER.md",
        "CUSTOMER_USER_MANUAL_TRIAL.md",
        "SERVICE_BOUNDARY_AND_TRIAL_AGREEMENT.md",
        "QUOTE_AND_SERVICE_SCOPE_TRIAL.md",
        "SEVEN_CORE_BLOCKS_READINESS_MATRIX.md",
    }
    generated_docs = {Path(path).name for path in result["generated_documents"]}
    assert expected_docs.issubset(generated_docs)

    archive_path = ROOT / result["archive"]["path"]
    assert archive_path.exists()
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == result["status"]
    assert manifest["boundaries"]["real_platform_send_ready"] is False
    assert manifest["boundaries"]["signed_dmg_exe_ready"] is False
    assert result["archive"]["secret_scan_findings"] == []


def test_comm1_does_not_claim_finished_channels_or_formal_signoff(tmp_path: Path) -> None:
    module = load_module()
    result = module.run_comm1_commercial_trial_launch_package(
        output_dir=tmp_path / "comm1",
        doc_path=tmp_path / "COMM1.md",
    )

    text = json.dumps(result, ensure_ascii=False)
    forbidden_phrases = [
        "正式客户验收已完成",
        "客户正式签收已完成",
        "真实外发已接通",
        "全渠道已接通",
        "签名安装包已完成",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in text

    assert "真实平台自动外发" in result["not_ready_for"]
    assert "企业微信、公众号、抖音、淘宝、京东、拼多多等真实渠道接通" in result["not_ready_for"]
