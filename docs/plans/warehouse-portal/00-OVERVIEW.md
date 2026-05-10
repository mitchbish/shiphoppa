# Warehouse portal

A token-link portal that lets the consolidation warehouse confirm cargo
receipt, record actual measurements, and upload supporting photos. Mirrors
the broker portal pattern (`BrokerAccessLink`, `/broker/{token}` endpoints,
`BrokerPortalView` component) which itself mirrors the supplier portal.

Goal in one sentence: remove the manual loop where the importer or admin
chases the warehouse for "did the cargo arrive, what were the dimensions,
is anything damaged" by giving the warehouse a self-serve URL that reads
from and writes to the shipment.

## Phases

1. **[Backend](01-backend.md)** — `WarehouseAccessLink` model + store slot,
   create/by-token operations, portal/receipt-confirmation/measurement/
   document endpoints, tests. Tier 2.
2. **[Frontend](02-frontend.md)** — warehouse portal page rendered for
   `/warehouse/:token`, "Invite warehouse" action on the cargo tab in Ship,
   copy-link UX, status refresh after warehouse confirms. Tier 2.

Both phases must pass full AP1 (Lens 1 + Lens 2) before phase 1 starts and AP2
(both lenses) before each phase is marked done.

## Success measure (AP3)

The Foshan or Tijuana warehouse can open `/warehouse/<token>`, see the
shipment's expected cargo (CBM, weight, package count), submit
"received" with actual CBM and weight, upload a cargo photo, and see the
shipment's `warehouse_received` event appear immediately on the importer's
tracking tab — all with no admin or importer keystrokes between them.

## Out of scope (do not start without explicit go-ahead)

- Carrier portal (next slice, separate plan)
- Multi-shipment warehouse dashboards (one link = one shipment, like supplier)
- Real-time GPS or scanner integration
- Damage claim workflow beyond a single notes field

## Audit log

Per-phase audit logs live in the phase docs. AP1 audits below.

#### Lens 1 — Correctness (2026-05-10 16:30 AEST)

(a) Likely-wrong assumption: that warehouse confirmation can fully ride on
    the existing `record_warehouse_measurement` operation. That operation
    is admin-authenticated. We need either to expose a token-authed thin
    wrapper, or write a parallel function. Wrapper is cleaner. Phase 1
    will pull the existing function's logic out and reuse it.
(b) Weakest exit criterion: AP3 success measure. The "appears immediately
    on the importer's tracking tab" claim isn't verifiable without a
    browser walk; flagged for user spot-check post-merge.
(c) Domain expert (3PL warehouse manager): would expect to also see
    pickup vs warehouse-receipt mode on the page. If the importer chose
    "ship hoppa pickup", the warehouse isn't receiving. Phase 1 portal
    response should include `delivery_mode` so the page can adapt.
(d) Leaving on the table: cargo damage workflow, partial-receipt support
    (some boxes missing), photo gallery. Out of scope; one notes field +
    one photo upload covers 80% of cases.
(e) Unintended consequence: warehouse confirms with a higher CBM than the
    booking estimate. The existing automation already creates an
    `approve_invoice_variance` approval at 10%+ — verify this still fires
    when the trigger comes from the warehouse portal vs admin.

#### Lens 2 — Adversarial (2026-05-10 16:33 AEST) — reviewer persona: a senior backend engineer reviewing PR diff cold

(a) Likely-wrong assumption: the broker portal plan worked, so warehouse
    will too with minimal change. The exception: warehouses can be on
    multiple shipments simultaneously (one warehouse, many bookings via
    `lane_id`). One-link-per-booking is correct here too (a warehouse
    confirms each cargo separately), but document this so future me
    doesn't try to add multi-link logic prematurely.
(b) Weakest criterion: doc-upload reuses `upload_document`. Already
    proven by broker portal. Reuse the same `actor_id="warehouse-portal"`
    pattern; tests assert that string.
(c) Domain expert (FastAPI engineer): broker + warehouse + supplier
    portal endpoints will start to look identical at the wiring level.
    Resist refactoring to a shared router until carrier portal lands.
    Premature for now.
(d) Leaving on the table: rate limiting on the public token endpoints.
    Same as broker portal. Will batch-fix when there are 3+ portals.
(e) Unintended consequence: when warehouse confirms receipt, it triggers
    `record_warehouse_measurement` which can create an approval request.
    Make sure the existing auto-advancement (booking status → loaded
    eventually) still fires, and the audit log captures
    `actor_id="warehouse-portal"`.

#### Plan revisions from AP1

- Phase 1 portal response includes `delivery_mode` so the UI can adapt
  to pickup vs warehouse-receipt mode.
- Phase 1 reuses `record_warehouse_measurement` via a thin token-auth
  wrapper that sets `actor_id="warehouse-portal"`.
- Phase 1 tests cover: link idempotency; expired token; portal returns
  expected cargo + delivery_mode; receipt confirmation creates
  warehouse_received event; CBM variance triggers approval (existing
  automation still fires); audit event records warehouse-portal.
- Phase 2 distinguishes pickup-mode (read-only "Ship Hoppa is collecting,
  no warehouse action needed") from receipt-mode (full form).
