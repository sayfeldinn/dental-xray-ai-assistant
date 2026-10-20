"""Aggregate ledger rows into the counts the UI and the retraining queue read."""

from collections import Counter
from typing import Iterable

from app.domain.feedback import FeedbackLog, FeedbackSummary


def summarize(logs: Iterable[FeedbackLog]) -> FeedbackSummary:
    logs = list(logs)
    return FeedbackSummary(
        total=len(logs),
        by_stage=dict(Counter(l.stage for l in logs)),
        by_correction_type=dict(Counter(l.correction_type for l in logs)),
    )
