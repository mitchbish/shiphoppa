# Phase 1 — Backend

Tier: 2 (Standard — Launchpad-internal runtime, no tenant write).

## Goal

Add a token-link broker portal API that mirrors the supplier portal shape, so a
broker with a shipment-scoped link can read customs/holds/docs and post a
clearance update or upload a customs document.

## Exit criteria

- [x] `BrokerAccessLink` model defined and stored in `Store.broker_links`,
      with `id`, `booking_id`, `token`, `active`, `expires_at`, `last_used_at`,
      `created_at` fields, mirroring `SupplierAccessLink`.
- [x] `create_broker_link(store, booking_id)` returns active link if one exists
      for the booking, otherwise creates a new one. 45-day expiry. Audit event
      `broker_link_created` written.
- [x] `broker_link_by_token(store, token)` returns the link or raises
      `ValueError` for missing/expired/inactive tokens.
- [x] `broker_portal(store, token) -> BrokerPortalResponse` reads booking
      (with `importer_abn` and `importer_company_name` surfaced), customs
      profile, holds, recent events, and documents. Updates `last_used_at`
      on each call.
- [x] `broker_clearance_update(store, token, payload) -> BrokerPortalResponse`
      writes customs status (whitelist of `submitted`/`queried`/`cleared`
      only — `held` is admin-only and rejected with 400 if a broker submits
      it), optional `customs_entry_number`, optional duty/GST paid amounts
      (stored as informational fields on `CustomsProfile`, NEVER triggering
      payment-side automation), and optional broker notes. Logs a shipment
      event (`stage=customs_update`, `source_name="Broker portal"`) and an
      audit event. When status flips to `cleared`, releases ONLY the customs
      hold via the existing release-hold helper. Never blanket-releases —
      payment, document, or other holds must remain in place.
- [x] `broker_document_upload` endpoint reuses `upload_document` with
      `actor_role=ActorRole.system`, `actor_id="broker-portal"`. Doc type
      passed in by the broker (no implicit default; broker picks).
- [x] HTTP endpoints:
      - `POST /broker-links` (admin) — create link. Body: `{booking_id}`.
      - `GET /broker/{token}` (no auth, token = auth) — fetch portal.
      - `POST /broker/{token}/clearance` — submit clearance update.
      - `POST /broker/{token}/documents` — upload doc.
- [x] 8 new tests in `backend/tests/test_broker_portal.py` (exceeded the
      6-test target):
      1. Create broker link returns same link if called twice for same booking.
      2. Unknown booking returns 404 on link create.
      3. Expired token rejected with 404.
      4. `GET /broker/{token}` returns customs profile + holds + importer ABN.
      5. Clearance update flips customs status; audit event written with
         `actor_id="broker-portal"` and `event_type="broker_clearance_update"`.
      6. Broker-rejects-`held`-status returns 400.
      7. Doc upload via broker portal stores doc against booking with
         `uploaded_by_id="broker-portal"`.
      8. Status flip to `cleared` releases ONLY the customs hold; the
         payment hold remains active.
- [x] Full backend suite stays green: `python3 -m pytest backend/tests/`
      → 161 tests passing (153 prior + 8 new).

## Files to touch

- `backend/app/models.py` — add `BrokerAccessLink`, `BrokerLinkCreate`,
  `BrokerClearanceUpdate`, `BrokerBookingSummary`, `BrokerPortalResponse`.
- `backend/app/store.py` — register `broker_links` dict; clear in reset.
- `backend/app/operations.py` — add `create_broker_link`,
  `broker_link_by_token`, `broker_portal`, `broker_clearance_update`. Reuse
  existing `events_for_booking`, `documents_for_booking`,
  `release_hold_for_booking_and_kind` helpers.
