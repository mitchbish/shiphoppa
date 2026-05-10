"""
Provider adapters for real outbound channels (email, SMS, FX quotes).

Every adapter respects two layers of safety:
  1. The relevant env vars must be set. If not, the adapter returns a
     "not configured" result and the caller queues the message for manual
     handling.
  2. The global feature flag SHIP_HOPPA_LIVE_PROVIDERS must equal "true".
     Without it the adapter does NOT call the provider, even if env vars
     are present. This protects against accidental sends in dev/staging
     when keys are loaded.

Adapters never raise; they return a structured result. The caller layers
on Sentinel error reporting and audit events.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx


def live_providers_enabled() -> bool:
    """Master switch. Set SHIP_HOPPA_LIVE_PROVIDERS=true in production."""
    return os.getenv("SHIP_HOPPA_LIVE_PROVIDERS", "").lower() in {"true", "1", "yes"}


def _result(
    sent: bool,
    provider: str,
    detail: str,
    provider_message_id: Optional[str] = None,
    error_code: Optional[str] = None,
    deferred: bool = False,
) -> Dict[str, Any]:
    return {
        "sent": sent,
        "provider": provider,
        "detail": detail,
        "provider_message_id": provider_message_id,
        "error_code": error_code,
        "deferred": deferred,
    }


# --- Email via Resend ---


def send_email_via_resend(
    to_addresses: List[str],
    subject: str,
    body: str,
    from_address: Optional[str] = None,
) -> Dict[str, Any]:
    api_key = os.getenv("RESEND_API_KEY")
    sender = from_address or os.getenv("RESEND_FROM_EMAIL")
    if not api_key or not sender:
        return _result(False, "resend", "Resend not configured.", error_code="SH-3403", deferred=True)
    if not live_providers_enabled():
        return _result(False, "resend", "Live providers disabled. Message stays queued.", deferred=True)
    if not to_addresses:
        return _result(False, "resend", "No recipients.", error_code="SH-3401")
    payload = {
        "from": sender,
        "to": to_addresses,
        "subject": subject,
        "text": body,
    }
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                "https://api.resend.com/emails",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )
        if response.status_code in (200, 201):
            data = response.json() if response.content else {}
            return _result(True, "resend", "Email sent.", provider_message_id=data.get("id"))
        if response.status_code == 429:
            return _result(False, "resend", "Resend rate limited.", error_code="SH-3402")
        return _result(False, "resend", f"Resend error {response.status_code}: {response.text[:200]}", error_code="SH-3401")
    except httpx.HTTPError as exc:
        return _result(False, "resend", f"Resend transport error: {exc!r}", error_code="SH-3401")


# --- SMS via Twilio ---


def send_sms_via_twilio(to_phone: str, body: str) -> Dict[str, Any]:
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")
    if not sid or not token or not from_number:
        return _result(False, "twilio", "Twilio not configured.", error_code="SH-3502", deferred=True)
    if not live_providers_enabled():
        return _result(False, "twilio", "Live providers disabled. SMS stays queued.", deferred=True)
    if not to_phone:
        return _result(False, "twilio", "No recipient phone number.", error_code="SH-3501")
    try:
        with httpx.Client(timeout=10.0, auth=(sid, token)) as client:
            response = client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                data={"From": from_number, "To": to_phone, "Body": body},
            )
        if response.status_code in (200, 201):
            data = response.json() if response.content else {}
            return _result(True, "twilio", "SMS sent.", provider_message_id=data.get("sid"))
        return _result(False, "twilio", f"Twilio error {response.status_code}: {response.text[:200]}", error_code="SH-3501")
    except httpx.HTTPError as exc:
        return _result(False, "twilio", f"Twilio transport error: {exc!r}", error_code="SH-3501")


# --- FX quote via Wise ---


def get_fx_quote_via_wise(
    source_currency: str,
    target_currency: str,
    amount: float,
) -> Dict[str, Any]:
    api_token = os.getenv("WISE_API_TOKEN")
    profile_id = os.getenv("WISE_PROFILE_ID")
    if not api_token:
        return _result(False, "wise", "Wise not configured.", error_code="SH-4201", deferred=True)
    if not live_providers_enabled():
        return _result(False, "wise", "Live providers disabled. Quote stays in sandbox.", deferred=True)
    if amount <= 0:
        return _result(False, "wise", "Quote amount must be positive.", error_code="SH-4201")
    payload: Dict[str, Any] = {
        "sourceCurrency": source_currency,
        "targetCurrency": target_currency,
        "sourceAmount": amount,
    }
    if profile_id:
        payload["profile"] = int(profile_id)
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                "https://api.transferwise.com/v3/quotes",
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_token}",
                    "Content-Type": "application/json",
                },
            )
        if response.status_code in (200, 201):
            data = response.json() if response.content else {}
            result = _result(True, "wise", "Wise quote received.", provider_message_id=str(data.get("id")))
            result["rate"] = data.get("rate")
            result["target_amount"] = data.get("targetAmount")
            return result
        return _result(False, "wise", f"Wise error {response.status_code}: {response.text[:200]}", error_code="SH-4201")
    except httpx.HTTPError as exc:
        return _result(False, "wise", f"Wise transport error: {exc!r}", error_code="SH-4201")


# --- Provider readiness summary ---


def provider_readiness() -> Dict[str, Dict[str, Any]]:
    """Quick summary used by /system/health and the admin UI."""
    live = live_providers_enabled()
    return {
        "resend": {
            "configured": bool(os.getenv("RESEND_API_KEY") and os.getenv("RESEND_FROM_EMAIL")),
            "live": live,
        },
        "twilio": {
            "configured": bool(
                os.getenv("TWILIO_ACCOUNT_SID")
                and os.getenv("TWILIO_AUTH_TOKEN")
                and os.getenv("TWILIO_FROM_NUMBER")
            ),
            "live": live,
        },
        "wise": {
            "configured": bool(os.getenv("WISE_API_TOKEN")),
            "live": live,
        },
    }
