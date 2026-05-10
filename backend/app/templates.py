"""
Ship Hoppa email/SMS template rendering.

Templates are addressed by `template_key`. Each template defines a subject,
body, and the recipient role it's intended for. Variables in templates are
substituted via standard Python str.format with a context dict.

The rendering function is pure: it does not touch the store, send anything,
or create audit events. It only produces the subject/body text. Side effects
happen in the queue layer.
"""

from typing import Any, Dict, Optional, Tuple

from .models import OutboundRecipientType


class Template:
    def __init__(
        self,
        key: str,
        recipient_type: OutboundRecipientType,
        subject: str,
        body: str,
        version: str = "v1",
    ) -> None:
        self.key = key
        self.recipient_type = recipient_type
        self.subject = subject
        self.body = body
        self.version = version


REGISTRY: Dict[str, Template] = {}


def register(template: Template) -> Template:
    REGISTRY[template.key] = template
    return template


# --- Supplier chase templates ---

register(Template(
    key="chase_pickup_address",
    recipient_type=OutboundRecipientType.supplier,
    subject="Pickup address needed for shipment {booking_id}",
    body=(
        "Hi {supplier_name},\n\n"
        "We need the factory pickup address and contact details to arrange "
        "collection for shipment {booking_id} ({cargo_description}).\n\n"
        "Please reply with:\n"
        "  • Full pickup address\n"
        "  • Contact name on collection day\n"
        "  • Contact phone number\n"
        "  • Goods ready time window\n\n"
        "Reply to this email and we'll update the shipment automatically.\n\n"
        "Thanks,\nShip Hoppa Operations"
    ),
))

register(Template(
    key="chase_packing_list",
    recipient_type=OutboundRecipientType.supplier,
    subject="Packing list required for shipment {booking_id}",
    body=(
        "Hi {supplier_name},\n\n"
        "Please attach or send the packing list for shipment {booking_id} "
        "({cargo_description}). We need carton count, dimensions, and weights "
        "to confirm the shipping plan and avoid carrier surcharges.\n\n"
        "PDF, Excel, or photos of a printed list all work.\n\n"
        "Thanks,\nShip Hoppa Operations"
    ),
))

register(Template(
    key="chase_commercial_invoice",
    recipient_type=OutboundRecipientType.supplier,
    subject="Commercial invoice required for shipment {booking_id}",
    body=(
        "Hi {supplier_name},\n\n"
        "Please send the commercial invoice for shipment {booking_id} "
        "({cargo_description}). This is needed for customs clearance at "
        "destination.\n\n"
        "Thanks,\nShip Hoppa Operations"
    ),
))

register(Template(
    key="chase_fumigation_certificate",
    recipient_type=OutboundRecipientType.warehouse,
    subject="ISPM-15 fumigation certificate needed for {booking_id}",
    body=(
        "Hi,\n\n"
        "Shipment {booking_id} requires an ISPM-15 compliant fumigation "
        "certificate before loading. Please arrange treatment and provide "
        "the certificate as soon as possible.\n\n"
        "Cargo: {cargo_description}\n"
        "Origin: {origin_city}\n\n"
        "Thanks,\nShip Hoppa Operations"
    ),
))


# --- Forwarder/broker chase templates ---

register(Template(
    key="chase_shipping_instructions",
    recipient_type=OutboundRecipientType.forwarder,
    subject="Shipping instructions needed for {booking_id}",
    body=(
        "Hi,\n\n"
        "Please provide shipping instructions for shipment {booking_id} "
        "before the carrier cutoff. Container: {container_number}.\n\n"
        "Thanks,\nShip Hoppa Operations"
    ),
))

register(Template(
    key="chase_house_bill",
    recipient_type=OutboundRecipientType.forwarder,
    subject="House BL needed for {booking_id}",
    body=(
        "Hi,\n\n"
        "Please send the house bill of lading for shipment {booking_id}.\n\n"
        "Thanks,\nShip Hoppa Operations"
    ),
))

register(Template(
    key="chase_arrival_notice",
    recipient_type=OutboundRecipientType.forwarder,
    subject="Arrival notice needed for {booking_id}",
    body=(
        "Hi,\n\n"
        "Shipment {booking_id} is due to arrive shortly. Please send the "
        "arrival notice so we can proceed with customs and delivery.\n\n"
        "Thanks,\nShip Hoppa Operations"
    ),
))

register(Template(
    key="chase_delivery_order",
    recipient_type=OutboundRecipientType.forwarder,
    subject="Delivery order needed for {booking_id}",
    body=(
        "Hi,\n\n"
        "Please send the delivery order for shipment {booking_id} so we can "
        "arrange final delivery.\n\n"
        "Thanks,\nShip Hoppa Operations"
    ),
))

register(Template(
    key="chase_hs_code",
    recipient_type=OutboundRecipientType.broker,
    subject="HS classification needed for {booking_id}",
    body=(
        "Hi,\n\n"
        "Please provide the HS code classification for shipment {booking_id}. "
        "Goods description: {cargo_description}.\n\n"
        "Thanks,\nShip Hoppa Operations"
    ),
))


# --- Importer-facing notifications ---

register(Template(
    key="importer_approval_required",
    recipient_type=OutboundRecipientType.importer,
    subject="Action needed: {approval_title}",
    body=(
        "Hi {importer_name},\n\n"
        "Your shipment {booking_id} needs your decision:\n\n"
        "{approval_summary}\n\n"
        "Open Ship Hoppa to review and approve.\n\n"
        "Thanks,\nShip Hoppa"
    ),
))

register(Template(
    key="importer_arrival_notice",
    recipient_type=OutboundRecipientType.importer,
    subject="Your shipment {booking_id} has arrived",
    body=(
        "Hi {importer_name},\n\n"
        "Shipment {booking_id} ({cargo_description}) arrived at "
        "{destination_port} today. Customs clearance and final delivery "
        "are in progress.\n\n"
        "Track progress in Ship Hoppa.\n\n"
        "Thanks,\nShip Hoppa"
    ),
))

register(Template(
    key="importer_sailing_change",
    recipient_type=OutboundRecipientType.importer,
    subject="Sailing schedule update for {booking_id}",
    body=(
        "Hi {importer_name},\n\n"
        "The carrier has updated the schedule for shipment {booking_id}.\n\n"
        "New ETA: {new_eta}\n"
        "Previous ETA: {old_eta}\n\n"
        "Open Ship Hoppa to confirm or request alternatives.\n\n"
        "Thanks,\nShip Hoppa"
    ),
))


# --- Generic fallback ---

register(Template(
    key="chase_generic",
    recipient_type=OutboundRecipientType.supplier,
    subject="Information needed for shipment {booking_id}",
    body=(
        "Hi,\n\n"
        "We need additional information for shipment {booking_id}. Please "
        "respond with the required details.\n\n"
        "Thanks,\nShip Hoppa Operations"
    ),
))


def render(template_key: str, context: Dict[str, Any]) -> Tuple[str, str]:
    """Render template subject and body. Missing context keys render as the
    placeholder name in braces, never raising KeyError."""
    template = REGISTRY.get(template_key) or REGISTRY["chase_generic"]
    safe_context: Dict[str, Any] = _SafeContext(context)
    subject = template.subject.format_map(safe_context)
    body = template.body.format_map(safe_context)
    return subject, body


def template_for(template_key: str) -> Optional[Template]:
    return REGISTRY.get(template_key)


def template_recipient(template_key: str) -> Optional[OutboundRecipientType]:
    template = REGISTRY.get(template_key)
    return template.recipient_type if template else None


class _SafeContext(dict):
    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"
