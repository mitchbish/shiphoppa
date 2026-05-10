"""
Supplier invoice extractor.

Takes raw invoice text (from a forwarded email body, OCR'd PDF, or pasted
upload) and produces a structured ParsedInvoice with the fields a customer
or operator needs to act on it: supplier, invoice number, amounts in any
currency, due date, payment instructions, and a confidence score per field.

Designed to be deterministic and side-effect free. The caller layers on
matching to a purchase order, payment request creation, audit events, and
notifications.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel

from .models import SourceConfidence


CURRENCY_CODES = ("USD", "AUD", "EUR", "GBP", "CNY", "RMB", "HKD", "SGD", "JPY", "CAD", "NZD")


INVOICE_NUMBER_PATTERN = re.compile(
    r"(?:invoice|inv)\s*(?:no\.?|number|#)?\s*[:#]?\s*([A-Z0-9][A-Z0-9\-/]{2,30})",
    re.IGNORECASE,
)

PI_NUMBER_PATTERN = re.compile(
    r"(?:proforma|p\.?i\.?)\s*(?:no\.?|number|#)?\s*[:#]?\s*([A-Z0-9][A-Z0-9\-/]{2,30})",
    re.IGNORECASE,
)

PO_REFERENCE_PATTERN = re.compile(
    r"(?:po|purchase order|p\.?o\.?)\s*(?:no\.?|number|#)?\s*[:#]?\s*([A-Z0-9][A-Z0-9\-/]{2,30})",
    re.IGNORECASE,
)

# Amount + currency: either "USD 4,250.00" or "$4,250.00 USD" or "4,250 RMB"
AMOUNT_CURRENCY_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (
        re.compile(
            r"(?:total|amount due|grand total|balance due|invoice amount|net total|total due)\s*[:=]?\s*"
            r"(USD|AUD|EUR|GBP|CNY|RMB|HKD|SGD|JPY|CAD|NZD|US\$|\$|€|£|¥)\s*([\d,]+\.?\d*)",
            re.IGNORECASE,
        ),
        "labelled_amount",
    ),
    (
        re.compile(
            r"(?:total|amount due|grand total|balance due|invoice amount|net total|total due)\s*[:=]?\s*"
            r"([\d,]+\.?\d*)\s*(USD|AUD|EUR|GBP|CNY|RMB|HKD|SGD|JPY|CAD|NZD)",
            re.IGNORECASE,
        ),
        "labelled_amount_trailing_currency",
    ),
]

DUE_DATE_PATTERN = re.compile(
    r"(?:due|payment due|due date|pay by|payable by)\s*[:=]?\s*"
    r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4})",
    re.IGNORECASE,
)

ISSUE_DATE_PATTERN = re.compile(
    r"(?:invoice date|issued|date of invoice|issue date)\s*[:=]?\s*"
    r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
    re.IGNORECASE,
)

BANK_NAME_PATTERN = re.compile(
    r"(?:bank|beneficiary bank|bank name)\s*[:=]?\s*([A-Za-z][A-Za-z &.,'-]{3,80})",
    re.IGNORECASE,
)

ACCOUNT_NUMBER_PATTERN = re.compile(
    r"(?:account|account no\.?|account number|a/c)\s*[:#]?\s*([0-9][0-9\- ]{5,30})",
    re.IGNORECASE,
)

SWIFT_PATTERN = re.compile(
    r"(?:swift|swift code|bic)\s*[:=]?\s*([A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)",
    re.IGNORECASE,
)

IBAN_PATTERN = re.compile(
    r"(?:iban)\s*[:=]?\s*([A-Z]{2}\d{2}[A-Z0-9]{4,30})",
    re.IGNORECASE,
)

BENEFICIARY_PATTERN = re.compile(
    r"(?:beneficiary|payable to|pay to|company name)\s*[:=]?\s*([A-Za-z][A-Za-z &.,'-]{3,80})",
    re.IGNORECASE,
)


class ParsedInvoiceLine(BaseModel):
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None


class ParsedInvoice(BaseModel):
    invoice_number: Optional[str] = None
    proforma_number: Optional[str] = None
    purchase_order_reference: Optional[str] = None
    supplier_name: Optional[str] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: Optional[str] = None
    total_amount: Optional[float] = None
    bank_name: Optional[str] = None
    account_number_last4: Optional[str] = None  # Mask account numbers, only keep last 4
    swift_code: Optional[str] = None
    iban_last4: Optional[str] = None
    beneficiary_name: Optional[str] = None
    line_items: List[ParsedInvoiceLine] = []
    confidence: SourceConfidence = SourceConfidence.estimated
    source_snippet: Optional[str] = None


def _parse_amount(raw: str) -> Optional[float]:
    cleaned = raw.replace(",", "").strip()
    try:
        return float(cleaned)
    except (TypeError, ValueError):
        return None


def _parse_date(raw: str) -> Optional[date]:
    raw = raw.strip()
    formats = [
        "%Y-%m-%d", "%Y/%m/%d",
        "%d-%m-%Y", "%d/%m/%Y",
        "%d-%m-%y", "%d/%m/%y",
        "%d %b %Y", "%d %B %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _normalize_currency(raw: str) -> Optional[str]:
    raw = raw.strip().upper()
    if raw in ("$", "US$"):
        return "USD"
    if raw == "€":
        return "EUR"
    if raw == "£":
        return "GBP"
    if raw == "¥":
        return "CNY"
    if raw == "RMB":
        return "CNY"
    if raw in CURRENCY_CODES:
        return raw
    return None


def _last4(value: str) -> str:
    digits = re.sub(r"[^\dA-Z]", "", value.upper())
    return digits[-4:] if len(digits) >= 4 else digits


def extract_invoice_from_text(text: str) -> ParsedInvoice:
    """
    Parse a single supplier invoice from raw text. Returns a ParsedInvoice
    with whatever fields could be extracted. Never raises; missing fields
    stay None.
    """
    if not text:
        return ParsedInvoice()

    parsed = ParsedInvoice()

    inv_match = INVOICE_NUMBER_PATTERN.search(text)
    if inv_match:
        parsed.invoice_number = inv_match.group(1).upper()

    pi_match = PI_NUMBER_PATTERN.search(text)
    if pi_match:
        parsed.proforma_number = pi_match.group(1).upper()

    po_match = PO_REFERENCE_PATTERN.search(text)
    if po_match and parsed.invoice_number != po_match.group(1).upper():
        parsed.purchase_order_reference = po_match.group(1).upper()

    for pattern, kind in AMOUNT_CURRENCY_PATTERNS:
        m = pattern.search(text)
        if m:
            if kind == "labelled_amount":
                parsed.currency = _normalize_currency(m.group(1))
                parsed.total_amount = _parse_amount(m.group(2))
            elif kind == "labelled_amount_trailing_currency":
                parsed.total_amount = _parse_amount(m.group(1))
                parsed.currency = _normalize_currency(m.group(2))
            if parsed.total_amount is not None:
                break

    issue_match = ISSUE_DATE_PATTERN.search(text)
    if issue_match:
        parsed.issue_date = _parse_date(issue_match.group(1))

    due_match = DUE_DATE_PATTERN.search(text)
    if due_match:
        parsed.due_date = _parse_date(due_match.group(1))

    bank_match = BANK_NAME_PATTERN.search(text)
    if bank_match:
        parsed.bank_name = bank_match.group(1).strip().rstrip(".,")

    acc_match = ACCOUNT_NUMBER_PATTERN.search(text)
    if acc_match:
        parsed.account_number_last4 = _last4(acc_match.group(1))

    swift_match = SWIFT_PATTERN.search(text)
    if swift_match:
        parsed.swift_code = swift_match.group(1).upper()

    iban_match = IBAN_PATTERN.search(text)
    if iban_match:
        parsed.iban_last4 = _last4(iban_match.group(1))

    ben_match = BENEFICIARY_PATTERN.search(text)
    if ben_match:
        parsed.beneficiary_name = ben_match.group(1).strip().rstrip(".,")

    # Confidence: more fields parsed = higher confidence
    field_count = sum(
        1
        for v in (
            parsed.invoice_number,
            parsed.total_amount,
            parsed.currency,
            parsed.due_date,
            parsed.bank_name,
            parsed.account_number_last4,
        )
        if v
    )
    if field_count >= 5:
        parsed.confidence = SourceConfidence.verified
    elif field_count >= 3:
        parsed.confidence = SourceConfidence.estimated
    else:
        parsed.confidence = SourceConfidence.estimated

    if text:
        # Capture a short surrounding snippet so the operator can audit the parse
        snippet_source = inv_match or (AMOUNT_CURRENCY_PATTERNS[0][0].search(text))
        if snippet_source:
            start = max(0, snippet_source.start() - 30)
            end = min(len(text), snippet_source.end() + 80)
            parsed.source_snippet = text[start:end].strip()

    return parsed
