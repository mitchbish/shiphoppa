# Next Session Handover

You are the next Claude session, picking up Ship Hoppa. The 2026-05-11 session shipped 14 features (cron-job.org wiring + 13 code features) on PR #1, taking backend tests from 228 to 306. This file tells you what's left from the build plan, organized so you can pick anywhere and ship.

The operator (Mitch, info@medio.com.au) wants you to work autonomously. He doesn't need to sign off on plans you have properly planned, audited, and corrected per his global `CLAUDE.md`. Push to PR #1 as you go. He'll sanity-check in the morning.

---

## Critical paths

- **Repo root:** `/Users/mitchbishop/Public/Projects/Ship-Hoppa/`
- **Working worktree:** `/Users/mitchbishop/Public/Projects/Ship-Hoppa/.claude/worktrees/reverent-maxwell-263429/` on branch `claude/reverent-maxwell-263429`. Direct push to `main` is sandbox-blocked; push here, PR #1 picks it up.
- **Build plan (authoritative for vision):** `/Users/mitchbishop/Public/Projects/Ship-Hoppa/docs/IMPORT_AUTOMATION_BUILD_PLAN.md` (4102 lines)
- **Backend ledger / overall status:** `/Users/mitchbishop/Public/Projects/Ship-Hoppa/HANDOVER.md`
- **Per-feature plans:** `/Users/mitchbishop/Public/Projects/Ship-Hoppa/.claude/worktrees/reverent-maxwell-263429/docs/plans/<feature>/`
- **Memory:** `/Users/mitchbishop/.claude/projects/-Users-mitchbishop-Public-Projects-Ship-Hoppa/memory/MEMORY.md`
- **Open PR:** https://github.com/mitchbish/shiphoppa/pull/1
- **Live API:** https://ship-hoppa-api-production.up.railway.app
- **Frontend SPA:** `frontend/src/App.tsx` (~7400 lines, single file)
- **Frontend api + types:** `frontend/src/api.ts`, `frontend/src/types.ts`. All clients for backends shipped this session are already in.

---

## Non-negotiable rules

1. **Run `npm run build` before pushing.** `tsc --noEmit` misses errors the production build catches.
2. **Test UI work in a real browser** (`npm run dev` + `uvicorn app.main:app --reload`). Type-checking and Vite build verify code shape, not feature correctness.
3. **Never edit `marketing/`, root `index.html`, or `vercel.json`.** Another chat owns the Vercel marketing site.
4. **No em dashes.** Use periods, commas, restructure. Operator has flagged this multiple times.
5. **No internal codenames.** Plain English in copy and commits. No "F1", "F11", commit-hash references in user-facing text.
6. **Push as you go.** Each cohesive slice gets its own commit.
7. **Plan-audit-execute-audit-push, per `CLAUDE.md`.** Each non-trivial feature needs a plan in `docs/plans/<feature>/` with AP1 (pre) and AP2 (post) audits through both lenses (Lens 1 correctness, Lens 2 adversarial). No deferrals.
8. **Apply the build plan's UX rules** at every customer-facing card:
   - **Plain language** (build plan §"Plain Language Rule", line 988): "Goods ready date" not "cargo ready date latest". "Arrive at warehouse by" not "warehouse receipt cutoff". "Final delivery" not "last mile". "Delivery hold" not "release hold". "Money to approve" not "payment queue". "Ship Hoppa service fee Priority" not "rush fee".
   - **Decision cards** (§"Actions Must Be Decision Cards", line 2216): every approval needs the action in plain English, the amount/date/impact, why it is needed, what happens if approved, what happens if no action, the source document, and approve/reject/ask-Ship-Hoppa buttons.
   - **Prefill before asking** (§"Prefill Before Asking", line 2200): never blank fields when the system already knows. "We think this is X. Please confirm." when confidence is low.
   - **Advanced detail always reachable** (§"Advanced Detail Is Always Available", line 2228): every automated output exposes source email, source document, extracted facts, confidence, automation rule used, human overrides.
   - **One input, many outputs** (§"One Input, Many Outputs", line 2176): a commercial invoice should update goods value, supplier, cargo description, HS code, landed cost, document checklist, customs profile.
   - **Ask the best person, not the importer by default** (§"Ask The Best Person", line 2186): packing dimensions to supplier, proof of delivery to courier, duty notes to broker, terminal availability to forwarder.

---

## How to start

