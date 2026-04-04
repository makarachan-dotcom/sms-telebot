"""
AI STAND WY2.5 - Carrier Detector Module
Mobile carrier detection based on phone number prefixes
Supports Cambodia (KH) and international carriers
Created by Kimi K2.5
"""

from __future__ import annotations

import re
from typing import Dict, Optional, Tuple


# Carrier data by country
# Format: {country_code: {prefix: (carrier_name, carrier_emoji)}}
CARRIER_PREFIXES: Dict[str, Dict[str, Tuple[str, str]]] = {
    "kh": {
        # Smart (Axiata)
        "010": ("Smart", "🔵"),
        "015": ("Smart", "🔵"),
        "016": ("Smart", "🔵"),
        "069": ("Smart", "🔵"),
        "086": ("Smart", "🔵"),
        "087": ("Smart", "🔵"),
        "096": ("Smart", "🔵"),
        "098": ("Smart", "🔵"),
        # Metfone (Vietnam Telecom)
        "031": ("Metfone", "🟢"),
        "060": ("Metfone", "🟢"),
        "066": ("Metfone", "🟢"),
        "067": ("Metfone", "🟢"),
        "068": ("Metfone", "🟢"),
        "088": ("Metfone", "🟢"),
        "097": ("Metfone", "🟢"),
        # CamGSM / Cellcard
        "011": ("Cellcard", "🔴"),
        "012": ("Cellcard", "🔴"),
        "017": ("Cellcard", "🔴"),
        "061": ("Cellcard", "🔴"),
        "076": ("Cellcard", "🔴"),
        "077": ("Cellcard", "🔴"),
        "078": ("Cellcard", "🔴"),
        "079": ("Cellcard", "🔴"),
        "085": ("Cellcard", "🔴"),
        "089": ("Cellcard", "🔴"),
        "092": ("Cellcard", "🔴"),
        "095": ("Cellcard", "🔴"),
        "099": ("Cellcard", "🔴"),
        # Seatel / Cootel
        "038": ("Seatel", "🟠"),
        "013": ("Seatel", "🟠"),
        # VIETTEL (Metfone) - some overlap
        "070": ("Viettel", "🟣"),
        "093": ("Viettel", "🟣"),
        # Xinwei / Hello
        "023": ("Xinwei", "⚪"),
    },
    "us": {
        # AT&T
        "201": ("AT&T", "🔵"),
        "203": ("AT&T", "🔵"),
        "205": ("AT&T", "🔵"),
        # Verizon
        "202": ("Verizon", "🔴"),
        "212": ("Verizon", "🔴"),
        # T-Mobile
        "206": ("T-Mobile", "🟣"),
        "213": ("T-Mobile", "🟣"),
        # Sprint (now T-Mobile)
        "210": ("T-Mobile (Sprint)", "🟣"),
    },
    "uk": {
        # EE
        "074": ("EE", "🟢"),
        "075": ("EE", "🟢"),
        # Vodafone
        "077": ("Vodafone", "🔴"),
        "078": ("Vodafone", "🔴"),
        # O2
        "072": ("O2", "🔵"),
        "073": ("O2", "🔵"),
        # Three
        "079": ("Three", "🟠"),
    },
    "th": {
        "08": ("AIS", "🔵"),
        "09": ("DTAC", "🔴"),
        "06": ("True Move H", "🟣"),
    },
    "vn": {
        "032": ("Viettel", "🔴"),
        "033": ("Viettel", "🔴"),
        "034": ("Viettel", "🔴"),
        "035": ("Viettel", "🔴"),
        "036": ("Viettel", "🔴"),
        "037": ("Viettel", "🔴"),
        "038": ("Viettel", "🔴"),
        "039": ("Viettel", "🔴"),
        "056": ("Vietnamobile", "🟢"),
        "058": ("Vietnamobile", "🟢"),
        "070": ("Mobifone", "🔵"),
        "076": ("Mobifone", "🔵"),
        "077": ("Mobifone", "🔵"),
        "078": ("Mobifone", "🔵"),
        "079": ("Mobifone", "🔵"),
        "081": ("Vinaphone", "🟣"),
        "082": ("Vinaphone", "🟣"),
        "083": ("Vinaphone", "🟣"),
        "084": ("Vinaphone", "🟣"),
        "085": ("Vinaphone", "🟣"),
        "086": ("Vinaphone", "🟣"),
    },
    "sg": {
        "8": ("Singtel", "🔴"),
        "9": ("StarHub", "🟢"),
    },
    "ph": {
        "0917": ("Globe", "🔵"),
        "0918": ("Smart", "🔴"),
        "0919": ("Smart", "🔴"),
        "0920": ("Smart", "🔴"),
        "0921": ("Globe", "🔵"),
        "0922": ("Sun Cellular", "🟡"),
        "0923": ("Sun Cellular", "🟡"),
        "0925": ("Globe", "🔵"),
        "0926": ("Globe", "🔵"),
        "0927": ("Globe", "🔵"),
        "0928": ("Smart", "🔴"),
        "0929": ("Smart", "🔴"),
        "0932": ("Sun Cellular", "🟡"),
        "0933": ("Globe", "🔵"),
        "0935": ("Globe", "🔵"),
        "0936": ("Globe", "🔵"),
        "0939": ("Smart", "🔴"),
        "0942": ("Sun Cellular", "🟡"),
        "0946": ("Smart", " 🔴"),
        "0947": ("Smart", "🔴"),
        "0948": ("Globe", "🔵"),
        "0949": ("Smart", "🔴"),
        "0951": ("Smart", "🔴"),
        "0955": ("Globe", "🔵"),
        "0956": ("Globe", "🔵"),
        "0961": ("Smart", "🔴"),
        "0966": ("Globe", "🔵"),
        "0967": ("Globe", "🔵"),
        "0975": ("Globe", "🔵"),
        "0977": ("Globe", "🔵"),
        "0978": ("Globe", "🔵"),
        "0979": ("Smart", "🔴"),
        "0981": ("Smart", "🔴"),
        "0982": ("Smart", "🔴"),
        "0989": ("Smart", "🔴"),
        "0992": ("Sun Cellular", "🟡"),
        "0994": ("Sun Cellular", "🟡"),
        "0995": ("Globe", "🔵"),
        "0996": ("Globe", "🔵"),
        "0997": ("Smart", "🔴"),
        "0998": ("Smart", "🔴"),
        "0999": ("Smart", "🔴"),
    },
    "my": {
        "010": ("DiGi", "🟡"),
        "011": ("Celcom", "🔵"),
        "012": ("Maxis", "🔴"),
        "013": ("Celcom", "🔵"),
        "014": ("U Mobile", "🟢"),
        "016": ("Maxis", "🔴"),
        "017": ("Celcom", "🔵"),
        "018": ("U Mobile", "🟢"),
        "019": ("Maxis", "🔴"),
    },
    "id": {
        "0811": ("Telkomsel (Halo)", "🔴"),
        "0812": ("Telkomsel", "🔴"),
        "0813": ("Telkomsel", "🔴"),
        "0814": ("Indosat Ooredoo", "🟡"),
        "0815": ("Indosat Ooredoo", "🟡"),
        "0816": ("Indosat Ooredoo", "🟡"),
        "0817": ("XL Axiata", "🔵"),
        "0818": ("XL Axiata", "🔵"),
        "0819": ("XL Axiata", "🔵"),
        "0821": ("Telkomsel", "🔴"),
        "0822": ("Telkomsel", "🔴"),
        "0823": ("Telkomsel", "🔴"),
        "0838": ("Axis", "⚪"),
        "0851": ("Telkomsel (As)", "🔴"),
        "0852": ("Telkomsel (As)", "🔴"),
        "0853": ("Telkomsel (As)", "🔴"),
        "0855": ("Indosat Ooredoo (Im3)", "🟡"),
        "0856": ("Indosat Ooredoo (Im3)", "🟡"),
        "0857": ("Indosat Ooredoo (Im3)", "🟡"),
        "0858": ("Indosat Ooredoo (Im3)", "🟡"),
        "0877": ("XL Axiata", "🔵"),
        "0878": ("XL Axiata", "🔵"),
        "0881": ("Smartfren", "🟣"),
        "0882": ("Smartfren", "🟣"),
        "0883": ("Smartfren", "🟣"),
        "0884": ("Smartfren", "🟣"),
        "0885": ("Smartfren", "🟣"),
        "0886": ("Smartfren", "🟣"),
        "0887": ("Smartfren", "🟣"),
        "0888": ("Smartfren", "🟣"),
        "0889": ("Smartfren", "🟣"),
        "0896": ("3 (Tri)", "🟠"),
        "0897": ("3 (Tri)", "🟠"),
        "0898": ("3 (Tri)", "🟠"),
        "0899": ("3 (Tri)", "🟠"),
        "0900": ("3 (Tri)", "🟠"),
        "0908": ("3 (Tri)", "🟠"),
    },
}

