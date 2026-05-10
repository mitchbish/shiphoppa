# Carrier portal

Token-link portal for the ocean / road carrier. They open the URL,
confirm the booking, push ETA updates, mark gate-in / departure /
arrival events, and upload the bill of lading. Mirrors broker and
warehouse portals.

## Phases

1. **[Backend](01-backend.md)** — `CarrierAccessLink`, ETA update via
   existing `update_container_eta`, event creation, document upload,
   tests. Tier 2.
2. **[Frontend](02-frontend.md)** — `/carrier/:token` standalone view,
   ETA + event forms, BL upload. "Invite carrier" on Sailings tab.
   Tier 2.

## Success measure (AP3)

A test carrier opens `/carrier/<token>`, sees the booking's container,
sailing window, and current ETA, submits a new ETA, and sees both:
(a) the existing `update_container_eta` automation fires (notification
to importer if delta ≥1 day, approval if ≥3 day baseline slip), AND
(b) the importer's tracking tab reflects the new ETA on next refresh.

## Out of scope

- Carrier-level dashboards (one carrier, many bookings).
- Live AIS / vessel tracking integration.
- Pricing / rate negotiation.

## AP1 audits

#### Lens 1 — Correctness (2026-05-10 17:38 AEST)

(a) Likely-wrong: that carrier ETA updates can flow through the
    existing per-container `update_container_eta` cleanly. Need to
    look up the booking's `container_id` and pass it. If the booking
    has no container yet (pre-confirmation), the ETA endpoint should
    400 with a clear message.
(b) Weakest exit: AP3 success measure depends on importer-side
    rendering. Build + types verify the API contract; user spot-check
    post-merge for the rendered tracking tab.
(c) Domain expert (carrier ops): would also want to mark "vessel
    delayed by typhoon" with a note. Add an optional `note` field to
    the ETA update.
(d) Leaving on the table: ETD updates (only ETA right now). Out of
    scope; current automation handles ETA only.
(e) Unintended consequence: a carrier with a stale link could push
    inaccurate ETA after the cargo is already delivered. Mitigation:
    if booking status is `delivered`, reject ETA updates with 400.

#### Lens 2 — Adversarial (2026-05-10 17:42 AEST) — reviewer persona: senior backend engineer reviewing a third portal in a row

(a) The three portal patterns are now nearly identical. Resist
    extracting a shared module — there are subtle per-role
    differences. After this third portal, evaluate a refactor as a
    separate slice if it would actually reduce code (carrier sets
    ETA, broker sets customs status, warehouse sets measurements —
    not a clean abstraction).
(b) ETA must be a proper date (not datetime, not string). Pydantic
    will catch wrong types via 422. Test with a malformed ETA to
    confirm.
(c) Event creation: carriers should be able to submit `loaded`,
    `departed`, `arrived` events. Whitelist these explicitly; reject
    others with 400.
(d) BL upload: reuse `upload_document` with type `house_bill`.
    `actor_id="carrier-portal"`.
(e) Rate limiting still pending. Bundle with the partner-portal
    refactor as a shared concern after this slice.

#### Plan revisions

- Phase 1 ETA endpoint requires booking to have `container_id`;
  returns 400 if not.
- Phase 1 ETA endpoint optionally accepts a `note` field; includes
  in audit event.
- Phase 1 event endpoint whitelists `loaded`, `departed`, `arrived`;
  rejects others with 400.
- Phase 1 ETA endpoint rejects with 400 if booking status is
  `delivered`.
- Phase 1 tests cover: idempotent link; expired token; portal returns
  container info; ETA update via portal triggers existing notify /
  approval; non-whitelisted event rejected; doc upload records
  carrier-portal origin; ETA on delivered booking rejected.
