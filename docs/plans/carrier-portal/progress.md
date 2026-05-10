# Carrier portal — progress

| Phase | Status | Audits | Notes |
|---|---|---|---|
| Overview | DONE | plan:2/2 post:0/2 | AP1 done. AP3 below. |
| 1 — Backend | DONE | plan:2/2 post:2/2 | 177 tests pass. Reuses `update_container_eta` for notify+approval. |
| 2 — Frontend | DONE | plan:2/2 post:2/2 | Build clean. Live walkthrough deferred. |

## AP1 plan revisions (applied)

- Phase 1 ETA endpoint requires `container_id`; rejects with 400 if missing.
- Phase 1 ETA endpoint rejects with 400 when booking status is `delivered`.
- Phase 1 event endpoint whitelists `loaded`, `departed`, `arrived`.
- Phase 1 ETA test sets baseline + 4-day delta to deterministically trigger
  approval threshold.
- Phase 1 documents endpoint accepts any DocumentType (BL, arrival notice).

## AP2 phase 1 findings (resolved)

- The variance approval type is `accept_sailing_change` (not `approve_*`).
  Test #5 fixed.
- The container has multiple bookings (seed has BKG-ANCHOR plus the new
  one). Test asserts only on the approval matching `related_booking_id`.

## AP2 phase 2 findings

- Frontend pattern reused unchanged from broker/warehouse. Same risks
  and mitigations apply. Browser walkthrough deferred to user post-merge.

## AP3 — feature audit (2026-05-10 18:18 AEST)

#### Lens 1 — Correctness

Carrier portal closes the third leg of the partner-portal gap from the
build plan. End-to-end flow: admin issues link via "Invite carrier" on
Sailings tab; carrier opens `/carrier/<token>`; sees container/sailing/
ETA; submits new ETA which triggers existing notify (≥1 day delta) and
approval (≥3 day baseline slip); marks loaded/departed/arrived which
creates shipment events; uploads BL document. All visible to importer
on next refresh.

#### Lens 2 — Adversarial — reviewer persona: project manager comparing build plan to shipped feature

The build-plan gap "Brokers, warehouses, and carriers have no role-
specific UI" is now fully closed for all three partners. With three
near-identical portal patterns shipped, the next backlog item is a
shared `PartnerPortal` refactor — but doing it now would block on
nothing while delivering nothing new. Defer.

177 tests, frontend builds clean, no regressions.

## Follow-up backlog

- Shared `PartnerPortal` React component refactor (now warranted with
  three concrete consumers).
- Add `partner_update` SourceType enum value (broker, carrier use
  `forwarder_confirmation` as approximation).
- Rate limiting on token-based portals.
- Carrier dashboard (one carrier, many bookings).
- Vessel name + voyage update support from carrier portal.
- Browser spot-check post-merge.