# Phone number length validation per country (min, max digits without country code)
PHONE_LENGTH_RULES: Dict[str, Tuple[int, int]] = {
    "kh": (8, 9),    # Cambodia: 8-9 digits
    "us": (10, 10),  # US: exactly 10 digits
    "uk": (10, 11),  # UK: 10-11 digits
    "ca": (10, 10),  # Canada: exactly 10 digits
    "au": (9, 9),    # Australia: 9 digits
    "sg": (8, 8),    # Singapore: exactly 8 digits
    "th": (9, 9),    # Thailand: 9 digits
    "vn": (9, 10),   # Vietnam: 9-10 digits
    "ph": (10, 10),  # Philippines: 10 digits
    "my": (9, 10),   # Malaysia: 9-10 digits
    "id": (9, 12),   # Indonesia: 9-12 digits
    "jp": (10, 11),  # Japan: 10-11 digits
    "kr": (9, 11),   # South Korea: 9-11 digits
    "cn": (11, 11),  # China: exactly 11 digits
    "in": (10, 10),  # India: exactly 10 digits
}


def detect_carrier(phone_number: str, country_code: str = "kh") -> Tuple[str, str]:
    """
    Detect carrier from phone number.

    Args:
        phone_number: The local phone number (without country code, without leading 0)
        country_code: Two-letter country code (e.g., 'kh', 'us')

    Returns:
        Tuple of (carrier_name, carrier_emoji). Returns ('Unknown', '❓') if not detected.
    """
    country_code = country_code.lower()

    # Normalize: remove country code prefix if present
    phone = re.sub(r"[^\d]", "", phone_number)

    # Remove leading zeros for prefix matching
    phone_normalized = phone.lstrip("0")

    country_carriers = CARRIER_PREFIXES.get(country_code, {})
    if not country_carriers:
        return ("Unknown", "❓")

    # Sort prefixes by length descending for longest-match-first
    sorted_prefixes = sorted(country_carriers.keys(), key=len, reverse=True)

    for prefix in sorted_prefixes:
        clean_prefix = prefix.lstrip("0")
        if phone_normalized.startswith(clean_prefix):
            return country_carriers[prefix]

    return ("Unknown", "❓")


