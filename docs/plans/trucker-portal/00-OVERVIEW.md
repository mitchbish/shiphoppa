# Trucker / courier portal

Token-link portal for the destination trucker (or courier) handling
the final-mile delivery. Mirrors broker / warehouse / carrier portals.

## Phases

1. **Backend** — `TruckerAccessLink`, status updates, POD upload, tests.
   Tier 2.
2. **Frontend** — deferred to follow-up; backend ships first so the
   API contract is stable before the UI lands. (Same staging pattern
   was used for email ingestion.)

## Backend exit criteria

- `TruckerAccessLink` model + `Store.trucker_links` slot + persistence.
- `create_trucker_link`, `trucker_link_by_token`, `trucker_portal`,
  `trucker_status_update`, `trucker_pod_upload` operations.
- `POST /trucker-links` (admin), `GET /trucker/{token}`,
  `POST /trucker/{token}/status`, `POST /trucker/{token}/pod`.
- Status whitelist: `pickup_scheduled`, `picked_up`, `delivered`.
  Trucker cannot mark `delivered` if release status is `blocked` —
  return 400 with the holds list.
- POD upload reuses `upload_document` with type `delivery_order` and
  `actor_id="trucker-portal"`.
- 7 tests:
  1. Idempotent link
  2. Unknown booking → 404
  3. Expired token → 404
  4. Portal returns delivery profile + release status
  5. Status update creates shipment event with
     `source_name="Trucker portal"`
  6. Marking delivered while release blocked returns 400 + lists holds
  7. POD upload records `uploaded_by_id="trucker-portal"`

## Out of scope

- Frontend trucker view (follow-up).
- Real-time GPS tracking.
- Driver vehicle / license capture.
- Multi-stop / partial-load support.

## AP1 audits

#### Lens 1 — Correctness (2026-05-11 10:35 AEST)

(a) Likely-wrong: that release-status check uses
    `release_status_for_booking`. Confirmed; the function exists.
(b) Weakest exit: test #6. Tighten by asserting the response
    contains the active hold types so the trucker sees what's
    blocking.
(c) Domain expert (final-mile dispatcher): would also want to flag
    delivery exceptions (consignee not present, refused). For now,
    the notes field on the status update covers it.
(d) Out of scope: signature capture (placeholder POD upload only).
(e) Trucker should be able to upload POD even before delivered
    status — pre-delivery photo of cargo handover. Allow regardless
    of status.

#### Lens 2 — Adversarial (2026-05-11 10:38 AEST) — reviewer persona: a backend engineer reviewing the fourth portal in a row

(a) Pattern fully established. Carbon-copy with delivery-specific
    fields. Don't refactor yet.
(b) Status whitelist as a frozenset. Test #6 covers blocked-delivery
    rejection with hold info.
(c) Existing `mark_delivery_delivered` operation might already exist —
    look for it before forking. (If yes, reuse with
    actor_id="trucker-portal".)
(d) Idempotency on status updates: same-stage duplicate is allowed;
    creates a new event each call. Acceptable.
(e) POD upload doesn't auto-mark delivered. The trucker submits
    status separately. UX clarity: keep them distinct.

#### Plan revisions

- If `mark_delivery_delivered` exists, reuse it. Otherwise create a
  similar wrapper.
- Test #6 asserts hold list in response detail.
- Test status whitelist: a non-allowed stage (e.g. `customs_cleared`)
  returns 400.
