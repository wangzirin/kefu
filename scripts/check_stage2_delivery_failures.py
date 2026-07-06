#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_TEXT = {
    "backend/app/models/foundation.py": [
        "class DeliveryFailureReview",
        "normalized_status",
        "provider_error_code",
        "needs_review",
        "next_action",
    ],
    "backend/app/migrations/versions/0007_delivery_failure_reviews.py": [
        "delivery_failure_reviews",
        "normalized_status",
        "provider_error_code",
        "ix_delivery_failure_reviews_tenant_status",
    ],
    "backend/app/services/delivery_failures.py": [
        "normalize_delivery_status",
        "attach_delivery_normalization_and_review",
        "unknown_provider_status",
        "provider_rate_limited",
        "manual_review_provider_status",
        "delivery_failure_review.created",
    ],
    "backend/app/api/delivery_failures.py": [
        "/tenants/{tenant_id}/delivery-failure-reviews",
        "/delivery-failure-reviews/{review_id}",
        "require_current_principal",
    ],
    "backend/app/schemas/delivery_failures.py": [
        "DeliveryFailureReviewRead",
        "DeliveryFailureReviewUpdate",
        "resolved",
        "ignored",
    ],
    "backend/app/services/channel_connectors.py": [
        "attach_delivery_normalization_and_review",
        "normalized_status",
        "failure_review_id",
    ],
    "backend/tests/test_delivery_failure_reviews_api.py": [
        "test_failed_platform_receipt_is_normalized_and_enters_failure_review_queue",
        "test_successful_platform_receipt_is_normalized_without_failure_review",
        "test_unknown_provider_receipt_status_enters_manual_review_queue",
    ],
    "frontend/src/api/client.ts": [
        "DeliveryFailureReview",
        "listDeliveryFailureReviews",
        "resolveDeliveryFailureReview",
        "/delivery-failure-reviews",
    ],
    "frontend/src/App.tsx": [
        "FailureReviewPanel",
        "失败复盘队列",
        "标记已处理",
        "refreshFailureReviews",
    ],
}


def fail(message: str) -> None:
    print(f"FAIL stage2 delivery failures: {message}")
    sys.exit(1)


def main() -> None:
    for path, fragments in REQUIRED_TEXT.items():
        full_path = ROOT / path
        if not full_path.exists():
            fail(f"missing file: {path}")
        content = full_path.read_text(encoding="utf-8")
        missing = [fragment for fragment in fragments if fragment not in content]
        if missing:
            fail(f"missing fragment in {path}: {', '.join(missing)}")
    print("PASS stage2 delivery failures")


if __name__ == "__main__":
    main()
