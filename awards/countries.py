"""Country code to name mapping using pycountry (ISO 3166-1 alpha-2)."""

import pycountry

# Historical codes present in TED data but removed from ISO 3166
_HISTORICAL = {
    "AN": "Netherlands Antilles",
}


def get_country_name(code: str) -> str | None:
    """Look up English name for an ISO 3166-1 alpha-2 country code.

    Also covers historical codes (AN) found in TED data.
    """
    if code in _HISTORICAL:
        return _HISTORICAL[code]
    country = pycountry.countries.get(alpha_2=code)
    return country.name if country else None
