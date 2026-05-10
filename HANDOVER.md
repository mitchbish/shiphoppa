# Ship Hoppa — Handover

## Intro for the new chat

You are the next Claude session picking up Ship Hoppa.

**The operator (Mitch, info@medio.com.au) is asleep.** He left explicit
instructions: work as autonomously and completely as possible. He does
not need to sign off on plans you have properly planned, audited, and
corrected per the planning standard in his global `CLAUDE.md`. Just
get the work done, push as you go, and update this file as you ship.

What this means in practice:

- Pick the next feature from the **Progress ledger** below (anything
  marked NOT STARTED in the "No-blocker, autonomous" section is fair
  game). Don't wait for permission.
- Plan in `/Users/mitchbishop/Public/Projects/Ship-Hoppa/docs/plans/<feature-name>/`
  using the standard 5-section shape with AP1 (pre-execution) and
  AP2 (post-execution) audits through both lenses. Apply revisions
  in scope. No deferrals.
- Ship in small, cohesive commits. Push after each one. Direct push
  to `main` is sandbox-blocked, so push to the feature branch
  `claude/reverent-maxwell-263429` and update PR #1
  (https://github.com/mitchbish/shiphoppa/pull/1) as you add work.
- Keep this `HANDOVER.md` ledger up to date. Every time you ship a
  feature, move its line from NOT STARTED → DONE with the date and
  test count.
- The full product spec is at
  `/Users/mitchbishop/Public/Projects/Ship-Hoppa/docs/IMPORT_AUTOMATION_BUILD_PLAN.md`
  (4102 lines, authoritative for vision).

If you hit a genuine blocker (need an external API key, need a
service signed up at a provider, need a decision the operator must
make), mark it BLOCKED in the progress ledger and move to the next
NOT STARTED item. Do not wait on him.

The previous Claude session shipped 11 features overnight (broker /
warehouse / carrier / trucker portals end to end, inbound email
webhook, saved import projects CRUD, audit log filtering, supplier
verification state machine, growth attribution, purchase order
clone). The 2026-05-11 session then shipped another 14: cron-job.org
wiring, shipments aggregator, approval request-review, supplier
portal preview, Sentinel SMS opt-in, email extraction preview,
audit log filter UI, supplier profile claim, DeliveryJob CRUD,
PartnerProfile + PartnerCapability + ContingencyOption skeleton,
PaymentProof + LandedCostActual upsert with variance derivation,
MarketplaceOrder ingest, InsurancePolicy + ClaimRecord skeleton,
and a `partner_update` SourceType cleanup. 306 backend tests pass.
Frontend builds clean. All bundled in PR #1. See the ledger below
for what's left.

## Critical paths (full absolute paths)

- **Repo root:** `/Users/mitchbishop/Public/Projects/Ship-Hoppa/`
- **Working worktree (current branch):**
  `/Users/mitchbishop/Public/Projects/Ship-Hoppa/.claude/worktrees/reverent-maxwell-263429/`
  on branch `claude/reverent-maxwell-263429`. Most recent work lives
  here. The repo's `main` branch is at the worktree's parent.
- **Build plan:**
  `/Users/mitchbishop/Public/Projects/Ship-Hoppa/docs/IMPORT_AUTOMATION_BUILD_PLAN.md`
- **This file:**
  `/Users/mitchbishop/Public/Projects/Ship-Hoppa/HANDOVER.md`
  (also mirrored in the worktree at the same relative path)
- **Per-feature plans:**
  `/Users/mitchbishop/Public/Projects/Ship-Hoppa/.claude/worktrees/reverent-maxwell-263429/docs/plans/<feature-name>/`
  (each contains `00-OVERVIEW.md`, optional per-phase docs,
  `progress.md`, and full AP1/AP2 audit logs).
- **Memory (persistent across chats):**
  `/Users/mitchbishop/.claude/projects/-Users-mitchbishop-Public-Projects-Ship-Hoppa/memory/MEMORY.md`
- **Operator's global CLAUDE.md (planning standard):**
  `/Users/mitchbishop/.claude/CLAUDE.md`
- **GitHub repo:** `mitchbish/shiphoppa` (the operator's GH login is
  `mitchbish`; `gh` CLI is logged in)
- **Open PR:** https://github.com/mitchbish/shiphoppa/pull/1
- **Live API:** `https://ship-hoppa-api-production.up.railway.app`

## What this product is

Ship Hoppa turns scattered import paperwork (supplier emails, PDF
invoices, forwarder updates, broker notes) into one live shipment
record per import. Goal: zero manual data entry. The importer
forwards an email; Ship Hoppa parses, matches, and acts.

The customer portal has **three workflow phases** plus a separate
Account area in the header (Account is not a phase, it's the
settings shelf):

- **Order** — supplier discovery, purchase orders, production,
  inspection, supplier payment, order-side documents. Covers
  everything until cargo is ready to ship.
- **Ship** — FCL, MCL (the primary revenue mode), or LCL transport
  from origin port to destination port, with live tracking.
- **Deliver** — from the moment the ship docks: customs, release,
  destination delivery to the importer's warehouse.

Phase 3 was previously called "Clear". The operator prefers
"Deliver". Don't revert that.

## Where everything lives

```
/Users/mitchbishop/Public/Projects/Ship-Hoppa/
  backend/                FastAPI + Pydantic; in-memory Store with snapshot persistence
    app/
      main.py             All HTTP endpoints
      operations.py       All store-mutating business logic
      automation.py       Lifecycle state machine, fact extraction, chase, approvals
      invoices.py         Supplier invoice extractor (text + PDF)
      customs.py          HS code classification helper
      providers.py        Resend / Twilio / Wise adapters (all gated by feature flag)
      sentinel.py         Error code registry, health checks, SMS reporter
      templates.py        Email/SMS template registry with safe substitution
      models.py           All Pydantic models and enums
      store.py            In-memory dict-of-dict store (the "DB")
      persistence.py      Optional snapshot to disk
      auth.py             Bearer-token auth (importer / admin / cron / inbound principals)
    tests/
      test_*.py           28 test files; 228 tests as of 2026-05-11

  frontend/               React + TypeScript + Vite SPA
    src/
      App.tsx             ~7900 lines, single-file SPA. Customer + admin views + 4 partner portal views.
      api.ts              Frontend API client. Token routing per endpoint.
      types.ts            Shared TypeScript types mirroring backend models.
      App.css             All styles.

  marketing/              DO NOT TOUCH. Owned by another chat session.
  index.html              DO NOT TOUCH. Owned by another chat session.
  vercel.json             DO NOT TOUCH.
  Dockerfile              Multi-stage: Node builds frontend, Python serves both.
  railway.toml            Railway service config.

  docs/
    IMPORT_AUTOMATION_BUILD_PLAN.md   Full product spec. Authoritative for vision.
    plans/<feature-name>/             Per-feature plans + AP1/AP2 audits + progress

  HANDOVER.md             This file.
```

## Deployment

- GitHub: `mitchbish/shiphoppa`. Direct-to-`main` push is
  sandbox-blocked under the current safety profile, so the workflow
  is push-to-feature-branch → PR → merge. The operator's normal
  habit is direct pushes; only the harness blocks it.
- Railway runs the **whole app** (backend + frontend) at
  `https://ship-hoppa-api-production.up.railway.app`. The Dockerfile
  is a multi-stage build. Railway auto-deploys on every push to
  `main`.
- Vercel runs only the marketing site at `marketing/` and root
  `index.html`. A different chat handles that.
- `railway` CLI is logged in. From
  `/Users/mitchbishop/Public/Projects/Ship-Hoppa/` you can run
  `railway status`, `railway domain`, `railway logs`, etc.

## Auth tokens

Dev (only work against local backend):

- Admin: `Bearer shiphoppa-admin-dev`
- Importer: `Bearer shiphoppa-importer-dev`
- Cron: `Bearer shiphoppa-cron-dev`
- Inbound webhook: `Bearer shiphoppa-inbound-dev`

Production: tokens live in Railway env vars
(`SHIP_HOPPA_ADMIN_TOKEN`, `SHIP_HOPPA_IMPORTER_TOKEN`,
`SHIP_HOPPA_CRON_TOKEN`, `SHIP_HOPPA_INBOUND_EMAIL_TOKEN`). Use
`railway run -- bash -c '... $SHIP_HOPPA_ADMIN_TOKEN ...'` to call
production with the right token without handling it yourself.

## Environment variables on Railway

Already set (as of 2026-05-11):

- `RESEND_API_KEY`, `RESEND_FROM_EMAIL`
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`
- `SHIP_HOPPA_LIVE_PROVIDERS=true` (master kill switch)
- `SHIP_HOPPA_ENV=production`
- `SHIP_HOPPA_OPS_PHONE=+61411400840` (P0/P1 SMS recipient)
- `SHIP_HOPPA_ADMIN_TOKEN`, `SHIP_HOPPA_IMPORTER_TOKEN`,
  `SHIP_HOPPA_CRON_TOKEN`
- Persistence vars

Not yet set (operator follow-ups):

- `SHIP_HOPPA_INBOUND_EMAIL_TOKEN` — needed for `POST /inbound/email`
  webhook auth. Until this is set + Resend Inbound (or Mailgun) is
  configured to point at the URL, inbound emails won't ingest.
- `WISE_API_TOKEN`, `WISE_PROFILE_ID` — deferred to last per
  operator instruction. Adapter at
  `backend/app/providers.py:get_fx_quote_via_wise` is ready; flip
  the env var when the operator says go.

## Commands you'll need

```bash
# Run the full backend test suite (must stay green; 306 as of 2026-05-11)
cd /Users/mitchbishop/Public/Projects/Ship-Hoppa/.claude/worktrees/reverent-maxwell-263429/backend && python3 -m pytest tests/

# Build the frontend the same way Railway does (NEVER use tsc --noEmit alone)
cd /Users/mitchbishop/Public/Projects/Ship-Hoppa/.claude/worktrees/reverent-maxwell-263429/frontend && npm run build

# Check git state from the worktree
cd /Users/mitchbishop/Public/Projects/Ship-Hoppa/.claude/worktrees/reverent-maxwell-263429 && git fetch && git status -sb && git log --oneline -15

# Check Railway state (run from anywhere inside the repo)
railway status
railway logs

# Live health check
curl https://ship-hoppa-api-production.up.railway.app/health
```

## Critical rules (don'ts)

1. **Don't touch `marketing/`, root `index.html`, or `vercel.json`.**
   Another chat owns the Vercel marketing site. If `git status`
   shows changes there, `git checkout` them before committing.
2. **Don't use em dashes** in any copy you write (UI strings,
   marketing, comments, commit messages). Use periods, commas, or
   restructure the sentence.
3. **Don't trust `tsc --noEmit` to catch frontend errors.** Always
   run `npm run build` before pushing.
4. **Don't internal-codename anything.** Status updates and commit
   messages should be plain English.
5. **Don't batch commits.** Push as you finish each cohesive change.
6. **Don't read another project's `.env` files** to harvest
   credentials. Sandbox blocks it for good reason.
7. **Don't write secrets to memory or repo files.** Memory and repo
   are readable; credentials go to Railway env vars only.
8. **Don't use direct push to `main`.** It's sandbox-blocked. Push
   to the feature branch and update PR #1.
9. **Don't skip the planning standard.** Every Tier 2+ feature gets
   a plan in `docs/plans/<feature-name>/` with AP1 audit before
   execution and AP2 audit before tick. No deferrals; fix in scope
   or mark BLOCKED.

## Progress ledger

Each row references the section in
`/Users/mitchbishop/Public/Projects/Ship-Hoppa/docs/IMPORT_AUTOMATION_BUILD_PLAN.md`
(by line number in parentheses). Pick anything in the
"No-blocker, autonomous" section that's NOT STARTED and ship it.

### Foundation — DONE

| Feature | Status | Plan ref | Code path |
|---|---|---|---|
| Customer portal three-phase IA (Order / Ship / Deliver + Account) | DONE 2026-05-10 | Customer Phase Architecture (line 28-76) | `frontend/src/App.tsx` |
| Account profile + integrations + help | DONE 2026-05-10 | Step 1 Account Foundation (line 93-107) | `backend/app/operations.py` (account_*), `frontend/src/App.tsx` |
| Order phase: supplier, production, inspection, supplier pay, docs | DONE 2026-05-10 | Step 2 Order Phase (line 108-132) | `backend/app/operations.py`, `frontend/src/App.tsx` |
| Ship phase: cargo, ship docs, pickup, sailings, tracking | DONE 2026-05-10 | Step 3 Ship Phase (line 133-156) | `backend/app/operations.py`, `frontend/src/App.tsx` |
| Deliver phase: customs, payments, delivery | DONE 2026-05-10 | Step 4 Clear Phase (line 157-172) | `backend/app/operations.py`, `frontend/src/App.tsx` |
| Lifecycle state machine (28 states) | DONE 2026-05-10 | Step 5 Automation (line 174-181) | `backend/app/automation.py` |
| Fact extraction from text | DONE 2026-05-10 | Phase 2 (line 2531-2566) | `backend/app/automation.py`, `backend/app/invoices.py` |
| Resend / Twilio outbound + Sentinel SMS reporter | DONE 2026-05-10 | Production-Grade Standard (line 201-225) | `backend/app/providers.py`, `backend/app/sentinel.py` |
| HS code rules-based suggester | DONE 2026-05-10 | Customs source strategy (line 2077-2088) | `backend/app/customs.py` |
| Cron-driven automation cycle endpoint | DONE 2026-05-10 | Step 5 Automation (line 174-181) | `POST /automation/cron/run` in `backend/app/main.py` |

### Overnight delivery 2026-05-11 — DONE (PR #1)

| Feature | Status | Plan ref | Code path | Plan dir |
|---|---|---|---|---|
| Broker portal (backend + frontend) | DONE 2026-05-11 | Phase 6 Customs/broker (line 161-164, 3732+) | `backend/app/operations.py:create_broker_link..broker_clearance_update`, endpoints `/broker-links` + `/broker/{token}/*`, `frontend/src/App.tsx:BrokerPortalView` | `docs/plans/broker-portal/` |
| Warehouse portal (backend + frontend) | DONE 2026-05-11 | Phase 3 warehouse + Step 3 Ship (line 137-148) | `backend/app/operations.py:create_warehouse_link..warehouse_receipt_update`, endpoints `/warehouse-links` + `/warehouse/{token}/*`, `frontend/src/App.tsx:WarehousePortalView` | `docs/plans/warehouse-portal/` |
| Carrier portal (backend + frontend) | DONE 2026-05-11 | Step 3 Ship: Sailings/Tracking (line 149-156) | `backend/app/operations.py:create_carrier_link..carrier_event_update`, endpoints `/carrier-links` + `/carrier/{token}/*`, `frontend/src/App.tsx:CarrierPortalView` | `docs/plans/carrier-portal/` |
| Trucker portal (backend + frontend) | DONE 2026-05-11 | Phase 5 Destination trucking (line 3644-3679) + Step 4 Clear: Delivery (line 169-172) | `backend/app/operations.py:create_trucker_link..trucker_status_update`, endpoints `/trucker-links` + `/trucker/{token}/*`, `frontend/src/App.tsx:TruckerPortalView` | `docs/plans/trucker-portal/` |
| Inbound email webhook | DONE 2026-05-11 | Email ingestion spec (line 2006-2044), Phase 2 Inbox intake (line 2531-2566) | `backend/app/main.py:inbound_email`, `backend/app/auth.py:require_inbound_webhook` | `docs/plans/email-ingestion/` |
| Saved import projects CRUD | DONE 2026-05-11 | Phase -2 Saved import projects (foundation, line 1939-1987) | `backend/app/operations.py:create_import_project..soft_delete_import_project`, endpoints `/import-projects` POST/PATCH/clone/DELETE | `docs/plans/import-projects-crud/` |
| Audit log filtering | DONE 2026-05-11 | Production-Grade audit standard (line 209-225) | `backend/app/main.py:audit_events` query params | (no separate plan; ad-hoc commit) |
| Supplier verification state machine | DONE 2026-05-11 | Supplier acquisition strategy (line 408-863), Compliance (line 412) | `backend/app/operations.py:update_supplier_lead_verification`, `PATCH /growth/supplier-leads/{id}/verification` | (no separate plan; ad-hoc commit) |
| Growth attribution events + summary | DONE 2026-05-11 | Activation Metrics (line 393-407), Adoption loop (line 261-310) | `backend/app/operations.py:filter_growth_attribution_events..summarise_growth_attribution`, `/growth/attribution-events` GET/POST + `/growth/attribution-summary` | (no separate plan; ad-hoc commit) |
| Purchase order clone | DONE 2026-05-11 | Step 2 Order Phase Production (line 117-119), repeat-order ergonomics | `backend/app/operations.py:clone_purchase_order`, `POST /purchase-orders/{id}/clone` | (no separate plan; ad-hoc commit) |
| Shipments aggregator endpoints | DONE 2026-05-11 | Phase 1 Reframe around shipments (line 3513-3515) | `backend/app/operations.py:list_shipment_summaries..shipment_workspace`, `backend/app/main.py:shipments..shipment_workspace_endpoint` | `docs/plans/shipments-aggregator/` |
| Approval `request-review` endpoint | DONE 2026-05-11 | Phase 3 Approval queue (line 3583-3586) | `backend/app/operations.py:request_approval_review`, `POST /approvals/{id}/request-review` in `backend/app/main.py`, frontend `requestApprovalReview` in `frontend/src/api.ts` | `docs/plans/approval-request-review/` |
| Supplier portal preview | DONE 2026-05-11 | Supplier-side wedge (line 260-286) | `backend/app/operations.py:supplier_portal_preview`, `GET /bookings/{id}/supplier-preview`, frontend `getSupplierPortalPreview` | `docs/plans/supplier-portal-preview/` |
| Sentinel SMS opt-in pattern (multi-subscriber) | DONE 2026-05-11 | Sentinel health checks (line 213, 220) | `backend/app/operations.py:create_sentinel_subscriber..opt_out_sentinel_subscriber`, `/sentinel/subscribers` POST/GET/confirm/opt-out, fan-out in `backend/app/sentinel.py:report_sentinel_error`, env-var fallback preserved | `docs/plans/sentinel-sms-opt-in/` |
| Email extraction preview endpoint | DONE 2026-05-11 | Phase 2 Inbox intake (line 2531-2566) | `POST /automation/extract-preview` in `backend/app/main.py:extract_preview`, frontend `extractFactsPreview` client | `docs/plans/email-extraction-preview/` |
| Audit log filter UI (admin) | DONE 2026-05-11 (build verified; browser sanity-check is operator follow-up) | Production-Grade audit standard (line 209-225) | `frontend/src/api.ts:getAuditEvents`, audit-filter form + results table inside `frontend/src/App.tsx` `adminView === 'audit'` block | `docs/plans/audit-filter-ui/` |
| Supplier profile claim workflow | DONE 2026-05-11 | Supplier-side wedge (line 260-310, 408-863) | `backend/app/operations.py:create_supplier_claim_link..accept_supplier_claim`, endpoints `POST /growth/supplier-leads/{id}/claim-link`, `GET /supplier-claim/{token}`, `POST /supplier-claim/{token}/accept`, frontend api clients | `docs/plans/supplier-profile-claim/` |
| DeliveryJob model + endpoints | DONE 2026-05-11 | Model spec (line 2968-2982), Phase 5 (line 3644-3679) | `backend/app/operations.py:create_delivery_job..update_delivery_job`, endpoints `POST/GET /bookings/{id}/delivery-jobs`, `PATCH /delivery-jobs/{id}`, frontend types + clients | `docs/plans/delivery-job/` |
| Partner capability + contingency option skeleton | DONE 2026-05-11 | Model spec (line 2712-2759), Phase 1-2 foundational (line 1939-1987) | `backend/app/operations.py` partner/capability/contingency operations, `/partners`, `/partners/{id}/capabilities`, `/partner-capabilities/{id}`, `/bookings/{id}/contingency-options`, `/contingency-options/{id}`, frontend types + clients | `docs/plans/partner-capability-skeleton/` |
| PaymentProof + LandedCostActual skeleton | DONE 2026-05-11 | Model spec (line 3056-3122), Phase 6 (line 3732-3849) | `backend/app/operations.py:record_payment_proof..record_landed_cost_actual`, endpoints `POST/GET /bookings/{id}/payment-proofs`, `PATCH /payment-proofs/{id}`, `POST/GET /bookings/{id}/landed-cost-actual`, frontend types + clients | `docs/plans/payment-proof-landed-cost/` |
| MarketplaceOrder model + ingest | DONE 2026-05-11 | Model spec (line 2535-2553), Step 2 Order (line 110-115), Account Integrations (line 102-106) | `backend/app/operations.py:record_marketplace_order..list_marketplace_orders`, endpoints `POST/GET /marketplace-orders`, frontend types + clients | `docs/plans/marketplace-order/` |
| InsurancePolicy + ClaimRecord skeleton | DONE 2026-05-11 | Model spec (line 3123-3157), Insurance/Claims/Exception Recovery (line 2130-2148) | `backend/app/operations.py:record_insurance_policy..update_claim_record`, endpoints `POST/GET /bookings/{id}/insurance-policy`, `POST/GET /bookings/{id}/claims`, `PATCH /claims/{id}`, frontend types + clients | `docs/plans/insurance-claim/` |
| `partner_update` SourceType enum value (cleanup) | DONE 2026-05-11 | Internal cleanup | Broker/carrier/trucker portal events now emit `source_type=partner_update`; `forwarder_confirmation` reserved for actual forwarder events. Frontend `SourceType` type updated. | (no separate plan; ad-hoc commit) |
| Cron-job.org wiring (was operator-blocked, unblocked) | DONE 2026-05-11 | Phase 5 Automation (line 174-181) | cron-job.org Job 7583175 hits `POST /automation/cron/run` every 15 minutes; `SHIP_HOPPA_CRON_TOKEN` rotated and matched between Railway and cron-job.org | (ops change, no code; verified HTTP 200 in cron-job.org history) |

### Overnight delivery 2026-05-11 (second wave) — DONE (PR #1)

| Feature | Status | Plan ref | Code path |
|---|---|---|---|
| Approval decision cards UI | DONE 2026-05-11 | Phase 3 Approval queue (line 3567-3603), Actions Must Be Decision Cards (line 2216) | `frontend/src/App.tsx` approvals-banner block now renders a `decision-card` per pending approval with Why / If approved / If no one acts copy and an Ask Ship Hoppa button calling `requestApprovalReview` |
| Sentinel SMS subscribers admin tab | DONE 2026-05-11 | Sentinel health checks (line 213, 220) | `frontend/src/App.tsx` `adminView === 'sentinel'` block, add/confirm/opt-out flow against `/sentinel/subscribers` |
| Growth + Suppliers + Imports admin tabs | DONE 2026-05-11 | Adoption loop, Supplier acquisition, Phase -2 saved import projects | `frontend/src/App.tsx` `adminView === 'growth' \| 'suppliers' \| 'projects'` blocks; new typed clients in `frontend/src/api.ts` for `/growth/attribution-events`, `/growth/attribution-summary`, `/growth/supplier-leads`, `/import-projects` |
| Email extraction preview modal | DONE 2026-05-11 | Phase 2 Inbox intake (line 2531-2566) | Try the parser modal in the customer Inbox, calls `extractFactsPreview` and shows facts table with confidence chips |
| Supplier portal preview button | DONE 2026-05-11 | Supplier-side wedge (line 260-310) | See what your supplier sees button on the customer Supplier tab opens a modal driven by `getSupplierPortalPreview` |
| Public supplier-claim landing page | DONE 2026-05-11 | Supplier-side wedge (line 408-863) | New `SupplierClaimView` SPA route at `/supplier-claim/{token}`. API moved to `/api/supplier-claim/{token}`; api client treats path as public; backend tests updated |
| Plain-language sweep across customer portal | DONE 2026-05-11 | Plain Language Rule (line 988), Decision Cards (line 2216) | Customer-facing labels: Warehouse cutoff → Arrive at warehouse by, Cargo ready → Goods ready by, Active holds / Release blockers → Delivery holds, Trucking estimate → Final delivery estimate, Rush service tier → Priority |
| Customer LandedCostActual + MarketplaceOrder + Insurance + Claim cards | DONE 2026-05-11 | Phase 5/6 spec, Marketplace ingest (line 2535-2553), Insurance/Claims (line 2130-2148) | Money tab now shows actual landed cost vs estimate with variance highlighted. Supplier tab adds marketplace order capture for Alibaba / 1688 / Made-in-China / Global Sources / direct supplier with order ID, product URL, payment method. Delivery tab adds insurance summary and claim drafting form (damage / loss / shortage / delay / other) |
| Customer DeliveryJob + PaymentProof cards | DONE 2026-05-11 | DeliveryJob spec (line 2968-2982), PaymentProof spec (line 3056-3094) | Delivery tab lists delivery jobs with mode, status pill that PATCHes, and a create form for the six modes. Money tab adds Payment proofs section with list (type, method, reference, amount, reconciliation status pill) and a record-payment form |
| Admin Partners directory | DONE 2026-05-11 | PartnerProfile + PartnerCapability spec (line 2712-2759), Phase 1-2 (line 1939-1987) | New Partners admin tab. Add a partner with name, type, contact email and phone, preferred channel. Click to view and add capabilities (regions, lanes, hours). |
| Admin ContingencyOption decision cards | DONE 2026-05-11 | ContingencyOption spec (line 2712-2759), Exception Recovery | Exceptions queue now shows contingency option cards under the selected shipment with Approve / Reject / Mark applied buttons. |

### No-blocker, autonomous — NOT STARTED (the new chat picks from here)

These can ship without operator action. All have clear seams in the
existing code; sizing is a rough guess.

| Feature | Plan ref | Adjacent code | Difficulty |
|---|---|---|---|
| **Snapshot / version restore endpoint** — let an importer roll back an `ImportProject` to an earlier version | Phase -2 Saved import projects (line 1939-1987) | `ImportProjectVersion` and `ImportProjectSnapshot` models exist; soft-delete shipped | Medium |
| **IA reframe to Today / Imports / Inbox / Approvals / Money / Space / Company** | Target Information Architecture (line 1031) | Existing Order/Ship/Deliver nav can coexist while migrating | Large |
| **Document AI extraction (v2 of inbox intake)** | §"Phase 2" Inbox intake (line 2531-2566) | Current `automation.py:extract_facts_from_text` is regex-only | Large |
| **Auto-route source messages to the right partner** | §"Ask The Best Person" (line 2186) | Today every chase goes to importer | Medium |
| **More Sentinel checks (low-confidence rate, supplier bank-detail change, ETA stale, etc.)** | §"Health Checks And Monitoring" (line 3927), §"Sentinel Error Code Registry" (line 3953) | Some shipped in `automation.py:check_stale_shipments`; many missing | Medium |

### Operator-blocked — BLOCKED on external setup

Don't start these without explicit go-ahead OR until the operator
provides credentials.

| Feature | Plan ref | What's needed | Difficulty |
|---|---|---|---|
| Wise FX quote integration | SupplierPayRequest workflow (line 3001-3030), model spec (line 3031-3055) | `WISE_API_TOKEN`, `WISE_PROFILE_ID` env vars on Railway. Operator said "do this last" | Small (adapter ready) |
| Microsoft 365 / Outlook OAuth inbox sync | Phase 2 Inbox intake (line 2531-2566), Email ingestion spec (line 2006-2044) | Azure AD app registration, OAuth consent, scheduled poller | Large |
| Google Workspace / Gmail OAuth inbox sync | Same as above | Google OAuth consent screen, polling | Large |
| Real ABF tariff API connector (Australia) | Customs source strategy (line 2077-2088), Launch Country Scope: Australia (line 196) | ABF API credentials, fallback chain, regulatory scope | Large |
| Real US tariff connector | Customs source strategy (line 2077-2088), Launch Country Scope: US (line 197) | USITC HTS data feed or third-party API | Large |
| Real sailing data feeds (CMA CGM, Maersk, MSC) | Phase 5+ contingency automation (around line 3644+) | Carrier API credentials, real-time event processing | Large |
| Image-only PDF OCR for supplier invoices | Phase 2 (line 2531-2566) | Tesseract or external OCR; Dockerfile system dependency | Medium |
| `SHIP_HOPPA_INBOUND_EMAIL_TOKEN` + Resend Inbound DNS | Email ingestion spec (line 2006-2044) | Operator sets env var + configures Resend dashboard | Tiny (operator action) |

### Big bets — NOT STARTED, large scope

These are weeks of work and benefit from operator scoping before
investing. Skeletons can be shipped autonomously; the full systems
need a real conversation.

| Feature | Plan ref | Scope |
|---|---|---|
| Supplier discovery enrichment pipeline (Alibaba, 1688, Made-in-China scraping + AI scoring) | Supplier acquisition strategy (line 408-863), Phase 7 backlog | Crawlers, enrichment, lead scoring, compliance filtering, outreach generation in EN + ZH, dedup. Models exist (`SupplierLead`, `SupplierDiscoveryRun`, `SEOOpportunity`); enrichment logic is missing |
| Real customs tariff integration (multi-country, with rules-based fallback) | Customs source strategy (line 2077-2088) | Multiple country APIs, regulatory scope, fallback chain (live → rules → manual review) |
| Real sailing data feeds + better-sailing contingency engine | Phase 5+ (around line 3644+) | Carrier APIs, baseline ETA tracking, automatic sailing-change detection, contingency option matching |
| Full payment proof + landed cost reconciliation (with Wise) | Phase 6 (line 3732-3849), model spec (line 3056-3094) | Multi-currency reconciliation state machine, variance rules, accounting export |
| Free supplier workspace (full deliverable, not just the portal) | Phase -0.5 Free supplier workspace (line 3412-3470) | New domain: company profile, upload staging, task tracking, buyer-facing status page, importer invite generation, supplier task automation |

### Polish + UI gaps — NOT STARTED

These are smaller follow-ups that compound the value of features
already shipped.

| Feature | Plan ref | What it adds |
|---|---|---|
| Frontend audit-log filter UI | Production-Grade audit standard (line 209-225) | Admin tab inputs for the new query params |
| Frontend admin tab for growth attribution dashboard | Adoption loop (line 261-310) | Visual ROI per source/channel/template chart |
| Frontend admin tab for supplier verification | Supplier acquisition (line 408-863) | Inbox-style queue of leads pending review |
| Chinese-language landing pages for supplier acquisition | Supplier acquisition (line 815-834, 1299) | `/cn/suppliers` plus category pages, WeChat-ready copy |
| Real binary file upload across portals | Production-Grade Standard (line 209-225) | Replaces placeholder JSON-only doc upload with multipart/binary |
| Shared `PartnerPortal` React component refactor | Internal architecture | Extract common shape from broker/warehouse/carrier/trucker portals (3+ instances now warrants the abstraction) |
| Rate limiting on token-based portals | Security best practice | Generic limiter shared across all four partner portals |
| Add `partner_update` `SourceType` enum value (DONE 2026-05-11) | Internal cleanup | Broker / carrier / trucker portal events now emit `source_type=partner_update`; `forwarder_confirmation` is reserved for actual forwarder events |

## How to start as the new chat

1. Read this file end to end (you just did).
2. Read `MEMORY.md` at
   `/Users/mitchbishop/.claude/projects/-Users-mitchbishop-Public-Projects-Ship-Hoppa/memory/MEMORY.md`.
3. `cd /Users/mitchbishop/Public/Projects/Ship-Hoppa/.claude/worktrees/reverent-maxwell-263429`
4. `git fetch && git status -sb` — should be clean on
   `claude/reverent-maxwell-263429`.
5. `git log --oneline -15` — see what was last shipped.
6. `cd backend && python3 -m pytest tests/ -q` — confirm 306 pass.
7. `cd ../frontend && npm run build` — confirm clean build.
8. Pick the next item from the **No-blocker, autonomous** section
   above. Plan it in
   `/Users/mitchbishop/Public/Projects/Ship-Hoppa/.claude/worktrees/reverent-maxwell-263429/docs/plans/<feature-name>/`.
   Run AP1. Execute. Run AP2. Tick exit criteria. Commit. Push.
9. Update this `HANDOVER.md` ledger: move the row from NOT STARTED
   to DONE with the date and the new test count.
10. Update PR #1 description so the new feature shows up in the
    summary.
11. Repeat.

If the operator wakes up and asks you something different, drop
what you're doing and follow his lead. Otherwise, keep shipping.

End of handover.
