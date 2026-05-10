# Email ingestion endpoint

A webhook-shaped endpoint that turns inbound emails (from Resend
Inbound, Mailgun, SendGrid Inbound, or any forwarder POSTing JSON)
into Ship Hoppa source messages. The existing matching, fact
extraction, and approval-creation automation does the rest.

## Why this matters

The build plan's core value proposition is "forward an email, Ship
Hoppa builds the workflow." Until this endpoint exists, the only way
to feed source messages into Ship Hoppa is the importer-side POST
`/source-messages` (in-app), which doesn't capture the magic moment
of forwarding from a real inbox.

## Phase

Single-phase Tier 2 — backend-only. No frontend surface. (When the
user wires DNS / configures the webhook in Resend, the endpoint
goes live. UI work can come in a follow-up if needed.)

## Goal

A webhook caller can POST JSON to `/inbound/email` with a shared
secret, the payload is parsed into a `SourceMessageCreate`, and
`ingest_source_message` does the rest. Existing automation (booking
match + fact extraction) fires through the same path as in-app
ingestion.

## Files to touch

- `backend/app/auth.py` — add `require_inbound_webhook` similar to
  `require_cron`. Reads `SHIP_HOPPA_INBOUND_EMAIL_TOKEN`; falls back
  to `shiphoppa-inbound-dev` in dev.
- `backend/app/main.py` — new endpoint `POST /inbound/email`. Accepts
  a vendor-flexible JSON body. Maps to `SourceMessageCreate`. Calls
  `ingest_source_message(store, payload, ActorRole.system,
  "inbound-webhook")`.
- `backend/app/models.py` — `InboundEmailWebhook` model that accepts
  multiple inbound shapes (from/to as string or object with email
  field; html/text body; attachments as list of objects with
  filename or just a filename string).
- `backend/tests/test_inbound_email.py` — new tests:
  1. Missing token → 401.
  2. Invalid token → 401.
  3. Valid Resend-shaped payload creates a SourceMessage with
     `source_type=forwarded_email` and the right from/subject/body.
  4. Email body that mentions an existing booking number gets matched
     to that booking (existing matching logic exercises the new path).
  5. Mailgun-shaped payload (different field names) is also accepted.

## Out of scope

- DNS / inbound-email service configuration (user does this in Resend
  dashboard). Document the URL in HANDOVER notes after merge.
- Email signature parsing / HTML-to-text conversion (leave as-is for
  now; the body field accepts both text and HTML).
- Attachment binary storage (attachment names are recorded;
  Resend/Mailgun include file content base64 inline, which would need
  a binary-upload pipeline — separate gap).
- Outbound bounce / delivery webhooks (separate concern).

## AP1 audits

#### Lens 1 — Correctness (2026-05-11 09:05 AEST)

(a) Likely-wrong: that all inbound webhook payloads share a clean
    shape. Resend wraps the email in `{from: {email}, to: [{email}]}`.
    Mailgun uses flat `{sender, recipient, subject, body-plain}`.
    SendGrid Inbound uses multipart form, not JSON. For now: support
    Resend-shaped JSON cleanly; add Mailgun shape via field aliases;
    SendGrid users will need to format JSON before POSTing or use a
    middleware. Documented in plan.
(b) Weakest exit: test #3 "creates a SourceMessage". Could pass even
    if `ingest_source_message` is bypassed. Tighten: also assert the
    SourceMessage's `id` appears in `store.source_messages` and that
    its `source_type` is `forwarded_email`.
(c) Domain expert (security engineer): would want HMAC verification
    in addition to bearer-token auth. Out of scope for this slice;
    bearer-token + HTTPS is acceptable for v1. Backlog.
(d) Leaving on the table: deduplication by Message-ID header. If
    Resend retries a failed delivery, we get duplicate SourceMessages.
    Acceptable for v1 — `match_source_message_to_booking` is
    idempotent at the SourceMessage level (each gets a new ID).
    Backlog.
(e) Unintended consequence: an attacker with the inbound token can
    spam create source messages. Mitigation: rotate the token if
    leaked. Same risk as the cron token. Acceptable.

