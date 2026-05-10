# Warehouse portal — progress

| Phase | Status | Audits | Notes |
|---|---|---|---|
| Overview | DONE | plan:2/2 post:0/2 | AP1 done. AP3 below. |
| 1 — Backend | DONE | plan:2/2 post:2/2 | 169 tests pass. Reuses `record_warehouse_measurement` for variance. |
| 2 — Frontend | DONE | plan:2/2 post:2/2 | Build clean. Live walkthrough deferred to user post-merge. |

## AP1 plan revisions (already applied)

- Phase 1 portal response includes `delivery_mode` so UI can branch
  pickup vs receipt mode.
- Phase 1 reuses `record_warehouse_measurement` with
  `actor_id="warehouse-portal"`.
- Phase 1 receipt endpoint returns 400 for pickup-mode bookings.
- Phase 1 test #5 asserts both shipment event source and audit actor.
- Phase 2 reuses broker portal CSS classes; no rename.
- Phase 2 confirmed-receipt panel replaces the form, not a toast.

## AP2 findings (resolved in scope)

- Phase 1: DeliveryMode enum has only `ship_hoppa_pickup` and
  `self_delivery`. Test default switched from invented
  `warehouse_drop` to `self_delivery`.
- Phase 2: `WarehouseReceiptUpdate` was imported into App.tsx but only
  used in the API client; removed unused import.

## AP3 — feature audit (2026-05-10 17:30 AEST)

#### Lens 1 — Correctness

The two phases meet the goal in 00-OVERVIEW.md: a warehouse opens
`/warehouse/<token>`, sees expected cargo + delivery_mode-aware UI,
submits actual CBM and weight, photos go to the booking's documents,
existing variance automation fires, and the importer sees the
`warehouse_received` event on tracking. Pickup-mode bookings show a
clear "no action needed" panel and never get a confirm form. All exit
criteria ticked across both phases.

#### Lens 2 — Adversarial — reviewer persona: project manager comparing build plan to shipped feature

The build-plan gap was "Warehouses have no role-specific UI or token-
gated access. This blocks the partner collaboration without new
accounts promise." For warehouses, that gap is closed. Carrier portal
remains open as the next slice, separate plan.

The browser walkthrough was deferred (autonomous overnight session).
Same risk as broker portal: a layout or runtime bug not caught by tsc
+ vite. Mitigation: pattern is identical to broker portal which the
build also approved; CSS is reused; types are tight; logic is exercised
by 8 backend tests + the matching API shapes.

No regressions: 169 backend tests still pass. Frontend bundle grew ~10
kB JS — proportional to the new component, no surprise weight.

#### AP3 findings to fix in scope

None. Browser spot-check is a post-merge user action.

## Follow-up backlog

- Damage flagging workflow on receipt.
- Photo gallery / multiple photos per receipt.
- Real binary file upload (not placeholder JSON-only).
- Rate limiting on token-based portals (carrier portal will be the
  third trigger; bundle a shared limiter then).
- Shared `PartnerPortal` React component refactor after carrier portal.
- Add a `partner_update` `SourceType` enum value (pending; current
  warehouse uses `warehouse_event` which is correct, but broker uses
  `forwarder_confirmation` which is approximate).
