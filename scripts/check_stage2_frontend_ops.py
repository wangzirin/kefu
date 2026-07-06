from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require_contains(path: str, snippets: list[str]) -> None:
    text = (ROOT / path).read_text()
    missing = [snippet for snippet in snippets if snippet not in text]
    if missing:
        raise SystemExit(f"{path} missing: {', '.join(missing)}")


def main() -> None:
    require_contains(
        "frontend/src/api/client.ts",
        [
            "listHumanReviewInbox",
            "resolveHumanReviewTask",
            "createOutboxDraftFromReview",
            "listOutboxDrafts",
            "confirmOutboxDraft",
            "createDryRunSendAttempt",
            "runOutboxWorker",
            "OutboxWorkerRun",
            "listDeliveryFailureReviews",
            "resolveDeliveryFailureReview",
            "DeliveryFailureReview",
        ],
    )
    require_contains(
        "frontend/src/App.tsx",
        [
            "ReviewInboxPanel",
            "人工审核收件箱",
            "批准入待发送",
            "确认待发送",
            "模拟发送",
            "运行发送检查",
            "最近发送检查",
            "FailureReviewPanel",
            "失败复盘队列",
            "标记已处理",
            "pending_confirmation",
            "ready_to_send",
        ],
    )
    require_contains(
        "frontend/src/styles.css",
        [
            ".review-panel",
            ".review-row",
            ".evidence-strip",
            ".review-actions",
            ".outbox-row",
            ".worker-summary",
            ".failure-row",
            ".retry-pill",
        ],
    )
    print("PASS stage2 frontend ops")


if __name__ == "__main__":
    main()
