# Ship Hoppa — Handover

This document is for the next agent or developer picking up the work. Read it
end to end before making any changes.

## What this product is

Ship Hoppa turns scattered import paperwork (supplier emails, PDF invoices,
forwarder updates, broker notes) into one live shipment record per import.
The goal is zero manual data entry: the importer forwards an email, Ship
Hoppa parses, matches, and acts. Customer portal is organised in four
phases:

- **Account** — profile, contacts, integrations
- **Order** — supplier discovery, purchase orders, production, inspection,
  supplier payment, order-side documents
- **Ship** — FCL, MCL (the primary revenue mode), or LCL transport from
  origin port to destination port, with live tracking
- **Deliver** — customs, release, destination delivery

Phase 3 was previously called "Clear". The user prefers "Deliver". Don't
revert that.

## Where everything lives

### Local working tree

`/Users/mitchbishop/Public/Projects/Ship-Hoppa/`

```
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
    persistence.py      Optional snapshot to disk (so a restart doesn't wipe state)
    auth.py             Bearer-token auth (importer / admin / cron principals)
  tests/
    test_automation.py  Most automation, invoice, inspection, ETA, provider tests
    test_*.py           Other test files
  requirements.txt

frontend/               React + TypeScript + Vite SPA
  src/
    App.tsx             ~7000 lines, single-file SPA. Customer + admin views.
    api.ts              Frontend API client. Token routing per endpoint.
    types.ts            Shared TypeScript types mirroring backend models.
    App.css             All styles.

marketing/              DO NOT TOUCH. Owned by another chat session.
index.html              DO NOT TOUCH. Owned by another chat session.
vercel.json             DO NOT TOUCH.
Dockerfile              Multi-stage: Node builds frontend, Python serves both.
railway.toml            Railway service config.

docs/
  IMPORT_AUTOMATION_BUILD_PLAN.md   Full product spec. Long. Authoritative for vision.

HANDOVER.md             This file.
```

### Memory (Claude-only persistent context)

`/Users/mitchbishop/.claude/projects/-Users-mitchbishop-Public-Projects-Ship-Hoppa/memory/MEMORY.md`

Read it before doing anything. Key entries:

- **Session scope = app only**. This chat owns the Railway backend + frontend.
  Another chat owns the Vercel marketing site. Never edit `marketing/`, root
  `index.html`, or `vercel.json`.
- **No em dashes**. The user has explicitly banned em dashes in copy. Use
  periods, commas, or restructure the sentence.
- **Use `npm run build` to verify frontend changes**. `tsc --noEmit` misses
  errors that the production build catches; the user got a wave of Railway
  build-failed emails when I relied on `tsc --noEmit`. Always run
  `cd frontend && npm run build` before pushing.
- **Push as you go**. Every push to `main` auto-deploys to Railway. The
  user wants visible progress fast, not batched commits.
- **Provider credentials**: Resend keys come from the user's Resend dashboard.
  Twilio creds are reused from the user's Systematicly project. Wise is
  deferred to last.

## Deployment

- GitHub: `mitchbish/shiphoppa`, branch `main`. Push directly, no PR flow.
- Railway runs the **whole app** (backend + frontend) at
  `https://ship-hoppa-api-production.up.railway.app`. The Dockerfile is a
  multi-stage build. Railway auto-deploys on every push to `main`.
- Vercel runs only the marketing site at `marketing/` and root `index.html`.
  Different chat handles that.
- Project on Railway is named `Ship Hoppa API`. Logged-in CLI works; you can
  use `railway status`, `railway domain`, etc. from
  `/Users/mitchbishop/Public/Projects/Ship-Hoppa/`.

## Auth tokens (dev)

- Admin: `Bearer shiphoppa-admin-dev`
- Importer: `Bearer shiphoppa-importer-dev`
- Cron: `Bearer shiphoppa-cron-dev`

In production, these are environment variables (`SHIP_HOPPA_ADMIN_TOKEN`,
`SHIP_HOPPA_IMPORTER_TOKEN`, `SHIP_HOPPA_CRON_TOKEN`). The dev tokens won't
work against the live deploy.

## Environment variables (Railway)

Already set as of 2026-05-10:

- `RESEND_API_KEY`, `RESEND_FROM_EMAIL`
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`
- `SHIP_HOPPA_LIVE_PROVIDERS=true` (master switch — without this, no live
  sends happen even if creds are present)
- `SHIP_HOPPA_ENV=production`
- Persistence + tokens

Not yet set:

- `WISE_API_TOKEN` — deferred to last per user instruction
- `SHIP_HOPPA_OPS_PHONE` — needed for P0/P1 Sentinel SMS alerts to fire

To add an env var, run from the repo root:

```bash
railway variables --set "KEY=value"
```

Railway redeploys automatically.

## Commands you'll need

```bash
# Run the full backend test suite (must stay green)
cd backend && python3 -m pytest tests/

# Build the frontend the same way Railway does (use this, not tsc --noEmit)
cd frontend && npm run build

# Check Railway state
railway status
railway domain
railway logs

# Check live health
curl https://ship-hoppa-api-production.up.railway.app/health
```

## What's been built (state on 2026-05-10)

153 backend tests passing. Frontend builds clean. All shipped to Railway.

### Customer portal

- Phase nav: Order / Ship / Deliver, plus Account in the header
- Account: profile, integrations, help, inbox, notifications
- Order: supplier, production, inspection (book inspector + result flow),
  supplier pay (paste invoice text or upload PDF, auto-match to PO,
  auto-create approval), order docs
- Ship: cargo (booking form), ship docs, pickup, sailings, tracking
- Deliver: customs (with HS code suggestions and one-click accept),
  payments (with full landed-cost table), delivery
- Pending approvals banner at top of workspace, one-click approve/reject
- Next-steps banner with derived lifecycle state and missing-data items
- Notifications bell with unread count, mark-read, auto-creation on
  approvals and status advancement
- Tracking cards show pending-approval count per shipment
- Smart landing: returning users go to Tracking, new users go to booking form
- FCL spare-space recovery panel
- Background polling every 30s for new approvals and notifications

### Backend automation

- Lifecycle state machine (28 states, derived from booking + events + customs)
- Fact extraction from text (booking IDs, container numbers, ETAs, vessel,
  voyage, CBM, weight, invoice amounts, HS codes, etc.)
- Supplier invoice extractor (text and PDF), auto-applies to matched PO
- Auto-extract on inbound source messages (keyword detection)
- Auto-create approvals for customs submission, final delivery booking,
  cargo release, sailing changes (3+ day baseline slip), invoice variance
- Auto-advance booking status on warehouse_received / loaded / departed /
  arrived events
- Quality inspection booking + result flow (failed/rework creates approval,
  passed creates notification)
- Carrier ETA monitoring (notify on 1+ day shift, approval on 3+ day
  baseline slip)
- Warehouse cargo measurement variance (10% threshold creates
  approve_invoice_variance)
- Stale shipment checks (overdue cargo ready, cutoff risk, arrival without
  customs, stale release holds)
- Email template registry with safe variable substitution
- HS code suggestions (rules-based) for customs profile

### Outbound

- Resend (email), Twilio (SMS), Wise (FX) adapters under
  `backend/app/providers.py`. Two-layer safety: env vars must be set AND
  `SHIP_HOPPA_LIVE_PROVIDERS=true`.
- `dispatch_outbound_message` in `operations.py` sends a queued message via
  the right provider. "Deferred" status when not configured leaves the
  message queued for later.
- Cron endpoint `/automation/cron/run` runs the automation cycle then
  dispatches up to 100 queued messages per tick. Use this from a Railway cron.
- Test endpoints `/system/test-provider/email` and `/sms` for one-shot
  verification.
- Sentinel reporter `report_sentinel_error` in `sentinel.py`: logs an audit
  event, optionally creates an admin task, and fires Twilio SMS for P0/P1
  codes with 10-minute per-code cooldown.

### Admin

- Exception queue with auto-generated admin tasks (resolve / waive / open
  shipment)
- Automation panel with run-all button and stale alerts
- System health endpoint with provider readiness
- Sentinel error code registry (`SH-XYYY` format)

## Critical things to NOT do

1. **Don't touch `marketing/`, root `index.html`, `vercel.json`.** Another
   chat owns the Vercel marketing site. If `git status` shows changes there,
   `git checkout` them before committing.
2. **Don't use em dashes** in any copy you write (UI strings, marketing,
   comments, commit messages).
3. **Don't trust `tsc --noEmit` to catch frontend errors.** Always run
   `npm run build` before pushing. Use the same command Railway uses.
4. **Don't internal-codename anything.** The user has been clear: status
   updates and commit messages should be plain English, not "F11 lands
   3855776 in lib/foo.ts:42".
5. **Don't batch commits.** Push as you finish each cohesive change.
   Railway redeploys per push and the user expects to see live progress.
6. **Don't read another project's `.env` files** to harvest credentials.
   The sandbox blocks it for good reason. Tell the user to copy via
   Railway dashboard or paste them in chat themselves.
7. **Don't write secrets to memory or repo files.** Memory and repo are
   readable; credentials go to Railway env vars only.

## Next steps (priority-ordered)

### 1. Verify live providers actually send (5 minutes)

```bash
# Email test (replace with your actual address)
curl -X POST https://ship-hoppa-api-production.up.railway.app/system/test-provider/email \
  -H "Authorization: Bearer $SHIP_HOPPA_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to":"you@example.com","subject":"Live test","body":"Hello from production."}'

