import os
from datetime import datetime
from typing import Iterable, List, Optional

from .models import (
    AdminTaskStatus,
    ApprovalStatus,
    OutboundStatus,
    SentinelErrorDefinition,
    SentinelSeverity,
    SystemHealthCheck,
    SystemHealthResponse,
    SystemHealthStatus,
)
from .persistence import configured_snapshot_path, snapshot_enabled
from .store import Store


RUNBOOK_ROOT = "https://shiphoppa.com/admin/runbooks"


def now_utc() -> datetime:
    return datetime.utcnow().replace(microsecond=0)


def error_definition(
    code: str,
    category: str,
    severity: SentinelSeverity,
    user_safe_message: str,
    internal_message: str,
    retryable: bool,
    creates_admin_task: bool,
    sends_sms_alert: bool = False,
) -> SentinelErrorDefinition:
    return SentinelErrorDefinition(
        code=code,
        category=category,
        severity=severity,
        user_safe_message=user_safe_message,
        internal_message=internal_message,
        retryable=retryable,
        creates_admin_task=creates_admin_task,
        sends_sms_alert=sends_sms_alert,
        runbook_url=f"{RUNBOOK_ROOT}/{code.lower()}",
    )


SENTINEL_ERROR_REGISTRY = {
    "SH-3101": error_definition(
        "SH-3101",
        "database",
        SentinelSeverity.P0,
        "Ship Hoppa could not reach its main data store.",
        "Primary database or persistence layer is unavailable.",
        True,
        True,
        True,
    ),
    "SH-3201": error_definition(
        "SH-3201",
        "automation",
        SentinelSeverity.P1,
        "An automation run failed and needs review.",
        "Background job failed.",
        True,
        True,
        True,
    ),
    "SH-3202": error_definition(
        "SH-3202",
        "automation",
        SentinelSeverity.P1,
        "A scheduled automation did not run on time.",
        "Cron missed scheduled run.",
        False,
        True,
        True,
    ),
    "SH-3301": error_definition(
        "SH-3301",
        "email_ingestion",
        SentinelSeverity.P1,
        "Ship Hoppa could not read or process an incoming message.",
        "Source message extraction failed.",
        True,
        True,
        True,
    ),
    "SH-3302": error_definition(
        "SH-3302",
        "email_ingestion",
        SentinelSeverity.P2,
        "Several extracted details need review.",
        "Low-confidence extraction spike detected.",
        False,
        True,
    ),
    "SH-3303": error_definition(
        "SH-3303",
        "email_ingestion",
        SentinelSeverity.P2,
        "Email inbox connection is not configured yet.",
        "Google and Microsoft inbox ingestion credentials are missing.",
        False,
        True,
    ),
    "SH-3401": error_definition(
        "SH-3401",
        "email_delivery",
        SentinelSeverity.P1,
        "Ship Hoppa could not send an email.",
        "Resend API error.",
        True,
        True,
        True,
    ),
    "SH-3402": error_definition(
        "SH-3402",
        "email_delivery",
        SentinelSeverity.P2,
        "Ship Hoppa email sending is temporarily rate limited.",
        "Resend rate limited.",
        True,
        True,
    ),
    "SH-3403": error_definition(
        "SH-3403",
        "email_delivery",
        SentinelSeverity.P0,
        "Ship Hoppa email sending is not configured.",
        "Resend domain or API credentials are missing.",
        False,
        True,
        True,
    ),
    "SH-3501": error_definition(
        "SH-3501",
        "sms_delivery",
        SentinelSeverity.P1,
        "Ship Hoppa could not send an SMS.",
        "Twilio API error.",
        True,
        True,
        True,
    ),
    "SH-3502": error_definition(
        "SH-3502",
        "sms_delivery",
        SentinelSeverity.P2,
        "Ship Hoppa SMS sending is not configured yet.",
        "Twilio credentials are missing.",
        False,
        True,
    ),
    "SH-3503": error_definition(
        "SH-3503",
        "sms_delivery",
        SentinelSeverity.P1,
        "Ship Hoppa could not verify an incoming SMS update.",
        "Twilio webhook verification failed.",
        False,
        True,
        True,
    ),
    "SH-4101": error_definition(
        "SH-4101",
        "shipping_data",
        SentinelSeverity.P1,
        "Carrier or forwarder schedule data could not sync.",
        "Carrier or forwarder schedule sync failed.",
        True,
        True,
        True,
    ),
    "SH-4102": error_definition(
        "SH-4102",
        "shipping_data",
        SentinelSeverity.P2,
        "Live ETA data could not sync.",
        "Visibility provider ETA sync failed.",
        True,
        True,
    ),
    "SH-4301": error_definition(
        "SH-4301",
        "file_backup",
        SentinelSeverity.P2,
        "Secure file backup is not configured yet.",
        "Cloudflare R2 backup credentials are missing.",
        False,
        True,
    ),
    "SH-4201": error_definition(
        "SH-4201",
        "supplier_pay",
        SentinelSeverity.P1,
        "Supplier payment quote could not be created.",
        "Wise or OFX quote failed.",
        True,
        True,
        True,
    ),
    "SH-4202": error_definition(
        "SH-4202",
        "supplier_pay",
        SentinelSeverity.P2,
        "A supplier payment quote expired before approval.",
        "FX quote expired before approval.",
        False,
        True,
    ),
    "SH-5101": error_definition(
        "SH-5101",
        "supplier_discovery",
        SentinelSeverity.P2,
        "A supplier discovery source is unavailable.",
        "Supplier discovery source blocked or unavailable.",
        True,
        True,
    ),
    "SH-5102": error_definition(
        "SH-5102",
        "supplier_discovery",
        SentinelSeverity.P2,
        "Supplier lead enrichment failed.",
        "Supplier lead enrichment failed.",
        True,
        True,
    ),
    "SH-5103": error_definition(
        "SH-5103",
        "outreach_compliance",
        SentinelSeverity.P0,
        "Outreach suppression checks failed.",
        "Outreach suppression check failed.",
        False,
        True,
        True,
    ),
    "SH-5104": error_definition(
        "SH-5104",
        "outreach_compliance",
        SentinelSeverity.P0,
        "An opt-out could not be processed.",
        "Opt-out processing failed.",
        True,
        True,
        True,
    ),
    "SH-5105": error_definition(
        "SH-5105",
        "outreach_compliance",
        SentinelSeverity.P1,
        "A spam complaint needs immediate review.",
        "Spam complaint received.",
        False,
        True,
        True,
    ),
    "SH-5106": error_definition(
        "SH-5106",
        "outreach_compliance",
        SentinelSeverity.P1,
        "Supplier outreach has reached its daily safety limit.",
        "Outbound campaign exceeded daily limit.",
        False,
        True,
        True,
    ),
    "SH-6101": error_definition(
        "SH-6101",
        "supplier_pay",
        SentinelSeverity.P0,
        "Supplier bank details changed and must be reviewed before payment.",
        "Supplier bank details changed.",
        False,
        True,
        True,
    ),
    "SH-6102": error_definition(
        "SH-6102",
        "supplier_pay",
        SentinelSeverity.P1,
        "A payment approval is stuck.",
        "Payment approval stuck.",
        False,
        True,
        True,
    ),
    "SH-6103": error_definition(
        "SH-6103",
        "invoices",
        SentinelSeverity.P0,
        "Invoice and freight release status do not match.",
        "Invoice/release mismatch.",
        False,
        True,
        True,
    ),
    "SH-7101": error_definition(
        "SH-7101",
        "customs",
        SentinelSeverity.P2,
        "A customs estimate could not be calculated.",
        "Customs estimate failed.",
        True,
        True,
    ),
    "SH-7102": error_definition(
        "SH-7102",
        "customs",
        SentinelSeverity.P1,
        "A biosecurity risk needs review.",
        "Biosecurity flag requires review.",
        False,
        True,
        True,
    ),
    "SH-8101": error_definition(
        "SH-8101",
        "tracking",
        SentinelSeverity.P2,
        "A shipment route could not be rendered.",
        "Route rendering failed.",
        True,
        True,
    ),
}


