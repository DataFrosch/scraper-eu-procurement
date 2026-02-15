"""Shared code normalization for procurement data.

Maps TED v2 and eForms coded values (procedure types, authority types,
contract nature codes) to canonical eForms codes (lowercase, hyphens).

TED v2 codes are mapped forward to eForms equivalents following the official
OP-TED/ted-xml-data-converter mappings (xslt/other-mappings.xml).
"""

import logging
from typing import NamedTuple, Optional

from ..schema import (
    AuthorityTypeEntry,
    ProcedureTypeEntry,
)

logger = logging.getLogger(__name__)


# Authority type normalization: exact eForms codes (buyer-legal-type codelist).
# Source: OP-TED/ted-xml-data-converter other-mappings.xml (BT-11 ca-types).
# Note: MINISTRY and NATIONAL_AGENCY both map to cga per the official converter.
# Code 8 ("Other") and Z ("Not specified") have no eForms equivalent; mapped to None.
#
# Mapping from old-style codes (R2.0.7/R2.0.8 CODED_DATA_SECTION).
# Verified empirically from R2.0.9 dual-code files.
AUTHORITY_TYPE_CODE_MAP: dict[str, str | None] = {
    "1": "cga",
    "3": "ra",
    "4": None,  # "Utilities entity" — maps to buyer-contracting-type, not buyer-legal-type
    "5": "eu-ins-bod-ag",
    "6": "body-pl",
    "8": None,
    "9": None,  # "Not applicable"
    "N": "cga",
    "R": "body-pl-ra",
    "Z": None,
}

# Mapping from TED v2 R2.0.9 canonical codes (CA_TYPE VALUE) to eForms codes.
# Source: OP-TED/ted-xml-data-converter other-mappings.xml.
TED_V2_AUTHORITY_TO_CANONICAL: dict[str, str | None] = {
    "MINISTRY": "cga",
    "NATIONAL_AGENCY": "cga",
    "REGIONAL_AUTHORITY": "ra",
    "REGIONAL_AGENCY": "body-pl-ra",
    "BODY_PUBLIC": "body-pl",
    "EU_INSTITUTION": "eu-ins-bod-ag",
    "OTHER": None,  # no eForms equivalent, consistent with old code "8" → None
}

# Human-readable descriptions for authority type codes
AUTHORITY_TYPE_DESCRIPTIONS: dict[str, str] = {
    "cga": "Central government authority",
    "ra": "Regional authority",
    "eu-ins-bod-ag": "EU institution, body or agency",
    "body-pl": "Body governed by public law",
    "body-pl-cga": "Body governed by public law, controlled by a central government authority",
    "body-pl-la": "Body governed by public law, controlled by a local authority",
    "body-pl-ra": "Body governed by public law, controlled by a regional authority",
    "la": "Local authority",
    "def-cont": "Defence contractor",
    "int-org": "International organisation",
    "pub-undert": "Public undertaking",
}

# Mapping from old-style contract nature codes (R2.0.7/R2.0.8 NC_CONTRACT_NATURE CODE)
# to canonical codes (R2.0.9 TYPE_CONTRACT CTYPE). Verified empirically from F03_2014
# dual-code files containing both NC_CONTRACT_NATURE and TYPE_CONTRACT:
# "1" -> WORKS (1,961 matches), "2" -> SUPPLIES (5,049), "4" -> SERVICES (6,226).
# Contract nature codes: exact eForms codes (lowercase).
# Source: OP-TED/ted-xml-data-converter other-mappings.xml (BT-23 contract-nature-types).
CONTRACT_NATURE_CODE_MAP: dict[str, str] = {
    "1": "works",
    "2": "supplies",
    "4": "services",
}

# Mapping from TED v2 R2.0.9 uppercase codes (TYPE_CONTRACT CTYPE) to eForms codes.
TED_V2_CONTRACT_NATURE_TO_CANONICAL: dict[str, str] = {
    "WORKS": "works",
    "SUPPLIES": "supplies",
    "SERVICES": "services",
}

# Known eForms contract nature codes (contract-nature-types codelist).
CONTRACT_NATURE_CODES: set[str] = {"works", "supplies", "services", "combined"}


