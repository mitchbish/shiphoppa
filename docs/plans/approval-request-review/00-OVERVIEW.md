Tier 2 (Standard). Single-phase backend + frontend wiring.

# Approval `request-review` endpoint

## Goal
Add `POST /approvals/{id}/request-review` so an importer can escalate a pending approval to admin/ops without approving or rejecting it.

## Exit criteria
- [ ] `ApprovalRequest` gains 3 optional fields: `review_requested_by: Optional[str]`, `review_requested_at: Optional[datetime]`, `review_requested_reason: Optional[str]`. Defaults to None — no migration risk for existing tests.
- [ ] `request_approval_review(store, approval_id, reason, actor_id)` in `operations.py`: fills the 3 fields, creates an admin task ("approval_review_requested" type), writes an `approval_review_requested` audit event, returns the updated approval. Raises `ValueError("Approval not found")` if missing, `ValueError("Approval already decided")` if status != pending.
- [ ] `POST /approvals/{id}/request-review` in `main.py`: importer-or-admin auth; takes `ApprovalReviewRequest { reason: str }`; 404 on not found; 400 on already decided.
- [ ] Frontend `requestApprovalReview(approvalId, reason)` in `api.ts`.
- [ ] At least 5 backend tests: happy path, returned fields populated, audit event created, 404 unknown id, 400 already-decided.
- [ ] Total backend tests >= 241 (236 baseline + 5).
- [ ] `npm run build` clean.
- [ ] Plain English commit. No em dashes. No internal codenames.

## Files to touch
- `backend/app/models.py` — add 3 optional fields to `ApprovalRequest`; add `ApprovalReviewRequest` payload model.
- `backend/app/operations.py` — `request_approval_review`.
- `backend/app/main.py` — endpoint.
- `backend/tests/test_approval_request_review.py` — new tests.
- `frontend/src/api.ts` — client.
- `frontend/src/types.ts` — extend ApprovalRequest type with the 3 new fields.
- `HANDOVER.md` — move to DONE.

## Known risks / do-not-skip list
- Don't mutate the approval's `status`. Review-requested keeps the approval pending.
- Don't double-create the admin task: `create_admin_task` already idempotent on (booking, task_type, status=open). When an approval has no related_booking_id, skip the admin task and rely on the audit event + notification.
- Audit event metadata must include `reason` and `actor`.
- Frontend types: extending the existing inline `ApprovalRequestRecord` in `api.ts` with the 3 fields is enough; no need to refactor.

## Verification
1. `cd backend && python3 -m pytest tests/ -q` — expect 241+ passing.
2. `cd frontend && npm run build` — clean.

## Audit log

### AP1 — Plan audit (2026-05-11)

#### Lens 1 — Correctness
1. **Risky assumption?** That `create_admin_task` requires a Booking. Reading `operations.py:505` — yes, it takes a `Booking`. So when an approval has no related_booking_id, skip the admin task and rely on audit + notification. Plan updated.
2. **Weakest exit criterion?** "5 tests" — strengthen by including a test where the approval has NO related_booking_id (no admin task created).
3. **Domain expert difference?** Would emit a Sentinel event for high-amount escalations. Skip — not in scope.
4. **Leaving on the table?** No SLA/auto-escalation. Acceptable.
5. **Unintended consequence?** None observed. New fields are optional with None defaults.

#### Lens 2 — Adversarial (reviewer: senior FastAPI engineer who's seen escalation flows leak state)
1. **Wrong assumption?** That re-calling request-review on an already-review-requested approval is acceptable. Plan: allow it (just re-stamp the fields). The reason text is the only thing that changes.
2. **Weakest criterion?** "Audit event created" — strengthen to assert specific event_type and metadata keys.
3. **Domain expert?** Notify ops via SMS for high-value approvals. Skip — Sentinel is opt-in.
4. **Leaving on the table?** No "cancel review" endpoint. The plan-bookkeeping doesn't need it; if importer changes mind they can just approve/reject normally.
5. **Unintended consequence?** Front-end may need to render the review-requested state. The 3 new fields surface that; existing Approve/Reject buttons stay unchanged.

**Revisions applied:**
- Skip admin task when no related_booking_id; always create audit + notification.
- Test for re-calling on already-review-requested approval (re-stamp).
- Test that audit event has expected event_type and metadata keys.

### AP2 — Post-execution audit (2026-05-11)

#### Lens 1 — Correctness
1. **Wrong assumption?** None surfaced during execution. Imports, model fields, and helper signatures all matched my plan. The only real-time check that mattered: confirmed `create_admin_task` requires a `Booking`, so the no-booking path correctly skips that step.
2. **Weakest exit criterion?** "5 tests" — I shipped 7, including no-booking path and re-call/re-stamp.
3. **Domain expert difference?** None for this slice.
4. **Leaving on the table?** No "cancel review" endpoint, no SLA timer, no Sentinel SMS for high-value escalations. All deliberately out of scope.
5. **Unintended consequence?** Existing 228+8 tests continue to pass (now 243 total). No model field default change broke anything.

#### Lens 2 — Adversarial (reviewer: senior FastAPI engineer)
1. **Wrong assumption?** That the 400 vs 404 routing on `ValueError` is correct. Verified by reading the message text: `"Approval not found"` → 404, anything else → 400. Tests cover both paths.
2. **Weakest criterion?** Audit metadata schema — strengthened by asserting both `reason` and `actor` keys with expected values.
3. **Domain expert difference?** Would add rate-limiting to prevent abuse of repeated review-request calls. Acceptable for v1; in-memory store doesn't justify rate-limiting.
4. **Leaving on the table?** No frontend UI to surface the new state yet — the api client is ready, but the approvals list still doesn't render the review-requested badge. Will be addressed in the upcoming "Approval decision cards UI" item.
5. **Unintended consequence?** None observed.

#### Revisions applied
- None. Plan and execution aligned.

#### Exit criteria — final tick
- [x] 3 optional fields on `ApprovalRequest` — DONE
- [x] `request_approval_review` operation with admin-task + audit + notification — DONE
- [x] `POST /approvals/{id}/request-review` endpoint — DONE
- [x] Frontend api client + types — DONE
- [x] 7 backend tests pass; total 243 — DONE
- [x] Frontend builds clean — DONE
- [x] Plain English commit, no em dashes — see `Add request-review escalation endpoint for pending approvals`
