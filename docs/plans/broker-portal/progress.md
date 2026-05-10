# Broker portal — progress

| Phase | Status | Audits | Notes |
|---|---|---|---|
| Overview | DONE | plan:2/2 post:0/2 | AP1 complete 2026-05-10 14:55-14:58 AEST. AP3 deferred until phase 2 ships. |
| 1 — Backend | DONE | plan:2/2 post:2/2 | AP1 complete 2026-05-10 15:02-15:05. Code shipped. AP2 complete 15:42-15:46. 161/161 tests pass. |
| 2 — Frontend | NOT STARTED | plan:2/2 post:0/2 | AP1 complete 2026-05-10 15:08-15:11. Ready to execute. |

## AP1 plan revisions (applied to phase docs)

- Broker can set `submitted`/`queried`/`cleared` only. `held` rejected with 400.
- Phase 1 portal response surfaces `importer_abn` and `importer_company_name`.
- `cleared` status releases ONLY the customs hold. Other holds untouched.
- duty_paid/gst_paid stored as informational fields on `CustomsProfile`. No
  payment-side automation triggered.
- Phase 1 test #6 added: cleared releases only customs, payment hold remains.
- Phase 2 surfaces `queried` with required note.
- Phase 2 clipboard fallback: visible, selectable URL field next to toast.
- Phase 2 drift detection: re-fetch on submit, warn if customs profile changed.
- Phase 2 verification adds mobile-width walkthrough.
- Phase 1 verification: grep `release_hold` and `upload_document` signatures
  before writing the calls.

## AP2 phase 1 findings (resolved in scope)

- Datetime offset bug in test (aware vs naive) caught and fixed before commit.
  Codebase is naive-only; future portal tests should use `datetime.utcnow()`.
- Audit-event assertion tightened: must match exact event type +
  `actor_id="broker-portal"`, not "last event" — robust to release-holds
  or booking-health hooks adding their own audit events.
- `release_hold_for_booking_and_kind` doesn't exist in this codebase. Real
  helper is `update_release_holds(store, booking)`, which is condition-based
  and naturally only releases the hold whose underlying state has flipped.
  Test #6 confirms only customs hold released, payment hold preserved.

## Follow-up backlog (out of scope for this plan, do not execute)

- Broker email/SMS notifications when invited and when importer adds info.
- Multi-shipment broker dashboard (one broker, many shipments).
- Rate limiting on token-based portals (worth doing once we have 3+ portals).
- Idempotency keys on clearance updates.
- `last_used_at` analytics surfacing for ops.
- Extract shared `PartnerPortal` component when warehouse portal lands.
- In-portal broker→importer chat primitive.
- i18n for broker portal (Mandarin in particular for Chinese-side brokers).
- Add a `partner_update` `SourceType` enum value when warehouse/carrier
  portals land. Phase 1 used `forwarder_confirmation` as the closest fit.
