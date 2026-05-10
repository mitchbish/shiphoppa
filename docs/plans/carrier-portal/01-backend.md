# Phase 1 — Backend (carrier portal)

Tier: 2.

## Goal

Carrier with a shipment-scoped link can read container/sailing info,
submit ETA updates, mark gate-in/departure/arrival events, and upload
the bill of lading.

## Exit criteria

- [ ] `CarrierAccessLink` model (mirror `BrokerAccessLink`, prefix `CRL`).
- [ ] `CarrierLinkCreate`, `CarrierEtaUpdate`, `CarrierEventUpdate`,
      `CarrierBookingSummary`, `CarrierPortalResponse` models.
- [ ] Store + persistence + reset path updated.
- [ ] `create_carrier_link`, `carrier_link_by_token`, `carrier_portal`,
      `carrier_eta_update`, `carrier_event_update` operations.
- [ ] ETA update reuses `update_container_eta` with
      `actor_id="carrier-portal"` and `source="carrier_portal"`.
      Returns 400 if booking has no container; returns 400 if booking
      status is `delivered`.
- [ ] Event update whitelists `loaded`, `departed`, `arrived`. Other
      stages → 400. Source: `forwarder_confirmation` (no
      `partner_update` enum yet — add to backlog).
- [ ] HTTP endpoints:
      - `POST /carrier-links` (admin)
      - `GET /carrier/{token}`
      - `POST /carrier/{token}/eta`
      - `POST /carrier/{token}/event`
      - `POST /carrier/{token}/documents`
- [ ] At least 7 tests in `tests/test_carrier_portal.py`:
      1. Idempotent link
      2. Unknown booking → 404
      3. Expired token → 404
      4. Portal returns container ETA
      5. ETA update triggers existing notify or approval (≥1 day delta;
         use a 3-day delta to also verify approval creation)
      6. Non-whitelisted event (e.g. `customs_cleared`) rejected with 400
      7. Doc upload records `uploaded_by_id="carrier-portal"`
- [x] Full suite green: 177 tests pass.

## Files

`models.py`, `store.py`, `operations.py`, `main.py`, `persistence.py`,
new `tests/test_carrier_portal.py`.

## Risks

- `update_container_eta` writes its own audit event; carrier portal
  wrapper writes a second `carrier_eta_update` audit event with
  `actor_id="carrier-portal"`. Don't duplicate the notify/approval
  side effects — the existing function handles both.
- Booking with no container_id (early-stage booking) → 400.
- Whitelist enforcement: don't allow carriers to set
  `customs_cleared` or `delivered` (those belong to broker / delivery
  trucker).

## Verification

`python3 -m pytest tests/ -q` green.

## Audit log

#### Lens 1 — Correctness (2026-05-10 17:48 AEST)

(a) Confirmed `update_container_eta(store, container_id, new_eta,
    actor_id, source)` exists (line 1179 of operations.py). I'll call
    it from the wrapper.
(b) Weakest exit: test #5 must use a real ETA delta that triggers BOTH
    notify AND approval thresholds. ETA_NOTIFY = 1 day, ETA_APPROVAL =
    3 day baseline. Test will set baseline, then submit an ETA 4 days
    later → triggers both.
(c) Domain expert: carrier ops would also want to set vessel name and
    voyage. Out of scope; current automation doesn't model those at
    container level. Backlog.
(d) Status whitelist: `loaded`, `departed`, `arrived` cover the carrier
    moments. Whitelist enforced at the operation level, returning
    `ValueError` → 400 in main.py.
(e) ETA update on delivered booking: `ValueError` raised, mapped to
    400 in main.py.

#### Lens 2 — Adversarial (2026-05-10 17:51 AEST) — reviewer persona: a senior backend engineer reviewing the third portal pattern

(a) Pattern is now established. Don't refactor in this slice. Note the
    refactoring opportunity in progress.md and stop.
(b) Test #5 will set the container's `baseline_estimated_arrival`
    explicitly to make the ≥3 day delta test deterministic.
(c) Event whitelist test: pick a stage clearly outside scope (e.g.
    `customs_cleared`) for the rejection test.
(d) BL upload: same `upload_document` call with
    `actor_id="carrier-portal"`. Test asserts.
(e) Audit emission: I'll add a `carrier_eta_update` audit event from
    the wrapper level, in addition to the audit `update_container_eta`
    writes.

#### Plan revisions

- Test #5 sets `baseline_estimated_arrival` explicitly to prove
  approval triggers.
- Event whitelist defined as a module-level frozenset for clarity.
- BL upload allows any DocumentType (not just `house_bill`); carrier
  may upload arrival notice or others.
