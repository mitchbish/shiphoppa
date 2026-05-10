Tier 2. Backend single-phase skeleton.

# InsurancePolicy + ClaimRecord skeleton

## Goal
Add cargo-insurance and damage-claim records per booking so the operator can capture coverage and post-arrival exceptions, even before any insurance provider is wired in.

## Exit criteria
- [ ] `InsurancePolicy` model: id, booking_id, insurance_required, waived_by, insured_value (Optional), currency, provider, policy_reference, premium_usd (Optional), coverage_notes, document_id (Optional), created_at, updated_at.
- [ ] `ClaimRecord` model: id, booking_id, insurance_policy_id (Optional), claim_type (damage, loss, shortage, delay, other), claim_status (draft, submitted, under_review, approved, rejected, paid, closed), claim_amount_usd, evidence_document_ids, photo_document_ids, survey_report_document_id, submitted_at, resolved_at, recovery_amount_usd, notes, created_at, updated_at.
- [ ] Store collections.
- [ ] Operations:
  - `record_insurance_policy(store, booking_id, payload, actor_id)` upserts (one per booking).
  - `get_insurance_policy_for_booking`.
  - `create_claim_record(store, booking_id, payload, actor_id)`.
  - `update_claim_record(store, claim_id, payload, actor_id)` — status changes write a separate audit event.
  - `list_claim_records_for_booking`.
- [ ] Endpoints (admin auth except importer can create their own claim):
  - `POST/GET /bookings/{id}/insurance-policy` (admin POST, importer GET)
  - `POST /bookings/{id}/claims` (importer)
  - `GET /bookings/{id}/claims` (importer)
  - `PATCH /claims/{id}` (admin)
- [ ] At least 7 backend tests; total >= 306.
- [ ] Frontend types + clients.
- [ ] Build clean.

## Risks
- Insurance one-per-booking — POST upserts.
- Claim status transitions written to audit when changed; other field updates write a generic update audit event.

## Audit log

### AP1
Lens 1: claim_amount and recovery in USD only is a simplification. Acceptable for v1; LandedCostActual already handles multi-currency with `currency`.
Lens 2: don't accidentally let importers PATCH claim status (admin-only).
Revisions: separate the importer create + admin patch endpoints clearly.

### AP2 — Post-execution audit (2026-05-11)
Lens 1: insurance is one-per-booking — confirmed via upsert test. Status flips to submitted record `submitted_at`; status flips to a terminal status (approved/rejected/paid/closed) record `resolved_at`. Both verified.
Lens 2: importer creates claims (their own claim flow); admin patches status. Verified via header role split.
Revisions: none.

#### Exit criteria — final tick
- [x] Models + enums — DONE
- [x] Store + reset_store_for_tests — DONE
- [x] Operations + endpoints — DONE
- [x] 7 backend tests pass; total 306 — DONE
- [x] Frontend types + clients — DONE
- [x] Build clean — DONE
