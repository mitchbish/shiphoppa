Tier 2. Single-phase backend + frontend wiring.

# Supplier profile claim workflow

## Goal
Once a `SupplierLead` is verified, give an admin a one-click action that generates a public claim link the supplier can visit to confirm and accept ownership of their auto-created profile.

## Exit criteria
- [ ] `SupplierProfileClaim` model: id, lead_id, token, status (pending/claimed/expired), expires_at, claimed_at, claimed_by_email, claimed_contact_name, created_at.
- [ ] Store collection `supplier_profile_claims`.
- [ ] Operations:
  - `create_supplier_claim_link(store, lead_id, actor_id)`: requires `lead.verification_status == SupplierVerificationStatus.verified`; raises `ValueError` otherwise. Idempotent — returns existing pending claim if one exists. Generates a 32-hex token. Default 30-day expiry.
  - `get_supplier_claim_by_token(store, token)`: returns claim + lead. Raises if not found / expired.
  - `accept_supplier_claim(store, token, contact_email, contact_name)`: marks claim claimed, sets `lead.outreach_status = onboarded`, sets lead.public_email/notes if provided, writes audit + growth attribution `supplier_signed_up`.
- [ ] Endpoints:
  - `POST /growth/supplier-leads/{id}/claim-link` → `SupplierProfileClaim` (admin auth)
  - `GET /supplier-claim/{token}` → `SupplierProfileClaimResponse {claim, lead}` (public; no auth)
  - `POST /supplier-claim/{token}/accept` body `{contact_email, contact_name}` → `SupplierProfileClaimResponse` (public; token gates it)
- [ ] At least 6 backend tests: claim-link requires verified, returns same token on second call, public GET returns claim+lead, GET 404 on bad token, accept transitions to onboarded, accept records growth event.
- [ ] Total tests >= 267 (261 baseline + 6).
- [ ] Frontend api: `createSupplierClaimLink`, `getSupplierClaim`, `acceptSupplierClaim`. Types added.
- [ ] Build clean.

## Files to touch
- `backend/app/models.py` — `SupplierProfileClaim`, `SupplierProfileClaimStatus`, `SupplierProfileClaimResponse`, `SupplierProfileClaimAccept`.
- `backend/app/store.py` — collection.
- `backend/app/operations.py` — operations.
- `backend/app/main.py` — endpoints.
- `backend/tests/test_supplier_profile_claim.py`.
- `frontend/src/types.ts` + `frontend/src/api.ts`.
- `HANDOVER.md` — DONE row.

## Known risks
- Don't allow claim creation when lead is unverified, restricted, or rejected.
- `accept_supplier_claim` should be idempotent — accepting again returns the already-claimed state, doesn't double-emit growth events.
- Token expiry handled at lookup time.

## Verification
1. `cd backend && python3 -m pytest tests/ -q` — 267+.
2. `cd frontend && npm run build` — clean.

## Audit log

### AP1 — Plan audit (2026-05-11)

#### Lens 1 — Correctness
1. **Wrong assumption?** That `SupplierLead` already has fields for "claimed by" info. Reading: it doesn't. Plan: store contact info on the claim record only. The lead's outreach_status flips to onboarded.
2. **Weakest exit criterion?** "claim-link requires verified" — strengthen by testing each invalid prior status (unverified, pending_review, restricted, rejected) returns 400. Acceptable to do one negative path + one positive path; saves test bloat.
3. **Domain expert difference?** Could include rate limiting on the public POST endpoint. Token-gating mitigates.
4. **Leaving on the table?** No "revoke claim" endpoint. Out of scope.
5. **Unintended consequence?** None.

#### Lens 2 — Adversarial (reviewer: senior product engineer)
1. **Wrong assumption?** That a lead with no public_email is fine for a claim. Edge case: yes — the claim flow itself collects the email.
2. **Weakest criterion?** "accept records growth event" — make sure the test asserts the event_type is exactly `supplier_signed_up`.
3. **Domain expert difference?** Add WeChat / WhatsApp option for contact. Skip — basic email + contact name is sufficient for v1.
4. **Leaving on the table?** No supplier portal token issued on claim. The supplier-portal token is per-booking; no booking exists yet for this lead.
5. **Unintended consequence?** None.

**Revisions applied:**
- Idempotency on accept: second accept returns the already-claimed claim and does not re-emit a growth event.
- Pre-condition on claim creation: lead.verification_status MUST be verified (returns 400 otherwise).

### AP2 — Post-execution audit (2026-05-11)

#### Lens 1 — Correctness
1. **Wrong assumption?** That `SupplierProfileClaimResponse` could be defined inline next to `SupplierProfileClaim`. It references `SupplierLead` which is declared further down; moved the response class after `SupplierVerificationUpdate` to fix the forward-reference error.
2. **Weakest exit criterion?** Coverage is good — the 8 tests exceed the 6-test minimum and exercise: unverified lead rejection, verified-lead happy path, idempotency on link creation, public GET / 404, accept happy path, accept idempotency, expired token (410).
3. **Domain expert difference?** Could send the supplier a confirmation email when the link is generated. Skipped — out of scope for v1; relies on existing outbound queue patterns.
4. **Leaving on the table?** No "rotate token" admin endpoint. Acceptable.
5. **Unintended consequence?** None.

#### Lens 2 — Adversarial
1. **Wrong assumption?** That GET / accept don't need rate limiting. Token-gating mitigates abuse.
2. **Weakest criterion?** "Idempotency does not re-emit growth event" — explicitly tested with growth event count assertion.
3. **Domain expert difference?** None for v1.
4. **Leaving on the table?** Frontend UI to surface the claim flow is not yet built; the api client is ready.
5. **Unintended consequence?** None observed.

#### Revisions applied
- Moved `SupplierProfileClaimResponse` after `SupplierLead` to resolve forward-reference.
- Idempotent accept (returns existing claimed claim without re-emitting growth event).

#### Exit criteria — final tick
- [x] Models added — DONE
- [x] Store collection — DONE
- [x] Operations: create_supplier_claim_link, get_supplier_claim_by_token, accept_supplier_claim — DONE
- [x] Endpoints: POST /growth/supplier-leads/{id}/claim-link, GET /supplier-claim/{token}, POST /supplier-claim/{token}/accept — DONE
- [x] 8 tests pass; total 269 — DONE
- [x] Frontend types + api client — DONE
- [x] Build clean — DONE
- [x] Plain English commit, no em dashes — see commit