# SMS test
curl -X POST https://ship-hoppa-api-production.up.railway.app/system/test-provider/sms \
  -H "Authorization: Bearer $SHIP_HOPPA_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to":"+61...","body":"Ship Hoppa SMS test"}'
```

If either returns `"sent": false`, check `/system/providers` to see which
flag is wrong. The user has confirmed env vars are set; if a send fails
it's likely the Resend domain isn't verified yet.

### 2. Set `SHIP_HOPPA_OPS_PHONE` to enable P0/P1 alerts

Without this env var, the Sentinel reporter logs P0/P1 errors but never
fires the SMS. To set it:

```bash
cd /Users/mitchbishop/Public/Projects/Ship-Hoppa
railway variables --set "SHIP_HOPPA_OPS_PHONE=+61..."
```

### 3. Wire a Railway cron to hit `/automation/cron/run` every 15 min

This is the missing piece for the system to be fully self-running. The
endpoint exists but nothing fires it on a schedule.

In Railway: Add a new service (or use the existing one with a different
command), schedule a cron job that runs:

```bash
curl -X POST https://ship-hoppa-api-production.up.railway.app/automation/cron/run \
  -H "Authorization: Bearer $SHIP_HOPPA_CRON_TOKEN"
```

### 4. Wise API integration (deferred)

User said "WE will do the Wire API last." Don't start this without
explicit go-ahead. When the time comes:

- Sign up for Wise Business API
- Set `WISE_API_TOKEN` and optionally `WISE_PROFILE_ID` on Railway
- The adapter at `backend/app/providers.py:get_fx_quote_via_wise` is ready;
  it'll start returning real quotes once the env var is set and the
  master switch is on
- Wire `generate_supplier_pay_quotes` in `operations.py` to call Wise
  instead of using its hard-coded synthetic rates

### 5. Big still-missing features

In the build plan but not yet built:

- **Supplier discovery enrichment pipeline**. The models exist
  (`SupplierLead`, `SupplierDiscoveryRun`, `SEOOpportunity`) and the seed
  data references them, but there's no actual enrichment logic. Plan
  expects: fetch lead from a source, enrich via web scrape or third-party
  API, score, queue for outreach.
- **Real customs source connectors**. `backend/app/customs.py` has a
  rules-based HS suggester but no live ABF / US tariff API integration.
  When the time comes, wire it as a fallback path: try the live API first,
  fall back to the rules table if it fails.
- **Image-only PDF support**. Current `extract_invoice_from_pdf` uses
  `pypdf` text extraction which fails on scanned PDFs. Adding Tesseract
  OCR would handle these but adds a system dependency to the Dockerfile.
- **Supplier portal polish**. Suppliers can already use the portal via
  a token link, but the importer-side preview ("see what your supplier
  sees") doesn't exist yet.
- **Audit log viewer enhancements**. The admin Audit tab exists but is
  thin. Filtering by actor, event type, and shipment would be useful.

## How to start as the next agent

1. Read this file end to end (you just did).
2. Read `MEMORY.md` at the path above.
3. `cd /Users/mitchbishop/Public/Projects/Ship-Hoppa`
4. `git fetch && git status -sb` to see if anything's drifted.
5. `git log --oneline -10` to see what was last shipped.
6. `cd backend && python3 -m pytest tests/` to confirm 153 tests pass.
7. `cd ../frontend && npm run build` to confirm clean frontend build.
8. Then start the user's task. Push as you go.

If the user asks you to do something that touches `marketing/` or
`index.html`, refuse and remind them another chat owns that. If they
ask you to commit a credential anywhere, refuse and tell them to put it
in Railway env vars.

End of handover.
