"""Regression tests for the Phase 2 bugs found while preparing Phase 3."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.finding import FindingReviewRequest
from app.services.supabase_client.finding_service import FindingService
from tests.conftest import make_finding


class RecordingClient:
    """Minimal stand-in for the supabase query builder that records the chain."""

    def __init__(self):
        self.calls = []

    def table(self, name):
        return self

    def __getattr__(self, method):
        def record(*args, **kwargs):
            self.calls.append((method, args))
            return self
        return record

    def execute(self):
        return type("Resp", (), {"data": []})()


def service(client) -> FindingService:
    svc = FindingService.__new__(FindingService)
    svc.client, svc.table = client, "findings"
    return svc


async def test_validated_findings_include_modified_ones():
    client = RecordingClient()
    await service(client).get_confirmed_findings(uuid4())
    assert ("in_", ("review_status", ["confirmed", "modified"])) in client.calls


async def test_review_without_dentist_does_not_write_a_placeholder_reviewer():
    client = RecordingClient()
    updates = []
    client.update = lambda data: (updates.append(data), client)[1]
    await service(client).review_finding(uuid4(), "confirmed")
    assert "reviewed_by" not in updates[0] and updates[0]["review_status"] == "confirmed"


def test_modified_review_needs_a_valid_disease_label():
    with pytest.raises(ValidationError):
        FindingReviewRequest(finding_id=uuid4(), review_status="modified")
    with pytest.raises(ValidationError):
        FindingReviewRequest(finding_id=uuid4(), review_status="modified", confirmed_disease="Gingivitis")
    FindingReviewRequest(finding_id=uuid4(), review_status="modified", confirmed_disease="Deep Caries")


def test_effective_disease_prefers_the_dentist_correction():
    assert make_finding("Caries", confirmed_disease="Deep Caries").effective_disease == "Deep Caries"
    assert make_finding("Caries").effective_disease == "Caries"
