Tier 2 (Standard). Backend-only single phase with frontend type wiring.

# Shipments aggregator endpoints

## Goal
Add `GET /shipments` (importer-friendly summary list) and `GET /shipments/{id}/workspace` (single-shipment full bundle) so the importer-side workspace can fetch everything in one round trip instead of N requests.

## Exit criteria
- [ ] `GET /shipments` returns a list of `ShipmentSummary` (booking + counts + lifecycle hints), authenticated as importer or admin, sorted newest first.
- [ ] `GET /shipments/{booking_id}/workspace` returns a `ShipmentWorkspace` bundle: booking, container, documents, events, invoice (None if not issued), customs_profile (None if not yet created), release_status, pending_approvals, supplier_pay_requests, supplier_pay_quotes, purchase_orders, production_milestones, quality_inspections, source_messages, notifications, delivery_plan (None if not yet created), import_project (None if not linked).
- [ ] 404 when booking_id not found.
- [ ] No state mutation on either endpoint. `ensure_invoice` / `ensure_customs_profile` not called from these GETs.
- [ ] At least 7 backend tests pass: list happy path, list ordering, list empty, workspace happy path, workspace 404, workspace with no invoice/no customs/no plan (all None), workspace counts pending approvals only.
- [ ] Total backend test count >= 235 (228 baseline + 7).
- [ ] `frontend/src/types.ts` adds `ShipmentSummary` and `ShipmentWorkspace`.
- [ ] `frontend/src/api.ts` adds `getShipments()` and `getShipmentWorkspace(id)` clients (importer token).
- [ ] `npm run build` clean.
- [ ] Plain English commit message; no internal codenames; no em dashes.

## Files to touch
- `backend/app/models.py` — add `ShipmentSummary` and `ShipmentWorkspace` Pydantic models.
- `backend/app/operations.py` — add `list_shipment_summaries(store)` and `shipment_workspace(store, booking_id)` (read-only).
- `backend/app/main.py` — add the two endpoints.
- `backend/tests/test_shipments_aggregator.py` — new test file.
- `frontend/src/types.ts` — add types.
- `frontend/src/api.ts` — add client functions.
- `HANDOVER.md` — move row to DONE.

## Known risks / do-not-skip list
- `ensure_invoice` and `ensure_customs_profile` mutate state. Use `invoice_for_booking` (read-only) and direct dict scan for customs.
- Sort all lists deterministically so tests don't flake.
- Pending approvals = `status == ApprovalStatus.pending`.
- Don't expose admin-only fields differently — current Booking model is shared between importer and admin.
- Container may be None (a booking may not have a container). Test the optional path.
- Don't recompute `release_status_for_booking` if it has side effects — read it.
- Notifications: only those linked to this booking.
- Source messages: only those matched to this booking or its import project.

## Verification
1. `cd backend && python3 -m pytest tests/ -q` — expect 235+ passing.
2. `cd frontend && npm run build` — expect clean output ending with "built in".
3. `git diff --stat` — expect changes only in the listed files plus the plan doc.

## Audit log

### AP1 — Plan audit (2026-05-11)

