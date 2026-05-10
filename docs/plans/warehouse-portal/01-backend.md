# Phase 1 — Backend

Tier: 2.

## Goal

Add a token-link warehouse portal API mirroring the broker portal so a
warehouse with a shipment-scoped link can read expected cargo, confirm
receipt with actual measurements, and upload cargo photos.

## Exit criteria

- [x] `WarehouseAccessLink` model in `models.py`. Same shape as
      `BrokerAccessLink`. ID prefix `WHL`.
- [x] `WarehousePortalResponse`, `WarehouseBookingSummary`,
      `WarehouseReceiptUpdate`, `WarehouseLinkCreate` models added.
- [x] `Store.warehouse_links: Dict[str, WarehouseAccessLink]` registered.
      Persistence map and reset path updated.
- [x] `create_warehouse_link(store, booking_id) -> WarehouseAccessLink`
      idempotent per booking. 45-day expiry. Audit
      `warehouse_link_created`.
- [x] `warehouse_link_by_token(store, token)` raises `ValueError` for
      missing/expired/inactive tokens.
- [x] `warehouse_portal(store, token) -> WarehousePortalResponse` returns
      cargo expectations (CBM, weight, package count, ready date),
      `delivery_mode`, warehouse name from lane lookup, recent events,
      documents.
- [x] `warehouse_receipt_update(store, token, payload)` reuses
      `record_warehouse_measurement` with `actor_id="warehouse-portal"`,
      adds a `warehouse_received` shipment event, and writes a
      `warehouse_receipt_confirmed` audit event. Pickup-mode bookings
      raise `PermissionError` → HTTP 400.
- [x] `POST /warehouse-links` (admin), `GET /warehouse/{token}`,
      `POST /warehouse/{token}/receipt`, `POST /warehouse/{token}/documents`
      endpoints wired.
- [x] 8 new tests in `tests/test_warehouse_portal.py`:
      1. Idempotent link creation.
      2. Unknown booking → 404.
      3. Expired token → 404.
      4. Portal returns delivery_mode + expected cargo.
      5. Receipt confirmation creates `warehouse_received` event with
         `source_name="Warehouse portal"` AND a
         `warehouse_receipt_confirmed` audit event with
         `actor_id="warehouse-portal"`.
      6. CBM variance ≥10% creates `approve_invoice_variance` approval
         through the portal path (existing automation reused).
      7. Pickup-mode booking returns 400 from receipt endpoint with
         "ship hoppa pickup" in detail.
      8. Doc upload records `uploaded_by_id="warehouse-portal"`.
- [x] Full suite green: 169 tests pass (153 baseline + 8 broker + 8
      warehouse).

## Files to touch

- `backend/app/models.py`
- `backend/app/store.py`
- `backend/app/operations.py` — add ops near broker portal.
- `backend/app/main.py` — endpoints + reset clear.
- `backend/app/persistence.py` — `STORE_COLLECTION_MODELS`.
- `backend/tests/test_warehouse_portal.py` — new file.

## Known risks / do-not-skip list

- Don't bypass `record_warehouse_measurement` — it's the canonical path
  and triggers the variance approval. Calling it with the right
  `actor_id` keeps audit trails correct.
- Don't fabricate `delivery_mode` defaults. Read from `booking.delivery_mode`.
- Don't add a new SourceType. Reuse `warehouse_event` (which is what
  `record_warehouse_measurement` already uses).
- Audit event source = `"warehouse-portal"` so the importer can see who
  did what.

## Verification

1. `python3 -m pytest tests/ -q` — green.
2. Cross-check: a test that calls the portal receipt endpoint with a
   CBM 15% larger than estimate sees `approve_invoice_variance` in
   `store.approval_requests`.

## Audit log

#### Lens 1 — Correctness (2026-05-10 16:38 AEST)

(a) Likely-wrong: that `record_warehouse_measurement` accepts
    `actor_id` as a string. Phase 1 will grep its signature first.
    Existing call site at `main.py` line ~954 passes `principal.actor_id`
    so the param exists.
(b) Weakest exit: test #6 (variance triggers approval). Easy to write
    a test that asserts the function was called rather than the side
    effect. Tighten: assert `store.approval_requests` has a new entry
    of type `approve_invoice_variance` after the receipt POST.
