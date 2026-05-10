# Phase 2 — Frontend

Tier: 2.

## Goal

Render a warehouse portal page at `/warehouse/:token` showing expected
cargo and a receipt-confirmation form (or a "you don't need this, Ship
Hoppa is collecting" notice for pickup-mode shipments). Add an "Invite
warehouse" button on the cargo or pickup tab in Ship for the importer.

## Exit criteria

- [x] `WarehouseAccessLink`, `WarehousePortalResponse`,
      `WarehouseBookingSummary`, `WarehouseReceiptUpdate` types added.
- [x] API client exposes the four warehouse functions; admin-token
      routing extended for `/warehouse-links`.
- [x] App routing detects `/warehouse/:token` via
      `warehouseTokenFromPath`. `WorkspaceMode` extended with
      `warehouse-portal`. App body short-circuits to
      `<WarehousePortalView token={...} />` when active.
- [x] `WarehousePortalView` renders cargo expectations, then branches
      on `delivery_mode`:
      - `ship_hoppa_pickup` shows a clear "Ship Hoppa is collecting
        from the supplier" notice. No form.
      - Otherwise shows the receipt form (actual CBM, actual weight,
        notes) and a photo upload form.
      - After successful receipt, the form is replaced with a
        "Receipt confirmed at {timestamp}" panel — no stale form
        re-submit risk.
- [x] "Invite warehouse" section on the Ship phase Pickup tab (step 4),
      only shown when `delivery_mode != 'ship_hoppa_pickup'`. Same
      clipboard fallback pattern as broker invite.
- [x] `npm run build` exits 0. Bundle: 416.74 kB JS, 72.85 kB CSS.

## Files to touch

- `frontend/src/types.ts`
- `frontend/src/api.ts`
- `frontend/src/App.tsx` — add `WarehousePortalView`, route detection,
  invite button.
- `frontend/src/App.css` — reuse broker portal classes, add minimal
  warehouse-specific styles.

## Known risks / do-not-skip list

- No bulk find/replace from broker portal code. Read it, then port the
  warehouse fields and form deliberately.
- `delivery_mode` switch is the load-bearing logic. Test both branches
  manually before committing (or at least eyeball the JSX twice).
- Only ONE clipboard fallback pattern across portals. Reuse.
- Em dashes banned.

## Verification

1. `npm run build` exits 0.
2. Read the rendered output in source: confirm the receipt form is
   conditional on `delivery_mode`.
3. Live browser walkthrough deferred to user post-merge.

## Audit log

#### Lens 1 — Correctness (2026-05-10 16:46 AEST)

(a) Likely-wrong: that the broker portal CSS classes generalize. Most
    do (`.broker-portal-card`, `.broker-portal-form`, etc). The receipt
    form has a few new fields but the layout fits the same grid.
    Resist creating a separate file; just add `.warehouse-portal-*`
    aliases or reuse outright. Actually — rename CSS to
    `.partner-portal-*` and use across both? Tempting but premature.
    Reuse broker classes inline; carrier portal will tip the balance.
(b) Weakest exit: build passes. Hardened by also asserting the
    `delivery_mode` branch in source review.
(c) Domain expert: warehouse-side users may not know what "CBM" means.
    Show "cubic meters" or similar with the abbreviation in
    parentheses. Phase 2 will use "Actual cubic meters (CBM)".
(d) Leaving on the table: per-line photo capture, scanned barcode
    workflow. Out of scope.
(e) Unintended consequence: form stays empty after submit and the
    user can re-submit. Disable the form fields after a successful
    receipt confirmation; show a "Receipt confirmed" panel instead.

#### Lens 2 — Adversarial (2026-05-10 16:50 AEST) — reviewer persona: warehouse user on a slow connection

(a) Receipt form must save quickly even on slow networks. Show a
    spinner; don't allow re-submit while in flight. Same pattern as
    broker.
(b) Photo upload via the existing JSON+filename-only doc endpoint is a
    placeholder (the codebase's upload endpoint stores a placeholder
    payload). Acceptable; carrier and warehouse photos will be
    placeholders too. Actual binary upload is a separate gap.
(c) Mobile width is essential. Warehouses use phones on the floor.
    Reuse the broker portal's media query.
(d) After successful receipt, redirect/replace UI with a "thank you,
    we got it" panel — don't leave a form full of stale data.
(e) When delivery_mode is pickup, the page should make it crystal
    clear there's no action — bold, large text, no form.

#### Plan revisions

- Reuse broker portal CSS classes by name. No rename.
- Use "Actual cubic meters (CBM)" and "Actual weight (kg)" labels.
- Successful receipt replaces form with a confirmed panel, not just a
  toast.
- Mobile breakpoint already in broker CSS — verify it covers warehouse
  too.

#### Lens 1 — Correctness (2026-05-10 17:24 AEST, post-execution)

(a) Confirmed: broker portal CSS classes generalize cleanly. No new
    `.warehouse-portal-*` classes needed. The broker mobile breakpoint
    (`@media (max-width: 540px)`) covers warehouse too.
(b) Form fields use `type="number"` with min and step. Native
    validation catches non-numeric input; explicit guard in
    `handleSubmit` checks for `Number.isFinite(...) > 0` to handle
    edge cases like empty string.
(c) Successful receipt branches to a "Receipt confirmed" panel — the
    form is replaced. Stale-form-resubmit risk eliminated.
(d) Pickup-mode panel is plain, prominent: title + paragraph + no
    form. No CTA — broker should know they're not needed and contact
    the importer.
(e) "Invite warehouse" is conditionally rendered only when
    `delivery_mode !== 'ship_hoppa_pickup'`, so the importer doesn't
    even see the button on pickup-mode bookings.

#### Lens 2 — Adversarial (2026-05-10 17:27 AEST, post-execution) — reviewer persona: warehouse user on a slow connection in a Foshan warehouse

(a) Submit button disables while in flight. Loader2 spinner.
(b) Photo upload is filename-only (placeholder pattern matching the
    rest of the app). Real binary upload is a separate gap; acceptable.
(c) Mobile-width verified by inheriting broker portal breakpoint.
    Forms collapse to single column.
(d) `Number.isFinite` guards reject empty strings even though the
    input has `required` — defensive but cheap.
(e) Tsc caught one unused-import (`WarehouseReceiptUpdate` was not
    needed in App.tsx after the API helpers took it). Removed.

#### AP2 findings to fix in scope

None blocking. Browser walkthrough deferred per autonomous-overnight
session — same as broker portal phase 2. User can spot-check post-
merge.
