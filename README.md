# Ship Hoppa MCL Platform

MVP foundation for Ship Hoppa, a Marketplace Container Load platform for splitting FCL container costs across compatible importers.

## What is included

- FastAPI backend with seeded South China to Brisbane lane, carrier services, warehouse, anchor cargo, and in-app notifications.
- Lane detection, container matching, density-complement scoring, capacity recalculation, release checks, and semi-automated carrier ranking/commit.
- React importer flow for booking, match result, price comparison, confirmation, supplier delivery instructions, and tracking state.
- React admin dashboard for containers, fill bars, release checks, carrier options, booking list, and notification feed.
- Dev-token RBAC for importer/admin paths, idempotency keys on mutating API calls, lifecycle guards, and audit events for operational state changes.
- Local snapshot persistence for the operating backbone, so bookings, import projects, documents, events, invoices, source messages, and growth runs survive API restarts during dev/staging.
- Sentinel-style health checks, Ship Hoppa error-code registry, and an outbound message queue for future Resend/Twilio/Email Manager automation.
- Production control, purchase orders, QC milestones, Supplier Pay quote comparison, approval cards, and an optional mark-paid-outside-app flow.
- Customer Production tab that turns a booking into an order-to-ready workflow without exposing the user to operational complexity.
- Unit and API integration tests covering matching, no-lane handling, carrier scoring, release triggers, auth, idempotency, duplicate commit prevention, and booking-to-carrier commit flow.

## Run locally

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

The app expects the API at `http://localhost:8000`. Override with `VITE_API_BASE_URL` if needed.

Default local auth tokens:

```bash
SHIP_HOPPA_IMPORTER_TOKEN=shiphoppa-importer-dev
SHIP_HOPPA_ADMIN_TOKEN=shiphoppa-admin-dev
```

The frontend sends matching dev tokens by default. Override with `VITE_IMPORTER_TOKEN` and `VITE_ADMIN_TOKEN`.

## Verify

```bash
cd backend
.venv/bin/pytest -q

cd ../frontend
npm run lint
npm run build
```

## Deploy

Ship Hoppa is set up as a two-service app:

- Railway runs the FastAPI backend from `backend/`.
- Vercel runs the customer/admin app from `frontend/`.
- Vercel runs the public marketing website from `marketing/`.

Current hosted URLs:

- Marketing website: `https://shiphoppa.com`
- Marketing website AU: `https://shiphoppa.com.au`
- App: `https://app.shiphoppa.com`
- App AU: `https://app.shiphoppa.com.au`
- App fallback: `https://ship-hoppa.vercel.app`
- API: `https://ship-hoppa-api-production.up.railway.app`

The deployment config lives in `railway.toml` and `vercel.json`. See `DEPLOYMENT.md` for the required Railway and Vercel environment variables.

## Current MVP boundaries

- Data uses an in-memory store with a JSON snapshot bridge for dev/staging. Production should move the same model boundaries to Railway Postgres before public launch.
- Importer identity is created from the booking form email; full registration/login is the next backend slice.
- Carrier rates and schedules are seeded/manual for Phase 1, ready to be replaced by live Freightos/Freightify integrations later.