1. Read this file end to end.
2. Read `MEMORY.md` and `HANDOVER.md` (paths above).
3. `cd /Users/mitchbishop/Public/Projects/Ship-Hoppa/.claude/worktrees/reverent-maxwell-263429`
4. `git fetch && git status -sb && git log --oneline -25`
5. `cd backend && python3 -m pytest tests/ -q` → expect 306 passed.
6. `cd ../frontend && npm run build` → expect exit 0.
7. Pick from "Outstanding work" below. Bias toward small + high-impact items first.
8. Plan in `docs/plans/<feature>/`, AP1, ship, AP2, push. Repeat.

---

## Outstanding work

### A. UI work where the backend is already shipped (highest ROI)

Each item has a typed api client in `frontend/src/api.ts` already. You're wiring screens, not building APIs. Order is by ROI; small high-impact first.

1. **Approval decision cards UI** (Small) — Replace the thin Approvals list with proper decision cards per §"Phase 3" (line 3567) and §"Actions Must Be Decision Cards". Each card: action in plain English, amount/impact, why, what-if-approved, what-if-no-action, source link, approve/reject/ask buttons. The "Ask Ship Hoppa" button calls `requestApprovalReview(approvalId, reason)` (already wired); render the review-requested badge using the new `review_requested_*` fields on `ApprovalRequest`.

2. **Admin tab for Sentinel SMS subscribers** (Small) — Backend has `getSentinelSubscribers`, `createSentinelSubscriber`, `confirmSentinelSubscriber`, `optOutSentinelSubscriber`. Add a new admin sub-tab. Form: phone, optional label, confirm-token paste box. List columns: phone, label, status pill, confirmed_at, created_at, opt-out button.

