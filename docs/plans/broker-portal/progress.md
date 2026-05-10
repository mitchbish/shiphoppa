# Broker portal — progress

| Phase | Status | Audits | Notes |
|---|---|---|---|
| Overview | DONE | plan:2/2 post:0/2 | AP1 done. AP3 below. |
| 1 — Backend | DONE | plan:2/2 post:2/2 | 161 tests pass. Shipped 2026-05-10. |
| 2 — Frontend | DONE | plan:2/2 post:2/2 | Build clean. Live browser walkthrough deferred to user post-merge. |

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

## AP2 findings (resolved in scope)

- Phase 1: `release_hold_for_booking_and_kind` doesn't exist; real helper is
  `update_release_holds(store, booking)` which is condition-based. Test #6
  confirms only customs hold released, payment hold preserved.
- Phase 1: datetime offset bug (aware vs naive) caught and fixed before
  commit. Codebase is naive-only.
- Phase 1: audit-event assertion tightened to match exact event_type +
  actor_id rather than "last event".
- Phase 2: `BookingStatus` doesn't exist in frontend types; switched to
  `string` to match existing `Booking.status` field.

## AP3 — feature audit (2026-05-10 16:22 AEST)

#### Lens 1 — Correctness

The two phases together deliver the goal stated in 00-OVERVIEW.md: a broker
opens `/broker/<token>`, sees the customs profile / holds / docs / events,
posts a clearance update, uploads a document, and the importer sees the
update on next customs-tab open. Backend exit criteria fully ticked, frontend
exit criteria fully ticked. Both share the same data shape (`BrokerPortal
Response`), no drift between layers. Importer-side "Invite broker" lives in
the Deliver phase customs tab where the build plan said it should.

#### Lens 2 — Adversarial — reviewer persona: a project manager comparing the build plan to the shipped feature

The build-plan gap was "Brokers, warehouses, and carriers have no role-
specific UI or token-gated access. This blocks the partner collaboration
without new accounts promise." For brokers, that gap is closed. Warehouses
and carriers remain open — they're explicitly out of scope for this plan.

The browser walkthrough was deferred (autonomous overnight session), so the
"works in a real browser" claim is unverified. Build + types + the matching
supplier-portal pattern are strong proxies, but not equivalent. Flagged as
the single non-zero risk; user can spot-check post-merge.

No regressions in 161 backend tests. Frontend bundle grew ~11 kB JS / 2 kB
CSS — proportional to the new component and styles, no surprise weight.

#### AP3 findings to fix in scope

None. Browser spot-check is a post-merge user action.

## Follow-up backlog (out of scope for this plan)

- Browser walkthrough of broker portal page on staging/prod after merge.
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