def sentinel_error_definitions() -> List[SentinelErrorDefinition]:
    return [SENTINEL_ERROR_REGISTRY[code] for code in sorted(SENTINEL_ERROR_REGISTRY)]


def require_env(*names: str) -> bool:
    return all(bool(os.getenv(name)) for name in names)


def optional_env_any(names: Iterable[str]) -> bool:
    return any(bool(os.getenv(name)) for name in names)


def missing_status(code: str, production: bool) -> SystemHealthStatus:
    severity = SENTINEL_ERROR_REGISTRY[code].severity
    if production and severity in {SentinelSeverity.P0, SentinelSeverity.P1}:
        return SystemHealthStatus.failing
    return SystemHealthStatus.warning


def health_check(
    key: str,
    label: str,
    configured: bool,
    healthy_message: str,
    missing_message: str,
    code: Optional[str] = None,
    provider: Optional[str] = None,
    production: bool = False,
) -> SystemHealthCheck:
    status = SystemHealthStatus.healthy if configured else missing_status(code, production) if code else SystemHealthStatus.warning
    return SystemHealthCheck(
        key=key,
        label=label,
        provider=provider,
        status=status,
        configured=configured,
        message=healthy_message if configured else missing_message,
        sentinel_error_code=None if configured else code,
        last_checked_at=now_utc(),
    )


