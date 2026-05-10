# Ship Hoppa Deployment

Ship Hoppa is split into two hosted services:

- **Railway** runs the full app — both the FastAPI backend and the React frontend (built at Docker build time and served as static files by the API).
- **Vercel** runs the public marketing website from `marketing/`.

Current production URLs:

- Marketing website: `https://shiphoppa.com`
- Marketing website AU: `https://shiphoppa.com.au`
- App + API: `https://app.shiphoppa.com`
- App + API AU: `https://app.shiphoppa.com.au`
- App + API fallback: `https://ship-hoppa-api-production.up.railway.app`

## Railway (App + API)

The Dockerfile is a multi-stage build: stage 1 builds the Vite frontend, stage 2 runs the Python API and serves the frontend as static files. All API routes (`/health`, `/bookings`, etc.) are handled by FastAPI; all other routes fall through to the SPA `index.html`.

Required Railway variables:

```bash
SHIP_HOPPA_ENV=production
SHIP_HOPPA_IMPORTER_TOKEN=<strong random token>
SHIP_HOPPA_ADMIN_TOKEN=<strong random token>
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

## Vercel (Marketing Website)

The root `vercel.json` points Vercel at the `marketing/` directory. No build step — it's static HTML.

Root website domains point here:

```text
shiphoppa.com
www.shiphoppa.com
shiphoppa.com.au
www.shiphoppa.com.au
```

App domains point to Railway:

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

Since the frontend and API now share the same Railway domain, CORS is no longer required for the app itself. The CORS middleware remains for external API consumers — configure `SHIP_HOPPA_ALLOWED_ORIGINS` and `SHIP_HOPPA_ALLOWED_ORIGIN_REGEX` only if needed.

The current token setup is acceptable for a private prototype, but not a public production launch. Before opening the app publicly, replace the shared frontend tokens with real user authentication and role-based sessions.

The current persistence setup is also a bridge, not the final database architecture. Use Railway Postgres as the primary source of truth before onboarding live customers.