def validate_phone_number(phone_number: str, country_code: str = "kh") -> Tuple[bool, str, str]:
    """
    Validate a phone number for the given country.

    Args:
        phone_number: Phone number string (may have leading 0, spaces, dashes)
        country_code: Two-letter country code

    Returns:
        Tuple of (is_valid, cleaned_number, error_message).
        cleaned_number is without leading 0 and without non-digit chars.
        error_message is empty string if valid.
    """
    # Import COUNTRY_CODES lazily to avoid circular dependency at module load time
    from sms_service import COUNTRY_CODES as _COUNTRY_CODES  # noqa: PLC0415

    # Remove whitespace and common separators
    cleaned = re.sub(r"[\s\-\(\)\.]", "", phone_number)

    # Only allow digits and optional leading +
    if not re.match(r"^\+?\d+$", cleaned):
        return (False, "", "Phone number contains invalid characters. Use digits only.")

    # Strip leading + and country code digits if present
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
        country = _COUNTRY_CODES.get(country_code, {})
        country_code_digits = country.get("code", "")[1:]  # strip the '+'
        if country_code_digits and cleaned.startswith(country_code_digits):
            cleaned = cleaned[len(country_code_digits):]

    # Remove single leading zero
    if cleaned.startswith("0"):
        cleaned = cleaned[1:]

    if not cleaned:
        return (False, "", "Phone number is empty after removing leading zeros.")

    # Length check
    min_len, max_len = PHONE_LENGTH_RULES.get(country_code, (7, 15))
    if len(cleaned) < min_len:
        return (False, cleaned, f"Phone number is too short ({len(cleaned)} digits, minimum {min_len}).")
    if len(cleaned) > max_len:
        return (False, cleaned, f"Phone number is too long ({len(cleaned)} digits, maximum {max_len}).")

    return (True, cleaned, "")


def mask_phone_number(phone_number: str) -> str:
    """
    Mask a phone number for display (show first 4 and last 2 digits).

    Args:
        phone_number: Full phone number string

    Returns:
        Masked phone number, e.g. '+855 96 ****78'
    """
    digits_only = re.sub(r"[^\d+]", "", phone_number)
    if len(digits_only) <= 6:
        return digits_only  # too short to mask meaningfully

    # Keep first 4 visible and last 2 visible
    visible_start = digits_only[:4]
    visible_end = digits_only[-2:]
    masked_middle = "*" * (len(digits_only) - 6)
    return f"{visible_start}{masked_middle}{visible_end}"
