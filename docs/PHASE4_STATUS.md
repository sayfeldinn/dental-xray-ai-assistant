# Phase 4 Status: Active Feedback & Logging (Step 6)

**Verified:** 147 automated tests pass (26 new); live run against the dev Supabase project with a throwaway patient (auto-deleted, 0 rows left). ML forwarding was **not** exercised live on purpose (it would append rows to the ML service's CSV queue); it is covered by tests with a fake client.

## 1. What was built

The `clinical_feedback_logs` table (created in Phase 1) is now an append-only ledger of **where the dentist departed from the AI**. Nothing is logged when the dentist accepts what the AI proposed: the table has no "accepted" correction type, and a confirmation carries nothing to learn from.

| Trigger | Stage | correction_type |
| :--- | :--- | :--- |
| Finding review `rejected` | finding_detection | `false_positive` |
| Finding review `modified` to a different disease | finding_detection | `misclassification` |
| `POST /feedback/missed-findings` (lesion the AI missed) | finding_detection | `false_negative` |
| Prescription rejected, drug swapped, or accepted over a flag with `override_reason` | prescription_dosing | `drug_override` |
| Prescription dose / frequency / duration changed (same drug) | prescription_dosing | `dosage_adjusted` |
| Treatment cancelled, or category/description changed | treatment_recommendation | `custom_note` |

`ai_original_data` is the AI's value (tooth, disease, confidence, box; or the proposed drug, regimen and rule IDs); `dentist_corrected_data` is the dentist's. Acknowledging warnings without changing anything is **not** a correction.

## 2. Layout (same layering as Phase 3)

| Piece | File |
| :--- | :--- |
| Models, FDI/disease validation | `domain/feedback.py` |
| Pure builders (before/after -> ledger row), ML payload, summary | `services/feedback/` (`builder.py`, `summary.py`) |
| Persistence (insert + list only) | `services/supabase_client/feedback_service.py` |
| Orchestration | `ClinicalWorkflowService`: `review_finding`, `report_missed_finding`, `_record`, `list_feedback`, `feedback_summary`; `decide_prescription` / `decide_treatment` now log |
| HTTP | `api/v1/feedback.py`; `POST /findings/review` now goes through the workflow |

## 3. Endpoints

- `GET /api/v1/feedback?scan_id=&stage=&correction_type=` newest first
- `GET /api/v1/feedback/summary?scan_id=` counts by stage and type
- `POST /api/v1/feedback/missed-findings` body `{scan_id, tooth_fdi, disease, notes?}`; it logs and forwards, and does not create a finding (use `POST /treatments` for the dentist's plan)

## 4. Forwarding to the ML service

Detection rows (false positive, misclassification, false negative) are forwarded through `DentexClient.submit_feedback` (the only path to `dentex_week3`), with `image_id` = scan id. A missed lesion is sent with `original_disease="None"`. Drug and treatment rows are audit-only and never leave the backend.

## 5. Design decisions

1. **Best effort after the decision is saved.** A ledger or ML failure is logged (`logger.exception`) and never fails the request or undoes a clinical decision. The exception is `missed-findings`, where the ledger write *is* the request, so a failure surfaces. An ML outage never removes the ledger row.
2. **Append-only.** The service has no update or delete. Re-reviewing a finding appends a new row; the earlier row stays (read newest first).
3. **Ledger not configured** (`feedback=None`): decisions still work; ledger reads return 422.
4. **`dentist_id` stays NULL** until Phase 5 auth.

## 6. Known limitations

1. **Cannot tell AI-proposed from dentist-authored prescriptions.** Both are stored `proposed`, so a decision on a dentist-authored prescription is logged against its own draft. Harmless for the audit trail; drug rows are never used for model retraining. A future `origin` column would fix it (needs a migration).
2. **Reversed reviews leave a stale row.** Reject then re-confirm keeps the first `false_positive` row and logs nothing for the confirmation. Order by `created_at` to see the final state.
3. **No ML-side acknowledgement is stored** (no column for forwarded status); failures appear only in the server log.
4. **AI report feedback** (`/feedback/report` on the ML service) is not wired: `DentexClient` has no method for it and the backend does not store the report edits.
5. **No retraining job.** The ML service accumulates CSVs; consuming them is out of scope.
