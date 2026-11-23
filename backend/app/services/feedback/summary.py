"""Aggregate ledger rows into the counts the UI and the retraining queue read."""

from collections import Counter
from collections.abc import Iterable

from app.domain.feedback import FeedbackLog, FeedbackSummary


def summarize(logs: Iterable[FeedbackLog]) -> FeedbackSummary:
    logs = list(logs)
    return FeedbackSummary(
        total=len(logs),
        by_stage=dict(Counter(log.stage for log in logs)),
        by_correction_type=dict(Counter(log.correction_type for log in logs)),
    )
