from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


CHECKS = {
    "docs/P3-06U-26H2W_NETWORKED_ENGINEERING_MASTER_PLAN.md": [
        "P3-06U-26H2W 网状工程推进总纲",
        "H2W-7X",
        "provenance_id",
        "model_call_records",
        "reply_citation_snapshots",
        "真实外发继续关闭",
    ],
    "backend/app/models/foundation.py": [
        "provenance_id",
        "class ModelCallRecord",
        "class ReplyCitationSnapshot",
        "raw_text_logged",
    ],
    "backend/app/migrations/versions/0031_h2w7x_reply_provenance_records.py": [
        "0031_h2w7x_reply_provenance",
        "reply_decisions",
        "model_call_records",
        "reply_citation_snapshots",
    ],
    "backend/app/services/reply_provenance.py": [
        "build_reply_provenance_id",
        "create_model_call_record_from_result",
        "create_reply_decision_citation_snapshot",
        "create_reply_match_citation_snapshots",
    ],
    "backend/app/services/reply_decisions.py": [
        "build_reply_provenance_id",
        "create_reply_decision_citation_snapshot",
        "provenance_id",
    ],
    "backend/app/services/reply_orchestrator.py": [
        "create_model_call_record_from_result",
        "create_reply_match_citation_snapshots",
        "provenance_id",
    ],
    "backend/app/services/rag_governance.py": [
        "ModelCallRecord",
        "model_call_records",
        "cost_source",
    ],
    "backend/tests/test_reply_decisions_api.py": [
        "ReplyCitationSnapshot",
        "provenance_id",
        "no_citation_reason",
    ],
    "backend/tests/test_reply_orchestrator_api.py": [
        "ModelCallRecord",
        "ReplyCitationSnapshot",
        "raw_text_logged",
    ],
    "backend/tests/test_rag_cost_governance_api.py": [
        "ModelCallRecord",
        "model_call_records",
        "estimated_model_cost",
    ],
}


def main() -> None:
    missing: list[str] = []
    for rel_path, needles in CHECKS.items():
        path = ROOT / rel_path
        if not path.exists():
            missing.append(f"{rel_path}: file missing")
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                missing.append(f"{rel_path}: missing {needle!r}")
    if missing:
        raise SystemExit("\n".join(missing))
    print("PASS p3-06u-26h2w7x reply provenance")


if __name__ == "__main__":
    main()
