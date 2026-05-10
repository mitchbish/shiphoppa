# Phase 2 — Frontend

Tier: 2 (Standard — Launchpad-internal runtime, no tenant write).

## Goal

Render a broker portal page at `/broker/:token` that shows the broker their
shipment's customs profile, holds, and recent events; lets them submit a
clearance status update; and lets them upload a customs document. Plus an
"Invite broker" button on the importer's customs tab in Deliver that creates
a link and copies the URL to clipboard.

## Exit criteria

- [ ] `BrokerAccessLink`, `BrokerPortalResponse`, `BrokerClearanceUpdate`
      types added to `frontend/src/types.ts`, mirroring `SupplierAccessLink`,
      `SupplierPortalResponse` shapes from backend.
- [ ] `frontend/src/api.ts` exposes `getBrokerPortal(token)`,
      `submitBrokerClearance(token, payload)`, `uploadBrokerDocument(token,
      payload)`, `createBrokerLink(bookingId)` (admin token routing for the
      last one only).
- [ ] App routing: when URL path matches `/broker/:token`, render the broker
      portal view instead of the customer SPA shell. Mirror how
      `/supplier/:token` is detected.
- [ ] Broker portal view shows: shipment ID, importer name, importer ABN
      (or other tax ID), customs profile summary (HS code, goods value,
      incoterm, current status), holds list, recent events list, document
      upload form, clearance-update form.
- [ ] Clearance-update form lets the broker pick between
      `submitted`/`queried`/`cleared` (not just the happy path). `queried`
      requires an attached note explaining the query.
- [ ] "Invite broker" button on the customs tab in the Deliver phase. On
      click: calls `createBrokerLink`, builds the absolute URL
      (`${origin}/broker/${token}`), writes to clipboard if the API is
      available, ALWAYS shows the full URL in a readable, manually-
      selectable text field as a clipboard fallback, and shows a toast.
      Existing toast primitive reused.
- [ ] After a clearance update, the portal view refetches and re-renders.
      Form re-fetches the latest customs profile before applying the broker's
      update; if the profile changed since the form loaded, a "the customs
      profile changed" toast appears and the broker re-confirms before
      submission. Importer-side: when the importer reopens the customs tab,
      the new status is visible (no real-time push needed; existing 30s
      poll is acceptable).
- [ ] `cd frontend && npm run build` exits 0 with no new warnings beyond the
      existing baseline.

## Files to touch

- `frontend/src/types.ts` — add the new types.
- `frontend/src/api.ts` — add the four functions.
- `frontend/src/App.tsx` — add broker portal view component, route detection,
  invite-broker button on customs tab, broker portal state management. Keep
  the structure parallel to the existing supplier portal code so future
  partner portals can be added the same way.
- `frontend/src/App.css` — reuse supplier-portal styles where possible; add
  one or two broker-specific tweaks if needed (the form differs).

## Known risks / do-not-skip list

- **No bulk find/replace from supplier portal code.** Per the
  no-bulk-conversion rule, port the broker portal component deliberately —
  read the supplier component fully, then write the broker version with the
  customs-specific fields. `sed` will silently drop or corrupt JSX.
- **Admin token routing.** `createBrokerLink` is the only admin-only call.
  Use the same token-routing pattern `api.ts` already has for other
  admin-only endpoints (`createSupplierLink` is the model).
- **Don't merge customer and broker views.** The `/broker/:token` URL must
  render only the broker portal. Leaking customer SPA chrome into the broker
  view is a privacy/UX hazard.
- **Use absolute URL when copying to clipboard.** `${window.location.origin}/broker/${token}`,
  not a relative path. Brokers will paste this into emails.
- **Em dashes are banned.** Apply this to every UI string in this phase.
- **Run `npm run build`, not `tsc --noEmit`.** Per HANDOVER, `tsc --noEmit`
  misses Vite/JSX errors that the production build catches.
- **Use the feature in a real browser.** Type checks and the build passing
  do not prove the broker page renders correctly. Open the URL, click
  through, submit a clearance update, watch the response come back. Document
  this in the verification section.

## Verification

