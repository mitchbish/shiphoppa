# Broker portal

A token-link portal that lets the customs broker assigned to a shipment view the
customs profile, holds, documents, and timeline; submit a clearance status
update; and upload customs documents. Mirrors the existing supplier portal
pattern (`SupplierAccessLink`, `/supplier/{token}` endpoints, `SupplierPortal`
UI).

Goal in one sentence: remove the manual chase loop where the importer or admin
keeps emailing the broker to ask "where's the entry, what's the duty, when do
we clear" by giving the broker a self-serve URL that reads from and writes to
the shipment.

## Phases

1. **[Backend](01-backend.md)** — `BrokerAccessLink` model + store slot,
   create/by-token operations, portal/clearance/document endpoints, tests. Tier 2.
2. **[Frontend](02-frontend.md)** — broker portal page rendered for `/broker/:token`,
   "Invite broker" action on the customs tab in Deliver, copy-link UX, status
   refresh after broker submits. Tier 2.

Both phases must pass full AP1 (Lens 1 + Lens 2) before phase 1 starts and AP2
(both lenses) before each phase is marked done.

## Success measure (AP3)

A test broker can open `/broker/<token>`, see the shipment's customs profile,
submit a "submitted" status with an entry number, see it land in the importer
view, and upload a customs declaration that appears in shipment documents —
all with no admin or importer keystrokes between them.

## Out of scope (do not start without explicit go-ahead)

- Warehouse portal, carrier portal (next slices, separate plans)
- Live ABF / US tariff connectors (separate gap)
- Broker-specific authentication beyond a token link
- Multi-shipment broker dashboards (one link = one shipment, like supplier)

## Audit log

Audits for the overview itself (cross-phase coherence, scope, naming).
Per-phase audit logs live in the phase docs.

#### Lens 1 — Correctness (2026-05-10 14:55 AEST)

(a) Likely-wrong assumption: that mirroring the supplier portal is the right
    shape. Brokers actually need read-write access to a wider surface
    (customs profile + holds + payments + maybe sailings/ETA). If brokers end
    up needing to see freight invoice or chase the importer for payment
    before clearing, a one-shipment one-link model could be too narrow.
    Signal of being wrong: first real broker tester says "I can't see X" or
    "I work on five of their imports, can I have one login?" — at which point
    we add multi-shipment broker dashboards in a follow-up.
(b) Weakest exit criterion: AP3 success measure ("test broker can submit a
    status with no admin keystrokes"). It's testable but doesn't prove the
    importer-side experience is good — could pass with the new status
    appearing only deep in the audit log. Mitigation: phase 2 verification
    explicitly reloads the customer Deliver tab and confirms the status
    surfaces there, not just in audit.
(c) Domain expert (customs broker): would want to see the file pack as one
    bundle (commercial invoice + packing list + bill of lading + customs
    declaration) and a single "ready to lodge" indicator, not just an HS
    code. Phase 1 backend already returns docs, so the expert's request
    materializes in phase 2 UI rather than backend; logged as a phase 2
    Lens 2 finding.
(d) Leaving on the table: broker email/SMS notifications when they're
    invited and when an importer adds info they were waiting for. Out of
    scope for this slice but the existing template + outbound infrastructure
    means it's a small follow-up — note to self in progress.md.
(e) Unintended consequence: a shared broker link with a 45-day expiry
    forwarded around an office could leak shipment info to non-brokers. Same
    risk as supplier portal; same mitigation (token rotation via
    `active=False` + re-create). Acceptable for parity.

#### Lens 2 — Adversarial (2026-05-10 14:58 AEST) — reviewer persona: a customs broker who has been burned by half-baked freight-tech portals

(a) Likely-wrong assumption: that a broker will trust a status flip in our
    portal as enforceable. If the broker marks "submitted" and then ABF
    queries it the next day, the broker needs a way to flip it to `queried`
    and add a note. Phase 1 already lists `queried` and notes; verify the
    UI exposes both, not just `cleared` happy path. Logged for phase 2.
(b) Weakest criterion: "Doc upload via broker portal stores doc against
    booking" — passes even if the broker's name and submission timestamp
    aren't recorded against the doc. Mitigation: tighten phase 1 test #5 to
    assert audit event includes `source="broker-portal"` and the doc's
    `uploaded_via` (or equivalent) field reflects broker origin.
(c) Domain expert: would expect the portal to show the importer's ABN,
    EIN, or tax ID prominently — without it the broker can't lodge. Already
    in `CustomsProfile.importer_abn` for AU; need a similar field for US.
    Logged as phase 2 finding (UI must surface this), and phase 1 should
    confirm the broker portal response includes `importer_abn`.
(d) Leaving on the table: rate limiting on `/broker/{token}/clearance`. A
    bored broker (or a leaked token) hammering the endpoint could spam
    audit events. The supplier portal has the same exposure today; not
    worth widening here. Note in progress.md.
(e) Unintended consequence: when broker flips status to `cleared`, phase 1
    plans to release the customs hold. If the importer hasn't paid the SH
    invoice yet, this could short-circuit a payment hold that should still
    block delivery. Verify: only the customs-specific hold gets released,
    not other holds. Phase 1 must explicitly use
    `release_hold_for_booking_and_kind` with `kind=customs`, not a blanket
    release.

#### Plan revisions from AP1

- Phase 1 test #5 to assert `source="broker-portal"` on the audit event.
- Phase 1 portal response to include `importer_abn` and document list with
  origin recorded.
- Phase 1 explicitly: only release the customs hold on `cleared`, never
  blanket release.
- Phase 2 must surface `queried` flow, not just happy path; ABN visible.
- progress.md notes file to track follow-ups (broker notifications,
  multi-shipment dashboard, rate limiting) so we don't lose them.
