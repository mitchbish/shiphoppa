# Ship Hoppa Deployment

Ship Hoppa is split into two hosted services:

- Railway runs the FastAPI backend from `backend/`.
- Vercel runs the customer/admin app from `frontend/`.
- Vercel runs the public marketing website from `marketing/`.

This keeps the operating API and the customer/admin website separate while still living in one project folder.

Current production URLs:

- Marketing website: `https://shiphoppa.com`
- Marketing website AU: `https://shiphoppa.com.au`
- App: `https://app.shiphoppa.com`
- App AU: `https://app.shiphoppa.com.au`
- App fallback: `https://ship-hoppa.vercel.app`
- API: `https://ship-hoppa-api-production.up.railway.app`

## Railway API

The repo includes `railway.toml` and a backend `Dockerfile`, so Railway can build the backend from the project root.

Required Railway variables:

```bash
SHIP_HOPPA_ENV=production
SHIP_HOPPA_IMPORTER_TOKEN=<strong random token>
SHIP_HOPPA_ADMIN_TOKEN=<strong random token>
SHIP_HOPPA_ALLOWED_ORIGINS=https://<your-vercel-domain>
SHIP_HOPPA_ALLOWED_ORIGIN_REGEX=https://.*\.vercel\.app
SHIP_HOPPA_STORE_SNAPSHOT_ENABLED=1
```

Optional dev/staging snapshot path:

```bash
SHIP_HOPPA_STORE_SNAPSHOT_PATH=/data/store_snapshot.json
```

The JSON snapshot is a bridge so the prototype can survive restarts. For a public production launch, move these same collections into Railway Postgres and keep Cloudflare R2 as the secure backup layer for files.

Optional provider variables now checked by `/system/health`:

```bash
RESEND_API_KEY=<resend key>
RESEND_FROM_EMAIL=<verified sender>
TWILIO_ACCOUNT_SID=<twilio sid>
TWILIO_AUTH_TOKEN=<twilio token>
TWILIO_FROM_NUMBER=<twilio number>
GOOGLE_CLIENT_ID=<google oauth client>
MICROSOFT_CLIENT_ID=<microsoft oauth client>
CLOUDFLARE_R2_ACCOUNT_ID=<r2 account>
CLOUDFLARE_R2_ACCESS_KEY_ID=<r2 access key>
CLOUDFLARE_R2_SECRET_ACCESS_KEY=<r2 secret>
CLOUDFLARE_R2_BUCKET=<r2 bucket>
WISE_API_TOKEN=<wise token>
OFX_API_KEY=<ofx key>
DCSA_API_KEY=<dcsa key>
PROJECT44_API_KEY=<project44 key>
VIZION_API_KEY=<vizion key>
```

Generate tokens locally with:

```bash
openssl rand -hex 32
```

Railway uses:

```bash
docker build .
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT
```

The health check is:

```text
/health
```

## Vercel App

The repo includes `vercel.json`, so Vercel can build the frontend from the project root.

Required Vercel variables:

```bash
VITE_API_BASE_URL=https://<your-railway-api-domain>
VITE_IMPORTER_TOKEN=<same value as SHIP_HOPPA_IMPORTER_TOKEN>
VITE_ADMIN_TOKEN=<same value as SHIP_HOPPA_ADMIN_TOKEN>
```

Vercel uses:

```bash
npm --prefix frontend ci
npm --prefix frontend run build
```

and serves:

```text
frontend/dist
```

## Vercel Marketing Website

The marketing website is a separate Vercel project deployed from `marketing/`.

It is static HTML and serves:

```text
marketing/index.html
```

Root website domains point here:

```text
shiphoppa.com
www.shiphoppa.com
shiphoppa.com.au
www.shiphoppa.com.au
```

App domains point to the Vite app project:

```text
app.shiphoppa.com
app.shiphoppa.com.au
```

Recommended DNS records:

```text
A      @     76.76.21.21
CNAME  www   cname.vercel-dns.com
A      app   76.76.21.21
```

## Production Note

The current token setup is acceptable for a private prototype, but not a public production launch. Before opening the app publicly, replace the shared frontend tokens with real user authentication and role-based sessions.

The current persistence setup is also a bridge, not the final database architecture. Use Railway Postgres as the primary source of truth before onboarding live customers.