- `backend/app/main.py` — wire 4 endpoints, import new ops, extend reset path.
- `backend/app/persistence.py` — extend snapshot/restore to include
  `broker_links` (mirror what's done for `supplier_links`).
- `backend/tests/test_broker_portal.py` — new test file (5 tests above).

## Known risks / do-not-skip list

- **Don't skip persistence.** If `broker_links` is missing from the snapshot
  serializer, broker links will silently disappear on restart. Test by
  triggering snapshot save/restore in a unit test, or at least mirror exactly
  what `supplier_links` does.
- **Audit events on every write.** Every clearance update and doc upload must
  produce an audit event with the broker-portal source so the importer and
  admin can see who did what.
- **Don't duplicate `upload_document`.** Reuse the existing function with
  `source="broker-portal"`. Adding a second path forks behavior and breaks
  search/filter.
- **Token expiry must be enforced.** The supplier portal raises `ValueError`
  for expired tokens; do the same. A "broker has been holding the link for 6
  months" attack vector is real.
- **No new release-hold types yet.** The customs hold already exists. Just
  release it when status hits `cleared`. Don't invent broker-specific holds in
  this phase — that's scope creep.
- **Re-run the full test suite, not just new tests.** New ops touching
  customs profile or holds can break existing automation tests; check.

## Verification

1. `cd backend && python3 -m pytest tests/ -q` — must end green with all
   prior tests + the 5 new ones.
2. `cd backend && uvicorn app.main:app --port 8001 &` then in another shell:
   ```
   ADMIN=shiphoppa-admin-dev
   BOOKING_ID=$(curl -s -H "Authorization: Bearer $ADMIN" \
     http://localhost:8001/bookings | python3 -c 'import sys,json; print(json.load(sys.stdin)[0]["id"])')
   LINK=$(curl -s -X POST http://localhost:8001/broker-links \
     -H "Authorization: Bearer $ADMIN" -H "Content-Type: application/json" \
     -d "{\"booking_id\":\"$BOOKING_ID\"}")
   TOKEN=$(echo $LINK | python3 -c 'import sys,json; print(json.load(sys.stdin)["token"])')
   curl -s http://localhost:8001/broker/$TOKEN | python3 -m json.tool | head -40
   ```
   Expected: a `BrokerPortalResponse` JSON with booking summary, customs
   profile, holds, events.
3. Submit a clearance update via:
   ```
   curl -s -X POST http://localhost:8001/broker/$TOKEN/clearance \
     -H "Content-Type: application/json" \
     -d '{"customs_status":"submitted","customs_entry_number":"E-12345"}' \
     | python3 -m json.tool | head -20
   ```
   Expected: customs profile in response shows `customs_status: "submitted"`
   and entry number propagated.
4. Stop the local uvicorn process.

## Audit log

#### Lens 1 — Correctness (2026-05-10 15:02 AEST)

(a) Likely-wrong assumption: that `release_hold_for_booking_and_kind` exists
    with that exact signature. The model docs say "release-hold mechanism"
    but I haven't grepped the function name. Signal of being wrong: import
    fails on first run. Mitigation: grep `release_hold` in operations.py
    before writing the call; pick the matching function name.
(b) Weakest exit criterion: test #1 (idempotent link creation). Could pass
    with a buggy implementation that returns the wrong link. Mitigation:
    test asserts the same `id` and `token` field — not just non-null.
(c) Domain expert (FastAPI engineer): would put the broker endpoints in a
    sub-router (`router = APIRouter(prefix="/broker")`) for clarity. Not
    doing this because supplier portal is also flat in main.py and we want
    parity for now. Trade-off: main.py grows; revisit when we add
    warehouse/carrier portals.
(d) Leaving on the table: `last_used_at` analytics — useful for ops to see
    which broker links are being used. The field is being recorded; surfacing
    it is phase 2 polish. Note in progress.md.
(e) Unintended consequence: `customs_status` enum has values like `held`
    that the broker shouldn't be able to set themselves (held usually means
    the importer or admin is blocking, not the broker). Tighten the
    whitelist: broker can set `submitted`/`queried`/`cleared`. `held` only
    via admin endpoint. Plan revision below.

#### Lens 2 — Adversarial (2026-05-10 15:05 AEST) — reviewer persona: a senior backend engineer who has cleaned up after multiple "we shipped a portal in a sprint" projects

(a) Likely-wrong assumption: the docs upload endpoint will Just Work.
    `upload_document` may need a content-type or file-bytes parameter the
    `DocumentUploadRequest` model doesn't have. Verify by reading
    `upload_document` signature before calling. Don't shortcut.
(b) Weakest criterion: "Audit events on every write." Audit events are
    easy to forget. Mitigation: add an explicit assertion in tests that
    `len(store.audit_events)` increases after each write op.