def system_health(store: Store) -> SystemHealthResponse:
    environment = os.getenv("SHIP_HOPPA_ENV", "development")
    production = environment == "production"
    checks: List[SystemHealthCheck] = []

    snapshot_is_enabled = snapshot_enabled()
    snapshot_path = configured_snapshot_path()
    snapshot_ready = snapshot_path.exists() if snapshot_is_enabled else not production
    checks.append(
        health_check(
            "persistence",
            "Primary data store",
            snapshot_ready,
            "Snapshot persistence is available for this prototype."
            if snapshot_is_enabled
            else "Snapshot persistence is disabled outside production.",
            "Snapshot persistence is not available. Use Railway Postgres before public production.",
            "SH-3101",
            "Railway Postgres / local snapshot",
            production,
        )
    )
    checks.append(
        health_check(
            "email_delivery",
            "Email sending",
            require_env("RESEND_API_KEY", "RESEND_FROM_EMAIL"),
            "Resend is configured for transactional and outreach email.",
            "Resend is not configured. Email actions remain queued/manual.",
            "SH-3403",
            "Resend",
            production,
        )
    )
    checks.append(
        health_check(
            "sms_delivery",
            "SMS sending",
            require_env("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER"),
            "Twilio is configured for urgent SMS and opt-out handling.",
            "Twilio is not configured. SMS actions remain queued/manual.",
            "SH-3502",
            "Twilio",
            production,
        )
    )
    checks.append(
        health_check(
            "email_ingestion",
            "Email ingestion",
            optional_env_any(["GOOGLE_CLIENT_ID", "MICROSOFT_CLIENT_ID"]),
            "Google or Microsoft inbox ingestion is configured.",
            "Email ingestion is not connected yet. Forwarded/admin-upload messages still work.",
            "SH-3303",
            "Google Workspace / Microsoft 365",
            production,
        )
    )
    checks.append(
        health_check(
            "file_backup",
            "Secure file backup",
            require_env("CLOUDFLARE_R2_ACCOUNT_ID", "CLOUDFLARE_R2_ACCESS_KEY_ID", "CLOUDFLARE_R2_SECRET_ACCESS_KEY", "CLOUDFLARE_R2_BUCKET"),
            "Cloudflare R2 backup is configured.",
            "Cloudflare R2 backup is not configured. Local uploads still work, but backup is missing.",
            "SH-4301",
            "Cloudflare R2",
            production,
        )
    )
    checks.append(
        health_check(
            "supplier_pay",
            "Supplier Pay quotes",
            optional_env_any(["WISE_API_TOKEN", "OFX_API_KEY"]),
            "At least one FX/payment quote provider is configured.",
            "Supplier Pay quote provider is not configured yet.",
            "SH-4201",
            "Wise / OFX",
            production,
        )
    )
    checks.append(
        health_check(
            "shipping_data",
            "Shipping data",
            optional_env_any(["DCSA_API_KEY", "PROJECT44_API_KEY", "VIZION_API_KEY"]),
            "Live shipping data provider credentials are configured.",
            "Live shipping data is not configured yet. Manual schedules remain the source of truth.",
            "SH-4101",
            "DCSA / project44 / Vizion",
            production,
        )
    )

    failed_outbound = [
        message for message in store.outbound_messages.values() if message.status == OutboundStatus.failed
    ]
    queued_outbound = [
        message for message in store.outbound_messages.values() if message.status == OutboundStatus.queued
    ]
    active_codes = {
        check.sentinel_error_code
        for check in checks
        if check.sentinel_error_code
    }
    active_codes.update(
        message.sentinel_error_code
        for message in failed_outbound
        if message.sentinel_error_code
    )
    active_error_definitions = [
        SENTINEL_ERROR_REGISTRY[code]
        for code in sorted(active_codes)
        if code in SENTINEL_ERROR_REGISTRY
    ]

    if any(check.status == SystemHealthStatus.failing for check in checks):
        overall = SystemHealthStatus.failing
    elif any(check.status == SystemHealthStatus.warning for check in checks) or failed_outbound:
        overall = SystemHealthStatus.warning
    else:
        overall = SystemHealthStatus.healthy

    return SystemHealthResponse(
        overall_status=overall,
        checked_at=now_utc(),
        environment=environment,
        checks=checks,
        active_error_codes=active_error_definitions,
        queued_outbound_messages=len(queued_outbound),
        failed_outbound_messages=len(failed_outbound),
        open_admin_tasks=sum(1 for task in store.admin_tasks.values() if task.status == AdminTaskStatus.open),
        open_approvals=sum(1 for approval in store.approval_requests.values() if approval.status == ApprovalStatus.pending),
    )


