"""
Unit tests for the email_validator module.

Covers:
- Valid email addresses (standard formats)
- Invalid formats (missing @, double dots, invalid chars)
- Edge cases (max lengths, unicode, internationalised)
- Boundary values (empty, None, non-string)
- TLD validation edge cases
"""

from __future__ import annotations

import pytest
from app.email_validator import (
    EMAIL_MAX_LEN,
    LOCAL_PART_MAX_LEN,
    ValidationResult,
    validate_email,
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _ok(addr: str) -> ValidationResult:
    """Shorthand for asserting a valid result."""
    result = validate_email(addr)
    assert result.is_valid is True, f"Expected valid, got errors: {result.errors}"
    assert result.normalized == addr.strip().lower()
    return result


def _bad(addr) -> ValidationResult:
    """Shorthand for asserting an invalid result."""
    result = validate_email(addr)
    assert result.is_valid is False, (
        f"Expected invalid for {addr!r}, but was marked valid."
    )
    return result


# ---------------------------------------------------------------------------
# Valid addresses
# ---------------------------------------------------------------------------

VALID_CASES = [
    "user@example.com",
    "first.last@example.com",
    "user+tag@example.org",
    "user@sub.example.co.uk",
    "a@b.io",
    "TEST@EXAMPLE.COM",  # normalised to lowercase
    "user@example-dash.com",
    "user@domain.travel",
    "user@domain.museum",
    "user@domain.dev",
    "user@domain.app",
    "user@domain.ai",
    "name@domain.mobi",
    "user@domain.cat",
    "user@domain.name",
    "user@domain.pro",
]


@pytest.mark.parametrize("address", VALID_CASES)
def test_valid_addresses(address: str) -> None:
    """All standard-format addresses should pass."""
    _ok(address)


# ---------------------------------------------------------------------------
# Invalid addresses – structural / format
# ---------------------------------------------------------------------------

INVALID_FORMAT_CASES: list[tuple[str, str]] = [
    ("", "empty"),
    ("plain", "missing @"),
    ("@domain.com", "empty local part"),
    ("user@", "empty domain"),
    ("user name@example.com", "space in local"),
    ("user@dom ain.com", "space in domain"),
    ('user@exa"mple.com', "quote in domain"),
    ("user..name@example.com", "consecutive dots in local"),
    ("user@sub..domain.com", "consecutive dots in domain"),
    (".user@example.com", "leading dot in local"),
    ("user.@example.com", "trailing dot in local"),
    ("-user@example.com", "leading hyphen in local"),
    ("user-@example.com", "trailing hyphen in local"),
    ("user@.example.com", "leading dot in domain"),
    ("user@example.com.", "trailing dot in domain"),
    ("user@-example.com", "leading hyphen in domain"),
    ("user@example.com-", "trailing hyphen in domain"),
    ("user@domain", "no dot in domain (no TLD)"),
    ("user@domain.toolongtld123", "unrecognised TLD"),
    ("user@domain.123", "numeric-only TLD"),
    ("user@domain..com", "empty subdomain"),
]


@pytest.mark.parametrize("address, _reason", INVALID_FORMAT_CASES)
def test_invalid_format_addresses(address: str, _reason: str) -> None:
    """Addresses with structural problems should be rejected."""
    _bad(address)


# ---------------------------------------------------------------------------
# Boundary / type checks
# ---------------------------------------------------------------------------


def test_none_input() -> None:
    result = _bad(None)
    assert "None" in result.errors[0]


def test_non_string_input() -> None:
    result = _bad(42)
    assert "int" in result.errors[0]

    result = _bad(3.14)
    assert "float" in result.errors[0]

    result = _bad([])
    assert "list" in result.errors[0]


def test_empty_string() -> None:
    result = _bad("")
    assert "empty" in result.errors[0].lower()


def test_whitespace_only() -> None:
    result = _bad("   ")
    assert "empty" in result.errors[0].lower()


# ---------------------------------------------------------------------------
# Length edge cases
# ---------------------------------------------------------------------------


def test_total_length_exceeded() -> None:
    """Total email > 254 chars should fail."""
    local = "a" * 64  # exactly 64 = max local
    domain = "b" * 189 + ".com"  # pushes total past 254
    addr = f"{local}@{domain}"
    assert len(addr) > EMAIL_MAX_LEN
    result = _bad(addr)
    assert any("254" in e for e in result.errors)


def test_total_length_exactly_max() -> None:
    """Total email == 254 chars with valid DNS labels should pass."""
    # Build a domain of exactly 189 chars with valid labels (max 63 each)
    # 63 + "." + 63 + "." + 57 + ".com" = 63+1+63+1+57+4 = 189
    domain = "a" * 63 + "." + "b" * 63 + "." + "c" * 57 + ".com"
    assert len(domain) == 189
    local = "d" * 64  # max local
    addr = f"{local}@{domain}"
    assert len(addr) == 254, f"Expected 254, got {len(addr)}"
    _ok(addr)


def test_local_part_exceeds_max() -> None:
    local = "a" * (LOCAL_PART_MAX_LEN + 1)
    result = _bad(f"{local}@example.com")
    assert any("64" in e for e in result.errors)


def test_local_part_exactly_max() -> None:
    local = "a" * LOCAL_PART_MAX_LEN
    _ok(f"{local}@example.com")


def test_domain_exceeds_max() -> None:
    """Domain > 255 chars. Total-length guard fires first, so we check that."""
    # Use a 1-char local so total = 2 + domain_len
    # Domain of 256 chars → total = 258 > 254 → total-length error
    domain = "x" * 252 + ".com"  # 256 chars
    addr = f"a@{domain}"
    assert len(addr) > EMAIL_MAX_LEN
    result = _bad(addr)
    assert any("254" in e for e in result.errors)


def test_domain_exactly_max() -> None:
    """Domain == 255 chars with 1-char local → total 257 > 254, caught by total."""
    domain = "x" * 251 + ".com"  # 255 chars
    addr = f"a@{domain}"
    assert len(addr) == 257
    result = _bad(addr)
    assert any("254" in e for e in result.errors)


def test_domain_at_253_with_1char_local_passes() -> None:
    """Domain == 253 chars + 'a@' = 255... wait, 253+2=255 > 254. Let's do 252."""
    # Domain 252 chars + "a@" = 254 total. Use valid labels.
    # 63 + "." + 63 + "." + 63 + "." + 59 + ".com" = 63+1+63+1+63+1+59+4 = 255... too much
    # 63 + "." + 63 + "." + 63 + "." + 56 + ".com" = 63+1+63+1+63+1+56+4 = 252 ✓
    domain = "a" * 63 + "." + "b" * 63 + "." + "c" * 63 + "." + "d" * 56 + ".com"
    assert len(domain) == 252
    addr = f"x@{domain}"
    assert len(addr) == 254
    _ok(addr)


# ---------------------------------------------------------------------------
# Unicode / internationalised
# ---------------------------------------------------------------------------


def test_unicode_local_part_valid() -> None:
    """Unicode characters in local part (RFC 6531) should pass."""
    _ok("\u00fcser@example.com")


def test_idn_domain_fails_without_tld_match() -> None:
    """IDN-style domain with an unrecognised TLD should fail."""
    _bad("user@xn--mase-dpa.nonexistent")


def test_idn_domain_with_com_tld() -> None:
    """xn-- prefix domain that ends in .com should pass."""
    _ok("user@xn--mase-dpa.com")


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------


def test_normalisation_lowercases() -> None:
    result = validate_email("User@Example.COM")
    assert result.normalized == "user@example.com"


def test_normalisation_strips_whitespace() -> None:
    result = validate_email("  user@example.com  ")
    assert result.normalized == "user@example.com"


# ---------------------------------------------------------------------------
# Regression / edge
# ---------------------------------------------------------------------------


def test_double_at_sign() -> None:
    _bad("user@name@example.com")


def test_missing_local_and_domain() -> None:
    _bad("@")