(c) Domain expert: would refuse to write the broker portal without rate
    limiting on the public token endpoints. Honest answer: I'm taking the
    parity-with-supplier-portal pass on this now, but progress.md notes a
    follow-up to add rate limiting once we have a third token-based portal
    (warehouse) — that'll make it worth a shared middleware.
(d) Leaving on the table: idempotency keys for clearance updates. If the
    broker double-submits, we get two audit events and possibly a duplicate
    shipment event. Acceptable for now (the customs status field doesn't
    accumulate). Note for follow-up.
(e) Unintended consequence: a clearance update that includes
    `duty_paid_amount` could be interpreted as a payment record by other
    automation (the landed-cost reconciler, for instance). Verify: store
    these as informational fields on the customs profile, NOT as payment
    records, and don't trigger payment-side automation. Plan revision below.

#### Plan revisions from AP1

- Whitelist: broker can set `submitted`/`queried`/`cleared` only. `held`
  remains an admin-only state.
- Pre-execution: grep `release_hold` to confirm exact function name; grep
  `upload_document` signature.
- Test #1 asserts same `id` AND same `token`.
- Test for `cleared`-releases-only-customs (already #6) tightened: assert
  payment hold remains in place.
- Add audit-events-grew assertion to clearance test.
- duty_paid/gst_paid stored as informational fields on `CustomsProfile`,
  NOT as payment records. No payment-side automation triggered.
- progress.md gets follow-up notes: rate limiting, idempotency keys,
  `last_used_at` UI surfacing.

#### Lens 1 — Correctness (2026-05-10 15:42 AEST, post-execution)

(a) Likely-wrong assumption checked: `release_hold_for_booking_and_kind`
    didn't exist. Real API was `update_release_holds(store, booking)`,
    which is condition-based (only releases customs when status is
    actually `cleared`). Discovered via grep before writing the call;
    swapped to the correct helper. Test #6 confirms the constraint is
    preserved (customs hold released, payment hold remains).
(b) Weakest exit criterion held up: test #1 asserts both `id` and `token`
    match across two POSTs to `/broker-links`. Passes.
(c) FastAPI engineer's note (from AP1): broker endpoints stayed flat in
    main.py rather than going into a sub-router. Mirrors supplier portal.
    Note kept on the follow-up backlog for when warehouse/carrier portals
    land and a shared sub-router is justified.
(d) Test #4 passes a value of `documents_required` for the customs status
    in the initial assertion — confirmed by reading the response. No
    surprises in default state.
(e) Customs status enum: I verified `held` is in the enum (so a broker
    sending it produces a real validation path) and that the 400 vs 404
    branching works. Test #6 (broker-rejects-held-status) confirms 400.

#### Lens 2 — Adversarial (2026-05-10 15:46 AEST, post-execution) — reviewer persona: a senior backend engineer reviewing the diff cold

(a) Datetime offset bug found and fixed: initial test used
    `datetime.now(timezone.utc)` against a codebase that uses naive
    `datetime.utcnow()`. Tests would have been comparing aware to naive
    and failing. Fixed by switching the test to `datetime.utcnow()`. Note
    for future: this codebase is naive-only; any aware datetime will blow
    up.
(b) Audit event assertion was initially over-constrained: test grabbed
    "the last audit event" but `update_release_holds` may write its own
    audit events. Tightened to assert there exists exactly one event
    matching the `broker_clearance_update` event_type with
    `actor_id="broker-portal"`. Robust to future changes.
(c) `forwarder_confirmation` SourceType used because no `partner_update`
    exists. Fits semantically (broker IS a forwarder/partner). Cleanest
    follow-up would be to add a `partner_update` enum value when we add
    warehouse/carrier portals. Logged on backlog.
(d) Doc upload endpoint reuses `upload_document` with
    `actor_id="broker-portal"` and `actor_role=ActorRole.system`. Test #7
    asserts the broker-portal origin survives. Same shape as supplier
    portal — no fork.
(e) Audit log: each clearance update writes one audit event of type
    `broker_clearance_update`. The 1-per-call assertion in test #5 also
    catches accidental double-writes if anything in `update_release_holds`
    or `update_booking_health` were to hook the same event_type.

#### AP2 findings to fix in scope

None blocking. Two follow-ups (already on backlog): rate limiting on
broker token endpoints; add `partner_update` SourceType when warehouse
or carrier portal lands.