(c) Domain expert: would also want a "no, this isn't right" path —
    warehouse received fewer/wrong items. Out of scope for this slice;
    notes field handles 80%, follow-up later.
(d) Leaving on the table: damage flagging, photo gallery, multi-line
    receipt notes. Single notes + single document upload is enough.
(e) Unintended consequence: if the booking is in pickup mode (Ship
    Hoppa pickup, not warehouse), this portal shouldn't write a
    receipt event. Phase 1 must reject the receipt POST with 400
    when `delivery_mode == ship_hoppa_pickup`.

#### Lens 2 — Adversarial (2026-05-10 16:41 AEST) — reviewer persona: senior backend engineer

(a) Reuse `record_warehouse_measurement` is the right call. Watch out:
    that function might write its own audit events with a different
    actor_id. Verify by reading it before writing the wrapper, and
    if needed write the audit at the wrapper layer in addition.
(b) Weakest criterion held up by tightening the assertion target.
(c) Domain expert: would refuse to ship without rate limiting. Same
    note as broker. Backlog.
(d) Idempotency on receipt POST. If warehouse double-clicks, do we
    create duplicate events? Reuse the existing function's behavior
    (probably already idempotent at the booking level).
(e) Pickup-mode rejection: 400 with a clear message
    ("This shipment is on Ship Hoppa pickup. The warehouse portal is
    not used.") — important for UX.

#### Plan revisions

- Test #5 also asserts `actor_id="warehouse-portal"` in the most
  recent matching audit event.
- Receipt endpoint returns 400 with a clear detail message when
  `delivery_mode == ship_hoppa_pickup`.
- Add test #7: pickup-mode booking rejects the receipt POST with 400.
- Pre-execution: read `record_warehouse_measurement` source, check
  audit emission and signature.

#### Lens 1 — Correctness (2026-05-10 17:14 AEST, post-execution)

(a) Confirmed `record_warehouse_measurement` accepts `actor_id` as a
    keyword. Reused as planned. The function emits its own
    `warehouse_measurement_recorded` audit event AND I add a separate
    `warehouse_receipt_confirmed` event from the wrapper, so audit
    trail captures both the measurement and the portal confirmation.
(b) DeliveryMode enum has only two values (`ship_hoppa_pickup`,
    `self_delivery`). Initial test used `warehouse_drop` which doesn't
    exist (422). Caught immediately, fixed with `self_delivery`.
(c) Pickup-mode rejection works as planned: `PermissionError` raised in
    operation, caught in main.py, returned as 400 with clear message.
    Test #7 confirms.
(d) Variance test #6 confirms existing automation still fires through
    the portal path. The booking has 20 CBM estimate; submitting 24.5
    CBM is 22.5% variance, well above the 10% threshold, so an
    `approve_invoice_variance` approval is created.
(e) `warehouse_portal` calls `warehouse_for_lane` to surface the
    warehouse name. Booking without a lane gets `warehouse_name=None`,
    handled gracefully.

#### Lens 2 — Adversarial (2026-05-10 17:18 AEST, post-execution) — reviewer persona: a senior backend engineer reviewing the diff cold

(a) `_warehouse_portal_response` is parallel to
    `_broker_portal_response`. Could refactor to a shared partner-
    portal helper, but premature with two consumers. Wait for carrier
    portal as the third trigger.
(b) The receipt endpoint's `PermissionError` is a Python builtin —
    `HTTPException(400)` mapping is explicit and readable. No mistake
    where a `ValueError` could leak through.
(c) Test #6 catches the variance trigger by asserting on
    `store.approval_requests`. If `record_warehouse_measurement`
    changes its threshold logic, the test will catch it (it's
    assertion-tight on the side effect).
(d) `link.last_used_at` is updated on receipt confirmation. Future
    rate-limiting or last-active analytics will have data.
(e) Documents endpoint reuses `upload_document` with
    `actor_id="warehouse-portal"`. Same pattern as broker.

#### AP2 findings to fix in scope

None blocking. One follow-up note added: the wrapper-level audit
event duplicates information already in
`warehouse_measurement_recorded`. Acceptable trade-off — the source
field on the additional event makes "who did this" obvious in the
audit log.
