"""
Customs classification helpers.

Given a cargo description and category, suggest plausible HS codes.
This is a lightweight rules-based classifier, not a substitute for a
licenced broker. The output drives a one-click accept in the customer
UI: high-confidence suggestions can auto-populate the customs profile,
medium-confidence suggestions need human review, low-confidence
suggestions are a starting point only.

The HS chapter prefixes here cover the AU/US tariff schedules well
enough for the launch lanes. For production, this should be backed by
a real ABF tariff lookup (and equivalent for the US), with this rules
table as a safety fallback when the live lookup fails.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .models import CargoCategory, SourceConfidence


@dataclass
class HSCodeSuggestion:
    hs_code: str
    description: str
    confidence: SourceConfidence
    rationale: str


# --- Category-level fallback ---
# When we have no description, the cargo category alone gets us into the right
# HS chapter. These are intentionally broad chapter headings, not specific
# tariff items.

CATEGORY_FALLBACKS = {
    CargoCategory.tiles_stone: HSCodeSuggestion(
        hs_code="6907",
        description="Ceramic flags and paving, hearth or wall tiles.",
        confidence=SourceConfidence.estimated,
        rationale="Cargo category 'tiles_stone' maps to chapter 69 (ceramic).",
    ),
    CargoCategory.furniture: HSCodeSuggestion(
        hs_code="9403",
        description="Other furniture and parts thereof.",
        confidence=SourceConfidence.estimated,
        rationale="Cargo category 'furniture' maps to chapter 94.",
    ),
    CargoCategory.homewares: HSCodeSuggestion(
        hs_code="6912",
        description="Ceramic tableware, kitchenware, and household articles.",
        confidence=SourceConfidence.estimated,
        rationale="Cargo category 'homewares' often classifies under chapter 69.",
    ),
    CargoCategory.bathroom_fittings: HSCodeSuggestion(
        hs_code="6910",
        description="Ceramic sinks, washbasins, baths, and similar fixtures.",
        confidence=SourceConfidence.estimated,
        rationale="Cargo category 'bathroom_fittings' maps to ceramic sanitary ware.",
    ),
    CargoCategory.lighting: HSCodeSuggestion(
        hs_code="9405",
        description="Lamps and lighting fittings, including parts.",
        confidence=SourceConfidence.estimated,
        rationale="Cargo category 'lighting' maps to chapter 94.",
    ),
    CargoCategory.hardware: HSCodeSuggestion(
        hs_code="8302",
        description="Base metal mountings, fittings, and similar articles.",
        confidence=SourceConfidence.estimated,
        rationale="Cargo category 'hardware' typically classifies under chapter 83.",
    ),
    CargoCategory.garden: HSCodeSuggestion(
        hs_code="6914",
        description="Other ceramic articles (garden statuary etc.).",
        confidence=SourceConfidence.estimated,
        rationale="Garden goods often combine chapter 69 (ceramic) and chapter 73 (steel).",
    ),
    CargoCategory.automotive: HSCodeSuggestion(
        hs_code="8708",
        description="Parts and accessories of motor vehicles.",
        confidence=SourceConfidence.estimated,
        rationale="Cargo category 'automotive' maps to chapter 87.",
    ),
}


# --- Keyword overrides ---
# When a description contains specific words, prefer the more specific HS code.

KEYWORD_RULES = [
    # Ceramic / tiles
    (("porcelain", "tile"), HSCodeSuggestion(
        hs_code="6907.21",
        description="Porcelain or china tiles, with a water absorption <= 0.5%.",
        confidence=SourceConfidence.verified,
        rationale="Description contains 'porcelain' and 'tile'.",
    )),
    (("ceramic", "tile"), HSCodeSuggestion(
        hs_code="6907.22",
        description="Ceramic tiles with water absorption between 0.5% and 10%.",
        confidence=SourceConfidence.verified,
        rationale="Description contains 'ceramic' and 'tile'.",
    )),
    (("mosaic",), HSCodeSuggestion(
        hs_code="6907.30",
        description="Mosaic cubes and the like.",
        confidence=SourceConfidence.verified,
        rationale="Description references mosaic.",
    )),
    # Furniture
    (("wooden", "chair"), HSCodeSuggestion(
        hs_code="9401.61",
        description="Other seats, with wooden frame, upholstered.",
        confidence=SourceConfidence.verified,
        rationale="Wooden upholstered seating.",
    )),
    (("metal", "chair"), HSCodeSuggestion(
        hs_code="9401.71",
        description="Other seats, with metal frame, upholstered.",
        confidence=SourceConfidence.verified,
        rationale="Metal-framed upholstered seating.",
    )),
    (("dining table",), HSCodeSuggestion(
        hs_code="9403.30",
        description="Wooden furniture of a kind used in offices.",
        confidence=SourceConfidence.estimated,
        rationale="Likely wooden furniture; broker should confirm subheading.",
    )),
    (("mattress",), HSCodeSuggestion(
        hs_code="9404.29",
        description="Mattresses of other materials (foam, spring).",
        confidence=SourceConfidence.verified,
        rationale="Description references mattress.",
    )),
    # Lighting
    (("led", "lamp"), HSCodeSuggestion(
        hs_code="9405.42",
        description="Other electric luminaires and lighting fittings, designed for use solely with LED light sources.",
        confidence=SourceConfidence.verified,
        rationale="LED lamp.",
    )),
    (("chandelier",), HSCodeSuggestion(
        hs_code="9405.11",
        description="Chandeliers and other electric ceiling/wall lighting fittings.",
        confidence=SourceConfidence.verified,
        rationale="Description references chandelier.",
    )),
    # Bathroom
    (("ceramic", "basin"), HSCodeSuggestion(
        hs_code="6910.10",
        description="Ceramic sinks, washbasins, and similar sanitary fixtures.",
        confidence=SourceConfidence.verified,
        rationale="Ceramic sanitary ware.",
    )),
    (("toilet",), HSCodeSuggestion(
        hs_code="6910.10",
        description="Ceramic sinks, washbasins, baths, water closet pans.",
        confidence=SourceConfidence.verified,
        rationale="Description references toilet/water closet pan.",
    )),
    (("tap", "brass"), HSCodeSuggestion(
        hs_code="8481.80",
        description="Other taps, cocks, valves, and similar appliances.",
        confidence=SourceConfidence.verified,
        rationale="Brass tapware.",
    )),
    # Homewares
    (("plate", "ceramic"), HSCodeSuggestion(
        hs_code="6912.00",
        description="Ceramic tableware (excluding porcelain or china).",
        confidence=SourceConfidence.verified,
        rationale="Ceramic tableware.",
    )),
    (("glassware",), HSCodeSuggestion(
        hs_code="7013.00",
        description="Glassware of a kind used for table, kitchen, toilet, office, indoor decoration.",
        confidence=SourceConfidence.verified,
        rationale="Description references glassware.",
    )),
    # Hardware
    (("door", "hinge"), HSCodeSuggestion(
        hs_code="8302.10",
        description="Hinges of base metal.",
        confidence=SourceConfidence.verified,
        rationale="Door hinges.",
    )),
    (("padlock",), HSCodeSuggestion(
        hs_code="8301.10",
        description="Padlocks of base metal.",
        confidence=SourceConfidence.verified,
        rationale="Description references padlock.",
    )),
    # Garden
    (("planter", "ceramic"), HSCodeSuggestion(
        hs_code="6914.10",
        description="Other ceramic articles, of porcelain or china (planters etc).",
        confidence=SourceConfidence.verified,
        rationale="Ceramic planter.",
    )),
    (("garden", "tool"), HSCodeSuggestion(
        hs_code="8201.30",
        description="Mattocks, picks, hoes, rakes, and similar hand tools.",
        confidence=SourceConfidence.verified,
        rationale="Garden hand tools.",
    )),
]


def suggest_hs_code(
    cargo_description: Optional[str],
    cargo_category: Optional[CargoCategory] = None,
) -> List[HSCodeSuggestion]:
    """
    Return a list of plausible HS code suggestions for a cargo description
    and category. Most-specific (keyword-matched) suggestions come first;
    a category fallback is appended if available. List may be empty.
    """
    suggestions: List[HSCodeSuggestion] = []

    description_normalised = (cargo_description or "").lower()
    if description_normalised:
        for keywords, suggestion in KEYWORD_RULES:
            if all(k in description_normalised for k in keywords):
                suggestions.append(suggestion)

    if cargo_category is not None and cargo_category in CATEGORY_FALLBACKS:
        fallback = CATEGORY_FALLBACKS[cargo_category]
        # Only include the fallback if it isn't already a more specific match
        if not any(s.hs_code.startswith(fallback.hs_code[:4]) for s in suggestions):
            suggestions.append(fallback)

    return suggestions


def best_suggestion(
    cargo_description: Optional[str],
    cargo_category: Optional[CargoCategory] = None,
) -> Optional[HSCodeSuggestion]:
    """Return the highest-confidence suggestion or None."""
    suggestions = suggest_hs_code(cargo_description, cargo_category)
    if not suggestions:
        return None
    confidence_order = {
        SourceConfidence.confirmed: 0,
        SourceConfidence.verified: 1,
        SourceConfidence.estimated: 2,
    }
    suggestions.sort(key=lambda s: confidence_order.get(s.confidence, 99))
    return suggestions[0]