3. **Admin tabs for growth attribution + supplier verification + import projects** (Medium, NO-BLOCKER #5 in the ledger) — Three small admin views:
   - Growth attribution dashboard from `/growth/attribution-events` + `/growth/attribution-summary`.
   - Supplier verification queue from `/growth/supplier-leads`, with verify form (PATCH `/growth/supplier-leads/{id}/verification`) and a one-click "Generate claim link" button (`createSupplierClaimLink`). The claim URL is `${origin}/supplier-claim/${token}` once item 8 below ships.
   - Saved import projects table from `/import-projects` with create / clone / soft-delete actions wired to existing endpoints.

4. **Customer shipment workspace cards for the wave-3 records** (Medium) — Each gets a card on the existing shipment workspace under the right phase:
   - **DeliveryJob** under Deliver → Delivery: list jobs per booking, create-from-button, status pill that PATCHes, pickup/delivery contacts, POD doc.
   - **PaymentProof** under Deliver → Payments: importer records proof, admin reconciles. Pill colour by reconciliation_status.
   - **LandedCostActual** under Deliver → Payments / Money: admin-editable, importer-readable. Show variance vs estimate when both present.
   - **InsurancePolicy** under Ship → Ship Docs (or new Insurance subview): admin records, importer reads.
   - **ClaimRecord** under Deliver → Delivery: importer drafts, admin patches. Status timeline draft → submitted → under_review → approved/rejected → paid → closed.
   - **MarketplaceOrder** under Order → Supplier: paste-or-attach card capturing Alibaba / 1688 / Made-in-China / Global Sources / direct-supplier order context.
   - All forms must prefill from existing data (§"Prefill Before Asking").

5. **Admin Partners directory + ContingencyOption cards** (Medium, NO-BLOCKER #10 in ledger) — Add admin "Partners" tab that lists `listPartners()` with type filter, click into a partner shows their capabilities and a create-capability form. ContingencyOption cards appear in admin Exceptions queue (and in customer Today / Approvals if `approval_request_id` is set): issue, option, cost/time impact, risk pill, source evidence, approve / reject / mark-applied buttons.

6. **Email extraction preview UI** (Small) — Add a modal on the Inbox tab: paste email text, calls `extractFactsPreview(text, subject)`, shows inferred facts plus would-match booking link. No persistence; confidence-builder.

7. **Supplier portal preview button** (Small) — Add "See what your supplier sees" button on the customer shipment workspace (most natural under Order → Supplier). Calls `getSupplierPortalPreview` and renders in a modal with a clear PREVIEW banner.

8. **Public supplier-claim landing page** (Small) — Once admin generates a claim link, the supplier visits `/supplier-claim/{token}`. No public page rendered for that route yet. Add a `WorkspaceMode === 'supplier-claim'` (or similar) that calls `getSupplierClaim(token)`, shows the auto-created profile, takes contact email + name, calls `acceptSupplierClaim`. Thank-you screen on success.

9. **Audit log filter UI polish** (Small) — Form already ships. Move inline styles to App.css; add CSV export button.

### B. IA reframe to the build plan's target navigation

Build plan §"Target Information Architecture" (line 1031) calls for **Today / Imports / Inbox / Approvals / Money / Space / Company** at the top level, plus per-shipment cards for Where it is, What is needed, Money, Delivery, Space, Audit trail. Current nav is **Order / Ship / Deliver + Account** with subtabs. Both can coexist while you migrate.

Plan this in `docs/plans/customer-ia-reframe/` first — it's a meaningful redesign, not a cleanup. Suggested incremental order:

1. Add **Today** tab as new default landing. Aggregate from existing data: pending approvals, missing-data items, release blockers, ETA slips, spare-space opportunities. Use `getShipments()` + `getShipmentWorkspace()`.
2. Add **Imports** tab: unified shipment list. Each row → existing tracking detail.
3. Promote **Approvals** to a top-level tab (keep the per-phase banners; the tab is where decision cards live in full).
4. Add **Space** tab: combine FCL spare-space + MCL booking under one home.
5. Add **Money** tab: invoice + landed cost + payment proofs in one place.
6. Promote **Inbox** to top level (already in the View enum).
7. Rename **Account** → **Company** if operator confirms.

Map old tabs per §"Old Tab Mapping" (line 1118):
- Current `Book` → `Space → Find shared MCL space`
- Current `Sailings` → split between `Imports` (per shipment) + `Space` (search)
- Current `Tracking` → shipment "Where it is" card
- Current `Order Docs` / `Ship Docs` → shipment Documents section
- Current `Money` → shipment Money section
- Current `Customs` → shipment Customs section
- Current `Profile` / `Account` → `Company`

Don't throw away existing views — keep per-phase nav working under the new top-level tabs until the new IA is fully populated.

### C. Backend / data-model gaps from the build plan

The build plan's "Data Model Evolution" (line 2240) lists models that don't exist yet. Each needs a plan + AP1 + tests + AP2 like the wave-3 skeletons.

- **`Organization`** (line 2244) — represents the importing company. Currently `Importer` + `AccountProfile` are scattered. An Organization gives proper tenant scoping for multi-user, RBAC, billing.
- **`User`** (line 2258) — multi-user-per-organization. Today auth is a static dev-token map; the operator needs real users before billing/multi-seat.
- **`Shipment`** (line 2422) — currently bookings ARE shipments (the aggregator endpoints I shipped expose `/shipments/{booking_id}/workspace`). The build plan wants `Shipment` as a wrapper so one shipment can span multiple bookings (e.g. an MCL split into 2 containers). Phase 1 (line 3505) explicitly calls for "Add Shipment model. Link every booking to a shipment."
- **`ShipmentStateTransition`** (line 2445) — explicit row per state change. Today the state derivation in `automation.py:derive_lifecycle_state` is computed; the audit trail wants a per-transition row.
- **`EntityResolutionRecord`** (line 2463) — for matching across messages; today fact extraction is regex-only and matches by booking_id.
- **`ProductImportProfile`** (line 2481) — SKU memory so repeat orders prefill product / dimensions / HS code.
- **`ImportWorkspace`** (line 2268) — sits between Organization and ImportProject; not yet modeled.
- **`ImportProjectCollaborator`** (line 2353) — multi-user collaborator on an import project.
- **`MissingDataRequest`** (line 2679) — first-class entity; today missing data is computed via `automation.py:detect_missing_data` and chase-messages are queued via OutboundMessage. A persistent MissingDataRequest record gives proper SLA tracking + per-partner deadlines.
- **`AutomationRule`** (line 2658) — separate from `AutomationRun`. Rules are configurable; runs are records of rule executions. Today rules are hard-coded in `automation.py`.
- **`IntegrationConnection`** (line 2984) — overlaps with the existing `AccountIntegration`. Decide whether to extend AccountIntegration or add a parallel record per the spec.
- **`SupplierWorkspace`** (line 2916) — the free supplier workspace per Phase -0.5. Lets a supplier reuse company / address / contact / bank profile across buyer orders.

### D. Automation gaps

- **Snapshot/version restore endpoint** (NO-BLOCKER #7) — punted earlier this session because cross-entity rollback semantics need an operator design conversation. Versions exist (append-only audit trail); snapshot bodies (`ImportProjectSnapshot.snapshot_data`) exist but nothing creates or restores them. Plan the cross-entity rollback shape with the operator before implementing.
- **Document AI extraction (v2 of inbox intake)** — current `automation.py:extract_facts_from_text` is regex-only. §"Phase 2" says v2 should add document AI extraction for invoices, packing lists, booking confirmations.
- **Better-sailing detection auto-creating ContingencyOption** — backend has the `ContingencyOption` model (this session); the engine that DETECTS sailing changes / cutoff misses / ETA slips and writes ContingencyOption rows is not built yet.
- **Auto-route source messages to the right partner** — §"Ask The Best Person" (line 2186). Today every chase goes to importer; logic should route packing dimensions to supplier, POD to courier, duty note to broker, terminal availability to forwarder.
- **Stale-data Sentinel checks** — many specified in §"Health Checks And Monitoring" (line 3927). Existing `automation.py:check_stale_shipments` covers some. Missing: low-confidence extraction rate spike (SH-3302), Supplier Pay quote expiry (SH-4202), supplier bank-detail change (SH-6101), invoice/release mismatch (SH-6103), biosecurity flag review (SH-7102), ETA stale past threshold (SH-8102), route rendering failed (SH-8101).
- **Full Sentinel error registry** — §"Sentinel Error Code Registry" (line 3953) lists 28 codes. Audit `backend/app/sentinel.py:SENTINEL_ERROR_REGISTRY` against the spec; add anything missing.

### E. Growth + acquisition automation

- **Supplier discovery enrichment pipeline** — models exist (`SupplierLead`, `SupplierDiscoveryRun`, `SEOOpportunity`); enrichment logic is a placeholder. §"Automated Supplier Intelligence Engine" (line 456) and §"Large-Scale Safe Supplier Discovery Engine" (line 514) spec the four-layer system: Discovery → Enrichment → Scoring → Outreach Control. Compliance guardrails per §"Outreach Compliance Guardrails" (line 716) are non-negotiable.
- **SEO Engine → CMS brief → published landing page wire-up** — opportunity model exists; the brief generation, CMS publish, and attribution chain don't.
- **Outreach delivery stack** — §"Supplier Outreach Delivery Stack" (line 605): Resend campaigns with suppression, throttling, per-domain limits, opt-out plumbing, complaint handling, deliverability tracking.
- **Trust + localization** — §"Trust And Localization" (line 813): Chinese supplier landing pages, multilingual templates, China-relevant proof points.
- **Free supplier workspace** — Phase -0.5 (line 3412). Multi-week deliverable; the `SupplierProfileClaim` flow shipped in this session is the entry point. The supplier-side workspace (active orders, tasks, production, packing, pickup, buyer invite link) is not built yet.
- **Activation metric dashboards** — §"Activation Metrics" (line 393) lists ten KPIs (supplier invite acceptance rate, buyer invite acceptance rate, forwarded-email-to-shipment-created conversion, etc.). Some need backend instrumentation; admin dashboard surfaces should follow.

### F. Infrastructure / production-readiness

This is the biggest hidden risk: today the entire app runs on an in-memory `Store` that persists via `persistence.py` snapshots. §"Technical Architecture Plan: Backend" (line 3878) is explicit: "Move from in-memory Store to database-backed repositories. Add database migrations. Add background jobs. Add file storage provider abstraction. Add event log as first-class source of truth. Add tenant scoping by organization. Add role-based access control."

Concrete items:

- **Postgres on Railway** — provision the database, write a migration tool (Alembic or similar), define schemas mirroring current models.
- **Repositories layer** — wrap the existing `Store` with a repository interface so call sites don't change while the storage layer migrates.
- **Background job runner** — today the cron-job.org endpoint is a single shot. A real worker (RQ / Dramatiq / Celery / Railway worker service) for email parsing, reminders, extraction retries, status refresh.
- **File storage abstraction** — §"Railway And R2 Storage Architecture" (line 1671): Railway Postgres primary for metadata + small blobs, optional local cache, R2 append-only archive for raw documents and attachments. Today documents are stored as base64 JSON.
- **Tenant scoping by organization** — once the Organization model lands, every read/write must filter by the principal's organization.
- **Role-based access control** — today auth is three flat roles (importer, admin, cron, inbound webhook). Real RBAC needs per-Organization roles, per-feature permissions, and a shared decorator/dependency that enforces them.
- **Real binary file upload** — every portal currently accepts base64 JSON. Migrating to multipart needs `upload_document` + every partner-portal upload endpoint + frontend uploaders rewritten.
- **Rate limiting on token-based portals** — broker / warehouse / carrier / trucker / supplier-claim are all token-gated; no rate limit. Add a shared limiter middleware before scaling outreach.
- **Append-only event log as source of truth** — §"Append-Only Ledgers" (line 1748). Today audit_events approximates this; full event-sourcing pattern is a bigger lift.
- **File backup and restore checks** — §"Phase 8 success criteria" (line 3264-3274). Tested restore path is missing.

### G. Integration items (operator-blocked or external API)

These need credentials, signups, DNS, or operator scoping. Don't start without explicit go-ahead.

- **Wise + OFX FX integration** — §"Phase 8" Supplier Pay. Adapters at `backend/app/providers.py` are ready; flip `WISE_API_TOKEN` + `WISE_PROFILE_ID` env vars when operator says go. OFX adapter not yet stubbed.
- **Outlook OAuth** + **Gmail OAuth** + **IMAP fallback** — §"Email Ingestion" (line 2006). Azure AD app registration, Google OAuth consent screen, polling worker, scoped permissions per organization.
- **Real ABF tariff API** + **US tariff connector** + **BICON biosecurity** — §"Customs Source Strategy" (line 2077). Live → rules → manual review fallback chain.
- **Real sailing data feeds** (CMA CGM, Maersk, MSC) — §"Phase 5+" carrier API credentials, real-time event processing.
- **Visibility provider track-and-trace** — Project44 / Marine Traffic / similar.
- **Stripe or payment provider** for Ship Hoppa invoicing.
- **Xero / QuickBooks / MYOB** accounting integrations — §"Phase 9" (line 3849) integration order item 16.
- **Shopify / WooCommerce / inventory systems** — §"Integration Connections" (line 1988).
- **OCR for image-only PDFs** — Tesseract or external; Dockerfile system dependency required.
- **Inbound email DNS + `SHIP_HOPPA_INBOUND_EMAIL_TOKEN`** — operator sets env var + configures Resend Inbound (or Mailgun) to point at `/inbound/email`. Webhook code is shipped.

### H. Polish + cleanup

- **Plain language audit** — sweep `App.tsx` for "cargo ready date latest", "release hold", "warehouse receipt cutoff", "last mile", "platform fee", "rush fee" and replace per §"Plain Language Rule" (line 988).
- **Shared `PartnerPortal` React component refactor** — broker / warehouse / carrier / trucker portals duplicate ~80% of the same shape. Extract once IA reframe is stable.
- **Add `partner_update` SourceType** — DONE this session (broker / carrier / trucker emit `source_type=partner_update`).
- **End-to-end tests** — §"Phase 8 Harden, Test And Scale" (line 3264): order-to-delivery walkthrough, provider failure tests, Sentinel alert tests, permission and data-isolation tests, file backup/restore checks, payment + supplier bank-detail risk checks, customs estimate + broker-review checks, growth automation suppression / opt-out / deliverability checks. The standard the operator cares about: "an import can be created, saved, resumed, paid, shipped, tracked, cleared, delivered, audited and cloned."

---

## Operator-blocked, do-not-start

Wait for explicit go-ahead before investing time in any of these:

- Wise FX integration (operator said "do this last")
- Microsoft 365 / Outlook OAuth inbox sync
- Google Workspace / Gmail OAuth inbox sync
- Real ABF / US tariff API connectors
- Real sailing data feeds (carrier APIs)
- Image-only PDF OCR (Dockerfile system dep)
- `SHIP_HOPPA_INBOUND_EMAIL_TOKEN` + Resend Inbound DNS

---

## Verification expectations

- `cd backend && python3 -m pytest tests/ -q` — should be 306 at start of session, only goes up.
- `cd frontend && npm run build` — exit 0, no warnings.
- For every UI slice: drive end-to-end in a browser before declaring done. The operator's `CLAUDE.md` is explicit: "Type checking and test suites verify code correctness, not feature correctness — if you can't test the UI, say so explicitly rather than claiming success."
- For every backend slice: tests + audit-log entries demonstrating the new behavior, plus a curl against the live deploy after Railway redeploys (cron-job.org confirms the deploy is up).
- After each ship: update `HANDOVER.md` ledger row from NOT STARTED to DONE with the date and code path. Update PR #1's description (`gh pr edit 1 --body ...`) when a meaningful slice lands.

---

## Suggested overnight slice

If you ship UI items 1, 2, 3, 6, 7, and 8, plus polish item H "plain language audit", the operator wakes up to:
- Decision-card approvals.
- Admin tab for Sentinel SMS subscribers.
- Three new admin tabs (growth, supplier verification, import projects).
- Email-extraction preview modal.
- See-what-your-supplier-sees button.
- Working public supplier-claim page.
- Plain-language copy across the customer portal.

That's a meaningful overnight delivery. UI items 4 and 5 are bigger; pick them up after the small ones land. The IA reframe (B) and the Organization / User / Shipment-wrapper data model (C) need a planning conversation when the operator is awake.

End of handover.