def normalize_contract_nature_code(raw_code: Optional[str]) -> Optional[str]:
    """Normalize a contract nature code to exact eForms form (lowercase).

    Old-style numeric codes are mapped via CONTRACT_NATURE_CODE_MAP.
    TED v2 uppercase codes are mapped via TED_V2_CONTRACT_NATURE_TO_CANONICAL.
    Known eForms codes pass through. Unknown codes log a warning and return None.
    """
    if raw_code is None:
        return None

    if raw_code in CONTRACT_NATURE_CODE_MAP:
        return CONTRACT_NATURE_CODE_MAP[raw_code]

    if raw_code in TED_V2_CONTRACT_NATURE_TO_CANONICAL:
        return TED_V2_CONTRACT_NATURE_TO_CANONICAL[raw_code]

    if raw_code in CONTRACT_NATURE_CODES:
        return raw_code

    logger.warning("Unknown contract nature code: %r", raw_code)
    return None


# Procedure type normalization: exact eForms codes (procurement-procedure-type codelist).
# Source: OP-TED/ted-xml-data-converter other-mappings.xml (BT-105 procedure-types).
# In eForms, "accelerated" is a separate boolean flag (BT-106), not a procedure type.
# The converter maps ACCELERATED_PROC → BT-106=true and keeps the base procedure type.


class ProcedureMapping(NamedTuple):
    """Result of mapping a raw procedure type code to eForms."""

    code: str | None
    accelerated: bool


# Mapping from old-style procedure type codes (R2.0.7/R2.0.8 PR_PROC CODE).
# Verified empirically from F03_2014 dual-code files.
# Codes "B" (competitive negotiation) and "4" (negotiated with competition) both map
# to neg-w-call per the official converter — they were always the same thing.
PROCEDURE_TYPE_CODE_MAP: dict[str, ProcedureMapping] = {
    "1": ProcedureMapping("open", False),
    "2": ProcedureMapping("restricted", False),
    "3": ProcedureMapping("restricted", True),
    "4": ProcedureMapping("neg-w-call", False),
    "6": ProcedureMapping("neg-w-call", True),
    "9": ProcedureMapping(None, False),  # "Not applicable"
    "A": ProcedureMapping(
        None, False
    ),  # "Direct awards" (MOVE/Reg 1370/2007, not convertible)
    "B": ProcedureMapping("neg-w-call", False),
    "C": ProcedureMapping("comp-dial", False),
    "G": ProcedureMapping("innovation", False),
    "T": ProcedureMapping("neg-wo-call", False),
    "V": ProcedureMapping("neg-wo-call", False),
    "N": ProcedureMapping(None, False),
    "Z": ProcedureMapping(None, False),
}

# Mapping from TED v2 R2.0.9 canonical codes (PT_* element names / PR_PROC CODE values)
# to eForms codes. Source: OP-TED/ted-xml-data-converter other-mappings.xml.
TED_V2_TO_CANONICAL: dict[str, ProcedureMapping] = {
    "OPEN": ProcedureMapping("open", False),
    "RESTRICTED": ProcedureMapping("restricted", False),
    "ACCELERATED_RESTRICTED": ProcedureMapping("restricted", True),
    "COMPETITIVE_NEGOTIATION": ProcedureMapping("neg-w-call", False),
    "NEGOTIATED_WITH_COMPETITION": ProcedureMapping("neg-w-call", False),
    "ACCELERATED_NEGOTIATED": ProcedureMapping("neg-w-call", True),
    "COMPETITIVE_DIALOGUE": ProcedureMapping("comp-dial", False),
    "INNOVATION_PARTNERSHIP": ProcedureMapping("innovation", False),
    "AWARD_CONTRACT_WITHOUT_CALL": ProcedureMapping("neg-wo-call", False),
    "NEGOTIATED_WITH_PRIOR_CALL": ProcedureMapping("neg-w-call", False),
    "AWARD_CONTRACT_WITH_PRIOR_PUBLICATION": ProcedureMapping("neg-w-call", False),
    "AWARD_CONTRACT_WITHOUT_PUBLICATION": ProcedureMapping("neg-wo-call", False),
    "NEGOTIATED_WITHOUT_PUBLICATION": ProcedureMapping("neg-wo-call", False),
    "INVOLVING_NEGOTIATION": ProcedureMapping(
        None, False
    ),  # maps to UNKNOWN in converter
}

