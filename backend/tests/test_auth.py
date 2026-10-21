"""Authentication (token verification) and authorization (a dentist only reaches their own patients)."""

import time
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from app.core.auth import InvalidToken, TokenVerifier
from tests.conftest import DENTIST_ID, OTHER_DENTIST_ID, http_client, make_patient

ISSUER = "https://test.supabase.co/auth/v1"
KEY = ec.generate_private_key(ec.SECP256R1())


class _FakeJwks:
    def __init__(self, key):
        self.key = key

    def get_signing_key_from_jwt(self, token):
        return type("K", (), {"key": self.key})()


def verifier(public_key=None, secret=""):
    v = TokenVerifier(ISSUER, secret)
    v._jwks = _FakeJwks(public_key or KEY.public_key())
    return v


def token(key=KEY, alg="ES256", **over):
    claims = {"sub": str(DENTIST_ID), "aud": "authenticated", "iss": ISSUER, "role": "authenticated",
              "email": "d@clinic.test", "exp": int(time.time()) + 600, "user_metadata": {"full_name": "Dr Test"}}
    claims.update(over)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, key, algorithm=alg)


# --- token verification ---------------------------------------------------------------

def test_valid_token_yields_the_dentist():
    d = verifier().verify(token())
    assert d.id == DENTIST_ID and d.email == "d@clinic.test" and d.full_name == "Dr Test"


@pytest.mark.parametrize("over", [
    {"exp": int(time.time()) - 10},          # expired
    {"aud": "anon"},                          # wrong audience
    {"iss": "https://evil.example/auth/v1"},  # another project
    {"role": "anon"},                         # anon key session, not a user
    {"sub": None},                            # no subject
])
def test_invalid_claims_are_rejected(over):
    with pytest.raises(InvalidToken):
        verifier().verify(token(**over))


def test_signature_from_another_key_is_rejected():
    with pytest.raises(InvalidToken):
        verifier().verify(token(key=ec.generate_private_key(ec.SECP256R1())))


def test_garbage_is_rejected():
    with pytest.raises(InvalidToken):
        verifier().verify("not-a-jwt")


def test_legacy_hs256_needs_the_configured_secret():
    hs = token(key="s3cret-s3cret-s3cret-s3cret-s3cret!", alg="HS256")
    with pytest.raises(InvalidToken):
        verifier().verify(hs)
    assert verifier(secret="s3cret-s3cret-s3cret-s3cret-s3cret!").verify(hs).id == DENTIST_ID


# --- HTTP: authentication -------------------------------------------------------------------

async def test_api_requires_a_bearer_token(world):
    import httpx
    from app.main import app
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    res = await client.get("/api/v1/patients")
    assert res.status_code == 401 and res.headers["www-authenticate"] == "Bearer"
    assert (await client.get("/api/v1/patients", headers={"Authorization": "Bearer junk"})).status_code == 401
    assert (await client.get("/health")).status_code == 200      # health stays public


# --- HTTP: authorization ----------------------------------------------------------------------

async def test_another_dentists_records_answer_404(world):
    w = world(make_patient(dentist_id=OTHER_DENTIST_ID))
    f = w.add_finding(review_status="pending")
    client = http_client(w)
    for url in (f"/api/v1/patients/{w.patient.id}", f"/api/v1/scans/{w.scan_id}/findings",
                f"/api/v1/findings/{f.id}", f"/api/v1/treatments?scan_id={w.scan_id}",
                f"/api/v1/feedback?scan_id={w.scan_id}"):
        assert (await client.get(url)).status_code == 404, url
    assert (await client.post("/api/v1/findings/review",
                              json={"finding_id": str(f.id), "review_status": "rejected"})).status_code == 404
    assert (await client.post(f"/api/v1/recommendations/scans/{w.scan_id}")).status_code == 404
    assert (await client.post("/api/v1/prescriptions/check", json={
        "patient_id": str(w.patient.id), "drug_name": "Ibuprofen", "indication_type": "pain_management"})).status_code == 404
    assert w.feedback.rows == [] and w.treatments.rows == {}    # nothing was written


async def test_unowned_legacy_patients_are_invisible(world):
    w = world(make_patient(dentist_id=None))
    assert (await http_client(w).get(f"/api/v1/patients/{w.patient.id}")).status_code == 404


async def test_writes_are_stamped_with_the_signed_in_dentist_not_the_body(world):
    w = world()
    f = w.add_finding(disease="Caries", review_status="pending")
    client = http_client(w)
    spoof = str(uuid4())
    res = await client.post("/api/v1/findings/review",
                            json={"finding_id": str(f.id), "review_status": "rejected", "dentist_id": spoof})
    assert res.status_code == 200
    assert w.feedback.rows[0].dentist_id == DENTIST_ID

    w.add_finding(disease="Periapical Lesion", fdi="46")
    gen = await client.post(f"/api/v1/recommendations/scans/{w.scan_id}", json={"dentist_id": spoof})
    assert gen.status_code == 201
    assert all(t.dentist_id == DENTIST_ID for t in w.treatments.rows.values())


async def test_shared_default_request_is_not_mutated(world):
    from app.domain.recommendation import RecommendationRequest
    w = world()
    w.add_finding(disease="Caries")
    assert (await http_client(w).post(f"/api/v1/recommendations/scans/{w.scan_id}")).status_code == 201
    assert RecommendationRequest().dentist_id is None
