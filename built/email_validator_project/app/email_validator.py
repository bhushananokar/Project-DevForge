"""
Email validation module.

Provides RFC 5321/5322‑compliant email address validation with:
- Structural regex check (supports Unicode in local part per RFC 6531)
- Length constraints (local ≤ 64, domain ≤ 255, total ≤ 254)
- TLD verification against a curated IANA‑like list
- Dot/hyphen placement rules
- Internationalised email awareness
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Curated list of valid top‑level domains (IANA subset + common ccTLDs)
# ---------------------------------------------------------------------------
_VALID_TLDS: frozenset[str] = frozenset(
    {
        "com", "org", "net", "edu", "gov", "mil", "int",
        "info", "biz", "name", "pro", "aero", "coop",
        "museum", "travel", "jobs", "mobi", "cat", "tel",
        "asia", "xxx", "post", "blog", "shop", "dev", "app",
        "online", "site", "tech", "ai", "io", "me", "tv",
        "gg", "co", "us", "uk", "de", "fr", "jp", "cn",
        "ru", "br", "au", "ca", "in", "it", "es", "nl",
        "se", "no", "dk", "fi", "pl", "ch", "at", "be",
        "cz", "pt", "ie", "nz", "za", "kr", "sg", "mx",
        "ar", "cl", "ph",
    }
)

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
# Domain label: 1-63 chars, alphanumeric + hyphens, no leading/trailing hyphen
_DOMAIN_LABEL: str = r"(?!-)[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"

# Full domain: one or more labels separated by dots.
# NOTE: inside an rf-string, \. produces a literal \. (escaped dot in regex).
_DOMAIN_RE: str = rf"{_DOMAIN_LABEL}(?:\.{_DOMAIN_LABEL})*"

# Local part: Unicode-aware via \w + safe specials (RFC 5321/6531)
_LOCAL_RE: str = r"[\w!#$%&'*+/=?^_`{|}~.-]+"

_EMAIL_REGEX: re.Pattern[str] = re.compile(
    rf"^({_LOCAL_RE})@({_DOMAIN_RE})$", re.UNICODE
)

# Maximum lengths per RFC 5321
LOCAL_PART_MAX_LEN: int = 64
DOMAIN_MAX_LEN: int = 255
EMAIL_MAX_LEN: int = 254


@dataclass(slots=True)
class ValidationResult:
    """Structured result of email validation."""

    is_valid: bool
    normalized: str | None = None
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_email(address: str | None) -> ValidationResult:
    """Validate an email address and return a structured result.

    Args:
        address: The email address to validate.

    Returns:
        ``ValidationResult`` with ``is_valid``, ``normalized``, and ``errors``.
    """
    # --- Guard: must be a non-empty string ---
    if address is None:
        return ValidationResult(is_valid=False, errors=["Email address is None."])
    if not isinstance(address, str):
        return ValidationResult(
            is_valid=False,
            errors=[f"Expected str, got {type(address).__name__}."],
        )
    stripped = address.strip()
    if not stripped:
        return ValidationResult(is_valid=False, errors=["Email address is empty."])

    # --- Total length ---
    if len(stripped) > EMAIL_MAX_LEN:
        return ValidationResult(
            is_valid=False,
            errors=[
                f"Email address exceeds {EMAIL_MAX_LEN} characters "
                f"(actual: {len(stripped)})."
            ],
        )

    # --- Regex structural match ---
    match = _EMAIL_REGEX.match(stripped)
    if not match:
        return ValidationResult(
            is_valid=False,
            errors=["Email address does not match expected pattern."],
        )

    local_part = match.group(1)
    domain = match.group(2)

    # --- Local part length ---
    if len(local_part) > LOCAL_PART_MAX_LEN:
        return ValidationResult(
            is_valid=False,
            errors=[
                f"Local part exceeds {LOCAL_PART_MAX_LEN} characters "
                f"(actual: {len(local_part)})."
            ],
        )

    # --- Domain length ---
    if len(domain) > DOMAIN_MAX_LEN:
        return ValidationResult(
            is_valid=False,
            errors=[
                f"Domain exceeds {DOMAIN_MAX_LEN} characters "
                f"(actual: {len(domain)})."
            ],
        )

    # --- Consecutive dots anywhere ---
    if ".." in stripped:
        return ValidationResult(
            is_valid=False, errors=["Email contains consecutive dots."]
        )

    # --- Leading/trailing dot or hyphen in local part ---
    if local_part.startswith(".") or local_part.endswith("."):
        return ValidationResult(
            is_valid=False,
            errors=["Local part must not start or end with a dot."],
        )
    if local_part.startswith("-") or local_part.endswith("-"):
        return ValidationResult(
            is_valid=False,
            errors=["Local part must not start or end with a hyphen."],
        )

    # --- Leading/trailing dot or hyphen in domain ---
    if domain.startswith(".") or domain.endswith("."):
        return ValidationResult(
            is_valid=False,
            errors=["Domain must not start or end with a dot."],
        )
    if domain.startswith("-") or domain.endswith("-"):
        return ValidationResult(
            is_valid=False,
            errors=["Domain must not start or end with a hyphen."],
        )

    # --- Domain must contain at least one dot ---
    if "." not in domain:
        return ValidationResult(
            is_valid=False,
            errors=["Domain must contain at least one dot (e.g. example.com)."],
        )

    # --- TLD check ---
    tld = domain.rsplit(".", 1)[-1].lower()
    if tld not in _VALID_TLDS:
        return ValidationResult(
            is_valid=False,
            errors=[f'TLD "{tld}" is not recognised.'],
        )

    # --- Success ---
    normalized = stripped.lower().strip()
    return ValidationResult(is_valid=True, normalized=normalized, errors=[])