# --- Sentinel reporter ---
# Module-level cooldown tracker so the same error code does not spam SMS.
# Maps code -> last fired datetime.
_SMS_COOLDOWNS: dict = {}
SMS_COOLDOWN_SECONDS = 600  # 10 minutes per error code


def report_sentinel_error(
    store: Store,
    code: str,
    context: Optional[dict] = None,
    related_booking_id: Optional[str] = None,
) -> dict:
    """
    Log an audit event for a Sentinel error code, optionally create an
    admin task, and fire a Twilio SMS alert for P0/P1 codes (with a per-code
    cooldown). Returns a result dict describing what fired.
    """
    from .operations import create_admin_task, create_audit_event
    from .providers import send_sms_via_twilio
    from .models import ActorRole

    definition = SENTINEL_ERROR_REGISTRY.get(code)
    if not definition:
        return {"reported": False, "reason": f"Unknown sentinel code {code}"}

    safe_context = {k: v for k, v in (context or {}).items() if not _looks_sensitive(k)}

    create_audit_event(
        store,
        ActorRole.system,
        "sentinel",
        "sentinel_error_reported",
        "sentinel_error",
        code,
        definition.internal_message,
        {
            "code": code,
            "category": definition.category,
            "severity": definition.severity.value,
            "retryable": definition.retryable,
            **safe_context,
        },
    )

    admin_task_id: Optional[str] = None
    if definition.creates_admin_task and related_booking_id:
        booking = store.bookings.get(related_booking_id)
        if booking:
            task = create_admin_task(
                store,
                booking,
                f"sentinel_{code.lower()}",
                f"{code} {definition.user_safe_message}",
            )
            admin_task_id = task.id

    sms_results: List[dict] = []
    if definition.sends_sms_alert and definition.severity in {SentinelSeverity.P0, SentinelSeverity.P1}:
        last_fired = _SMS_COOLDOWNS.get(code)
        now = now_utc()
        if last_fired is None or (now - last_fired).total_seconds() >= SMS_COOLDOWN_SECONDS:
            from .operations import active_sentinel_phone_numbers

            phones = active_sentinel_phone_numbers(store)
            sms_body = f"[{code}] {definition.user_safe_message}"
            any_sent = False
            for phone in phones:
                try:
                    result = send_sms_via_twilio(phone, sms_body)
                except Exception as exc:
                    result = {"sent": False, "error": str(exc), "phone": phone}
                else:
                    result = {**result, "phone": phone}
                sms_results.append(result)
                if result.get("sent"):
                    any_sent = True
            if any_sent:
                _SMS_COOLDOWNS[code] = now

    return {
        "reported": True,
        "code": code,
        "severity": definition.severity.value,
        "admin_task_id": admin_task_id,
        "sms": sms_results[0] if len(sms_results) == 1 else None,
        "sms_results": sms_results,
    }


def _looks_sensitive(key: str) -> bool:
    """Strip sensitive fields out of audit context so they never reach logs/SMS."""
    lowered = key.lower()
    return any(token in lowered for token in (
        "password", "token", "secret", "api_key", "auth", "card", "cvv", "ssn",
        "bank", "iban", "swift", "account_number",
    ))