1. `cd frontend && npm run build` exits 0.
2. `cd backend && uvicorn app.main:app --port 8001 &` and
   `cd frontend && npm run dev -- --port 5174` (or however the dev server is
   configured). Open the dev URL.
3. Load the customer view, advance a shipment so it has a customs profile,
   open Deliver → Customs, click "Invite broker". Confirm a toast appears
   and the clipboard contains the URL.
4. Paste the URL into a new browser tab. Confirm the broker portal renders
   with the right shipment info and no customer chrome.
5. Submit a clearance update from the broker view. Confirm the portal
   re-fetches and shows the new status.
6. Reload the customer Deliver tab. Confirm the customs status reflects
   what the broker submitted.
7. Upload a small PDF as a customs document via the broker form. Confirm it
   appears in the importer's documents list.
8. Resize browser to mobile width (375px wide). Confirm broker form is
   usable, fields are readable, submit button is reachable without
   horizontal scroll.
9. Stop dev servers. Document the verification screenshots / plain-text
   walkthrough in the audit log before ticking exit criteria.

## Audit log

#### Lens 1 — Correctness (2026-05-10 15:08 AEST)

(a) Likely-wrong assumption: that the existing supplier portal's URL
    detection is in App.tsx using a path prefix. App.tsx is 7000 lines —
    the routing pattern could be regex, location.pathname.startsWith, or a
    custom router. Signal: `npm run build` errors on type mismatch when I
    try to extend the routing. Mitigation: read the supplier-route check in
    App.tsx before writing the broker version; replicate exactly.
(b) Weakest exit criterion: "`npm run build` exits 0". This says nothing
    about whether the page renders. Real verification is the browser walk in
    step 3-7. Tightened by the explicit verification protocol in this doc.
(c) Domain expert (frontend engineer): would extract a `PartnerPortal`
    component shared between supplier and broker, parameterized by role.
    Not doing this now — premature abstraction with two instances. Will
    revisit when warehouse portal lands and we have three. Note in
    progress.md.
(d) Leaving on the table: an in-portal "Ask the importer a question" chat
    primitive. Brokers would love this (cleaner than email). Out of scope;
    notifications/inbox already exist for one-way; bidirectional chat is a
    separate plan.
(e) Unintended consequence: clipboard write may fail silently in some
    browsers (Safari, certain insecure-context scenarios). Without a
    fallback, the importer thinks they copied a link they don't have.
    Mitigation: show the URL in a readable text field next to the toast so
    a manual copy is always possible.

#### Lens 2 — Adversarial (2026-05-10 15:11 AEST) — reviewer persona: a frontend engineer who's been on call when an emoji-heavy "shipped" tweet went out before anyone confirmed the page actually worked in production

(a) Likely-wrong assumption: that the existing dev server config is
    already set up. The handover doesn't mention it. If `npm run dev`
    needs `VITE_API_BASE_URL` or proxy config to talk to the backend,
    verification step 3 fails. Mitigation: check existing dev server
    behavior with a smoke test before relying on it.
(b) Weakest criterion: "Use the feature in a real browser." Real
    verification needs the importer to ALSO see the broker's update.
    Tightened in step 6 of the verification protocol.
(c) Domain expert: would test on mobile. Brokers often reply on phones.
    Add to verification: open the broker URL on a mobile width (resize
    browser) and check the form submits.
(d) Leaving on the table: i18n. China is a launch country; broker portal
    is import-side, so EN-only is acceptable for now. Note in progress.md.
(e) Unintended consequence: If the broker leaves the form open with stale
    state and submits, they could overwrite an importer-side update made
    in the meantime. Mitigation: re-fetch on form submit before applying
    the update; show a "this is new" toast if the customs profile drifted.
    Lightweight optimistic-concurrency is enough for now.

#### Plan revisions from AP1

- Phase 2 verification adds: clipboard fallback (show URL in copyable field).
- Phase 2 verification adds: open broker URL on mobile width, confirm form
  submits.
- Phase 2 form behavior: re-fetch on submit; toast if customs profile
  drifted between load and submit.
- progress.md follow-ups: extract shared `PartnerPortal` component when
  warehouse portal lands; in-portal chat primitive; i18n.