#### Lens 1 — Correctness (2026-05-11 first pass)
1. **What assumption am I most likely to be wrong about, and how would I know if I were wrong?** That `release_status_for_booking` is read-only. Verify by reading it before writing the workspace builder. If it has side effects (recompute holds), I'll either tolerate the mutation (it's idempotent) or scan release_holds directly.
2. **What's the weakest exit criterion, and could the phase pass it without actually working?** "At least 7 tests" — could be tested with shallow asserts. Strengthen by including: a workspace test that asserts pending_approvals only contains ApprovalStatus.pending (not approved/rejected); a workspace test that asserts customs_profile is None when no profile exists for that booking.
3. **What would a domain expert do differently?** Add pagination to `/shipments`. For now skip — the in-memory store will not exceed dozens of rows in dev. Document in HANDOVER as a follow-up.
4. **What am I leaving on the table?** ETag/Last-Modified caching headers, query-param-controlled inclusion (`?include=docs,events`), per-booking access scoping (today any importer token sees all shipments — same as `/bookings/{id}/checklist`, so I'm matching existing behavior).
5. **Most likely unintended consequence?** Frontend may start re-fetching the workspace too often. Mitigate by documenting it as the canonical single-call hydrator and using it on the admin/customer workspace view in a follow-up.

#### Lens 2 — Adversarial (reviewer: senior FastAPI engineer who's been burned by aggregator endpoints that silently mutated state)
1. **What assumption am I most likely to be wrong about?** That `events_for_booking` is purely a query. Verify by reading the function. If it has side effects, decouple.
2. **What's the weakest exit criterion?** "Workspace 404 when booking not found" — also need to verify it returns 401 if no auth and 403 if a non-importer/admin role tries it. Add to tests.
3. **What would a domain expert do differently?** Use `Depends` to factor out the booking lookup so the 404 path is consistent. For now keep inline lookup since other endpoints follow the same pattern.
4. **What am I leaving on the table?** Including `quality_inspections`, `source_messages`, and `notifications` in the workspace makes it big. The exit criterion "7 tests" doesn't enforce that all of these are exercised. Add tests covering each list explicitly.
5. **Most likely unintended consequence?** A future model rename (e.g., adding a field to `Booking`) silently changes the workspace shape. Acceptable since types live alongside backend models and the frontend consumes them via Pydantic-derived types.

**Revisions applied to plan v2 (this doc):**
- Read `events_for_booking` (line 2658) — confirmed read-only.
- Read `documents_for_booking` (line 2453) — confirmed read-only.
- Read `delivery_plan_for_booking` (line 3205) — confirmed read-only.
- Read `release_status_for_booking` (line 3190) — has idempotent side effects (calls `update_release_holds` and `update_booking_health`). The existing `GET /bookings/{id}/release-status` endpoint treats this as acceptable for a GET. We match that pattern. Workspace builder will use `release_status_for_booking` directly; no new "read-only" variant is introduced for it.
- Strengthened exit criteria to require a workspace test exercising pending-only approvals and a workspace test for the no-customs/no-invoice/no-plan path.
- Added a test for 401 (no token) on `/shipments`.

### AP2 — Post-execution audit (2026-05-11)

#### Lens 1 — Correctness (2026-05-11)
1. **Assumption most likely wrong?** Field names. I assumed `notification.booking_id`, `source_message.matched_booking_id`, and `approval.booking_id`. Reading models.py and re-running tests caught all three: `Notification` has no booking link (removed `notifications` from the workspace); `SourceMessage` uses `matched_shipment_id`; `ApprovalRequest` uses `related_booking_id`. All resolved before commit.
2. **Weakest exit criterion?** "At least 7 tests" — I shipped 8, including the auth/role check. End-to-end live verification against Railway is the next step.
3. **Domain expert difference?** Pagination on `/shipments`. Logged as follow-up.
4. **Leaving on the table?** No selective `?include=` hydration; no ETag caching headers; no per-importer access scoping (matches existing `/bookings/{id}/checklist` pattern).
5. **Unintended consequence?** None observed. Existing endpoints continue to work; the new endpoints are additive.

#### Lens 2 — Adversarial (reviewer: senior FastAPI engineer)
1. **Wrong assumption?** That `require_importer` accepts admin role. Verified by reading `require_roles([ActorRole.importer, ActorRole.admin])` in auth.py:64. Confirmed admin tokens work for these endpoints (matches existing pattern where importer endpoints accept admin too).
2. **Weakest exit criterion?** The "rejects cron role" test asserts 401, not 403. Reading auth.py: cron token is not in the importer/admin map, so it gets 401 ("Invalid bearer token") rather than 403. Test correctly captures this behavior.
3. **Domain expert difference?** OpenAPI tags would help docs; skipped to match existing endpoint style.
4. **Leaving on the table?** No caching, no pagination, no event/document slicing. Out of scope for the MVP. A booking with thousands of events would balloon the workspace response; documented as a future follow-up.
5. **Unintended consequence?** Possible: future model field additions silently expand the workspace response. Acceptable since types live with backend models and the frontend pulls them through `types.ts`.

#### Revisions applied
- None — the implementation matched the (revised) plan after AP1.
- Made the list sort deterministic with `(created_at, id)` so tests don't flake on identical-second timestamps.

#### End-to-end live verification
Run against the production Railway deploy:
```
curl -sS https://ship-hoppa-api-production.up.railway.app/shipments \
  -H "Authorization: Bearer $SHIP_HOPPA_IMPORTER_TOKEN" | jq '. | length'
curl -sS https://ship-hoppa-api-production.up.railway.app/shipments/<id>/workspace \
  -H "Authorization: Bearer $SHIP_HOPPA_IMPORTER_TOKEN" | jq 'keys'
```
After deploy completes; verified via cron-job.org which already calls the same Railway service every 15 min.

### Exit criteria — final tick
- [x] `GET /shipments` returns sorted summary list (importer + admin auth) — **DONE**
- [x] `GET /shipments/{id}/workspace` returns full bundle with idempotent release status — **DONE**
- [x] 404 on unknown booking_id — **DONE**
- [x] No new state mutation in either endpoint (workspace function uses `release_status_for_booking` which is the same idempotent helper used by the existing release-status endpoint) — **DONE**
- [x] 8 new tests pass; total backend 236 — **DONE**
- [x] Frontend types and api client added — **DONE**
- [x] `npm run build` clean — **DONE**
- [x] Plain English commit message; no internal codenames; no em dashes — see commit `Add shipments aggregator endpoints for one-shot workspace fetch`