# Human-readable descriptions for procedure type codes
PROCEDURE_TYPE_DESCRIPTIONS: dict[str, str] = {
    "open": "Open procedure",
    "restricted": "Restricted procedure",
    "neg-w-call": "Negotiated with prior call for competition",
    "comp-dial": "Competitive dialogue",
    "innovation": "Innovation partnership",
    "neg-wo-call": "Negotiated without prior call for competition",
    "oth-single": "Other single stage procedure",
    "oth-mult": "Other multiple stage procedure",
    "comp-tend": "Competitive tendering (Regulation 1370/2007)",
}


def normalize_procedure_type(
    raw_code: Optional[str], description: Optional[str]
) -> tuple[Optional[ProcedureTypeEntry], bool]:
    """Convert a raw procedure type code to a normalized ProcedureTypeEntry.

    Returns (procedure_type_entry, accelerated) tuple.
    All codes normalize to exact eForms codes (lowercase, hyphens). Mapping chain:
    - R2.0.7/R2.0.8 numeric/letter codes (e.g. "1") → via PROCEDURE_TYPE_CODE_MAP
    - R2.0.9 canonical codes (e.g. "AWARD_CONTRACT_WITHOUT_CALL") → via TED_V2_TO_CANONICAL
    - eForms codes (e.g. "neg-wo-call") → pass through as-is
    """
    if raw_code is None or raw_code == "unpublished":
        return None, False

    # Old-style numeric/letter code (R2.0.7/R2.0.8)
    if raw_code in PROCEDURE_TYPE_CODE_MAP:
        canonical, accelerated = PROCEDURE_TYPE_CODE_MAP[raw_code]
        if canonical is None:
            return None, False
        return ProcedureTypeEntry(
            code=canonical,
            description=PROCEDURE_TYPE_DESCRIPTIONS.get(canonical),
        ), accelerated

    # TED v2 R2.0.9 uppercase code that needs remapping
    if raw_code in TED_V2_TO_CANONICAL:
        canonical, accelerated = TED_V2_TO_CANONICAL[raw_code]
        if canonical is None:
            return None, False
        return ProcedureTypeEntry(
            code=canonical,
            description=PROCEDURE_TYPE_DESCRIPTIONS.get(canonical),
        ), accelerated

    # Known eForms code — pass through
    if raw_code in PROCEDURE_TYPE_DESCRIPTIONS:
        return ProcedureTypeEntry(
            code=raw_code,
            description=description or PROCEDURE_TYPE_DESCRIPTIONS[raw_code],
        ), False

    logger.warning("Unknown procedure type code: %r", raw_code)
    return None, False


def make_authority_type_entry(
    raw_code: Optional[str],
) -> Optional[AuthorityTypeEntry]:
    """Convert a raw authority type code to a normalized AuthorityTypeEntry.

    All codes normalize to exact eForms codes (lowercase, hyphens). Mapping chain:
    - R2.0.7/R2.0.8 numeric/letter codes (e.g. "6") → via AUTHORITY_TYPE_CODE_MAP
    - R2.0.9 canonical codes (e.g. "BODY_PUBLIC") → via TED_V2_AUTHORITY_TO_CANONICAL
    - eForms codes (e.g. "body-pl") → pass through as-is
    """
    if raw_code is None:
        return None

    # Old-style numeric/letter code (R2.0.7/R2.0.8)
    if raw_code in AUTHORITY_TYPE_CODE_MAP:
        canonical = AUTHORITY_TYPE_CODE_MAP[raw_code]
        if canonical is None:
            return None
        return AuthorityTypeEntry(
            code=canonical,
            description=AUTHORITY_TYPE_DESCRIPTIONS.get(canonical),
        )

    # TED v2 R2.0.9 uppercase code that needs remapping
    if raw_code in TED_V2_AUTHORITY_TO_CANONICAL:
        canonical = TED_V2_AUTHORITY_TO_CANONICAL[raw_code]
        if canonical is None:
            return None
        return AuthorityTypeEntry(
            code=canonical,
            description=AUTHORITY_TYPE_DESCRIPTIONS.get(canonical),
        )

    # Known eForms code — pass through
    if raw_code in AUTHORITY_TYPE_DESCRIPTIONS:
        return AuthorityTypeEntry(
            code=raw_code,
            description=AUTHORITY_TYPE_DESCRIPTIONS[raw_code],
        )

    logger.warning("Unknown authority type code: %r", raw_code)
    return None