#### Lens 2 — Adversarial (2026-05-11 09:08 AEST) — reviewer persona: a security engineer who's seen plenty of webhook abuse

(a) Likely-wrong: that bearer-token alone is enough. HMAC of the
    payload would be stronger. Logged as backlog. Bearer over HTTPS
    is OK for v1.
(b) Tightened test #3 already.
(c) Body size limit: a 50MB email could OOM the server. FastAPI has
    no default body limit; uvicorn has `--limit-request-line` but no
    body-size flag. Mitigation: trust Resend/Mailgun to reject
    massive emails upstream. Acceptable for v1 with a backlog note.
(d) Source field validation: `from_address` should be validated as
    an email-shaped string. Pydantic `EmailStr` would do this if
    available. Use `EmailStr` if installed; else a regex check.
    Pragmatic note: existing `SourceMessageCreate` doesn't validate
    either, so don't over-tighten just here.
(e) Auth header parsing: same `HTTPBearer(auto_error=False)` pattern
    as `require_cron`. Token-not-present → 401 with clear message.

#### Plan revisions

- Test #3 asserts SourceMessage appears in `store.source_messages`
  with `source_type=forwarded_email`.
- Backlog notes added: HMAC verification, dedup by Message-ID,
  body-size enforcement.
- `InboundEmailWebhook` model uses Pydantic field aliases to accept
  both Resend (`from.email`) and Mailgun (`sender`) shapes.

## Status — DONE 2026-05-11

7 new tests pass (`tests/test_inbound_email.py`); full suite at 184.

#### AP2 Lens 1 — Correctness (2026-05-11 09:30 AEST)

(a) Confirmed: `from` is a Python keyword, so the Pydantic field is
    declared as `from_field: Optional[Any] = Field(default=None,
    alias="from")`. Works via `populate_by_name = True`. Test #3
    confirms the alias works.
(b) Mailgun-style flat fields (sender, recipient, body-plain) map
    cleanly via separate aliased fields. Test #4 confirms.
(c) Booking-ID matching (test #5) routes through the existing
    `match_source_message_to_booking` logic — no new pathway. The
    inbound endpoint is just a thin shape-converter on top of the
    same `ingest_source_message`.
(d) HTML-only body (test #6) falls through to `payload.html` after
    text/body_plain are empty. Confirmed.
(e) 422 on missing sender (test #7) prevents downstream None-string
    from polluting the audit log.

#### AP2 Lens 2 — Adversarial (2026-05-11 09:33 AEST) — reviewer persona: a security/SRE engineer reviewing a webhook PR

(a) Bearer-token auth via `require_inbound_webhook` matches the
    `require_cron` pattern. Same operational characteristics: rotate
    the env var to revoke. HMAC verification noted on backlog.
(b) Body parsing is permissive — unknown fields are ignored. Pydantic
    will not 422 on extra Resend-specific metadata fields like
    `delivered_at` or `headers`.
(c) `_coerce_inbound_addresses` is defensive: handles list of dicts,
    list of strings, single string, missing. Tested via Resend +
    Mailgun shapes.
(d) Attachment names are recorded but binary content is not stored.
    Backlog: real binary attachment pipeline.
(e) Empty body fields all-falsy → SourceMessage body = "". Acceptable;
    `match_source_message_to_booking` will get `extraction_status =
    needs_review`.

#### AP2 findings — none blocking

The endpoint is shippable. Documentation should call out:
- Configure Resend Inbound (or Mailgun) to POST to
  `https://ship-hoppa-api-production.up.railway.app/inbound/email`
  with `Authorization: Bearer $SHIP_HOPPA_INBOUND_EMAIL_TOKEN`.
- Set `SHIP_HOPPA_INBOUND_EMAIL_TOKEN` on Railway before pointing
  any inbound provider at the endpoint.

## Follow-up backlog

- HMAC payload verification.
- Dedup by Message-ID header.
- Body-size limit enforcement.
- Real binary attachment storage pipeline.
- SendGrid Inbound shape support (multipart, not JSON).
- Stricter EmailStr validation on `from_address`.
- UI affordance: an "Inbound mailbox" panel in admin showing recently
  ingested webhook messages.
