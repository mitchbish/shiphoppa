# Phase 2 — Frontend (carrier portal)

Tier: 2.

## Goal

`/carrier/:token` standalone view with sailing/container info, ETA
update form, milestone event buttons (loaded/departed/arrived), and
BL upload. "Invite carrier" button on Sailings tab in Ship phase.

## Exit criteria

- [ ] Frontend types: `CarrierAccessLink`, `CarrierPortalResponse`,
      `CarrierBookingSummary`, `CarrierEtaUpdate`, `CarrierEventUpdate`.
- [ ] API client: `createCarrierLink`, `getCarrierPortal`,
      `submitCarrierEta`, `submitCarrierEvent`, `uploadCarrierDocument`.
- [ ] `WorkspaceMode` extended with `'carrier-portal'`. Route detection
      handles `/carrier/:token`.
- [ ] `CarrierPortalView` component renders booking + container ETA,
      ETA update form, three milestone buttons (Mark loaded / Mark
      departed / Mark arrived), and BL upload form. Reuses broker
      portal CSS.
- [ ] "Invite carrier" button on the Sailings tab — only visible when
      `activeBooking` has a container. Same clipboard fallback pattern
      as broker/warehouse.
- [ ] Build passes.

## Audit log

#### Lens 1 — Correctness (2026-05-10 17:55 AEST)

(a) Three milestone buttons (loaded/departed/arrived) match the
    backend whitelist. UI reuses the supplier-portal action-panel
    button pattern.
(b) ETA update form: `<input type="date">` plus optional note. Submit
    re-fetches portal to render new ETA.
(c) Domain expert: carrier portal must work on a phone. Reuse the
    broker mobile breakpoint.
(d) Out of scope: carrier dashboard, multi-shipment view.
(e) "Invite carrier" should be hidden when no container — would just
    error. Conditional render guards this.

#### Lens 2 — Adversarial (2026-05-10 17:58 AEST) — reviewer persona: a frontend engineer reviewing the third portal mirror

(a) Three portals' code is now ~700 lines of similar JSX. Tempted to
    abstract but resist for now — different forms, different fields.
    After carrier ships, evaluate as a separate refactor PR.
(b) ETA date input: HTML5 `<input type="date">` returns yyyy-mm-dd
    string, which is what the backend Pydantic `date` model expects.
(c) Milestone buttons disable while in flight. Status message reflects
    success/failure.
(d) BL upload: filename + notes only (placeholder pattern).
(e) Mobile breakpoint reused.

#### Plan revisions

- Carrier portal CSS reuses broker portal classes. No rename.
- Confirm-pattern after milestone event: refresh portal, show success
  toast.
- "Invite carrier" only renders when booking has container.
