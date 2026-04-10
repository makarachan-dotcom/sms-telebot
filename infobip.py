"""
SMS Telegram Bot – Infobip Integration Module
===============================================
Sends SMS messages through the **Infobip REST API** (v2 / advanced endpoint).

Only **Cambodian numbers (+855)** are accepted.  The module handles all phone
number normalisation so the rest of the application never needs to worry about
leading zeros or missing country codes.

Phone number rules
------------------
* Digits only, with an optional leading ``+`` or ``0``.
* If the number starts with ``+855`` it is already in E.164 form and is used
  as-is.
* If the number starts with ``0`` (local Cambodian format, e.g. ``012345678``),
  the leading ``0`` is stripped and ``+855`` is prepended.
* Any other numeric string (e.g. ``12345678``) has ``+855`` prepended directly.
* Numbers that do not match the expected Cambodian pattern raise a
  :class:`ValueError`.

References
----------
* Infobip SMS API docs: https://www.infobip.com/docs/api/channels/sms
* API keys:            https://portal.infobip.com/dev/api-keys
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

CAMBODIA_PREFIX: str = "+855"

# Cambodian mobile numbers: 8 or 9 digits after the country code.
# E.g. +85512345678  (10 digits)  or  +855012345678 (before stripping 0)
_KH_PATTERN = re.compile(r"^\+855[1-9]\d{7,8}$")

# Infobip SMS endpoint (appended to INFOBIP_BASE_URL)
_SMS_PATH: str = "/sms/2/text/advanced"

# HTTP request timeout in seconds
_TIMEOUT: int = 30


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class SMSSendResult:
    """
    Encapsulates the outcome of a single SMS send operation.

    Attributes
    ----------
    success:
        ``True`` if Infobip accepted the message for delivery.
    recipient:
        The normalised E.164 phone number the SMS was addressed to.
    message_id:
        Infobip's bulk/message identifier (``None`` on failure).
    status_name:
        Human-readable delivery status string returned by Infobip.
    error:
        Error description if *success* is ``False``.
    raw_response:
        Full JSON dict from Infobip (useful for debugging).
    timestamp:
        When the send was attempted.
    """

    success: bool
    recipient: str
    message_id: Optional[str] = None
    status_name: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[dict] = field(default=None, repr=False)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────────────────────────────────────
# Phone number helpers
# ─────────────────────────────────────────────────────────────────────────────


def format_cambodian_number(raw: str) -> str:
    """
    Normalise *raw* to an E.164 Cambodian phone number (``+855XXXXXXXX``).

    Accepted input formats
    ~~~~~~~~~~~~~~~~~~~~~~
    * ``+85512345678``    – already E.164; validated and returned unchanged.
    * ``012345678``       – local with leading zero; zero stripped, +855 added.
    * ``12345678``        – 8 digits without leading zero; ``+855`` prepended.
    * ``85512345678``     – without the ``+``; ``+`` prepended.

    Parameters
    ----------
    raw:
        User-supplied phone number string (may contain spaces or dashes).

    Returns
    -------
    str
        E.164-formatted number, e.g. ``+85512345678``.

    Raises
    ------
    ValueError
        When *raw* cannot be normalised to a valid Cambodian number.
    """
    # Strip whitespace, dashes, and parentheses.
    cleaned: str = re.sub(r"[\s\-\(\)]", "", raw.strip())

    if not cleaned:
        raise ValueError("Phone number must not be empty.")

    # Already E.164 with +855
    if cleaned.startswith("+855"):
        normalised = cleaned
    # Local format with leading 0 (e.g. 012345678)
    elif cleaned.startswith("0"):
        normalised = CAMBODIA_PREFIX + cleaned[1:]
    # Raw digits starting with 855 (without +)
    elif cleaned.startswith("855"):
        normalised = "+" + cleaned
    # Bare local digits without leading 0 (e.g. 12345678)
    elif cleaned.isdigit():
        normalised = CAMBODIA_PREFIX + cleaned
    else:
        raise ValueError(
            f"Cannot parse phone number '{raw}'. "
            "Please enter a Cambodian number, e.g. 012345678 or +85512345678."
        )

    # Validate against the expected pattern
    if not _KH_PATTERN.match(normalised):
        raise ValueError(
            f"'{normalised}' does not look like a valid Cambodian mobile number "
            "(expected +855 followed by 8–9 digits, first digit non-zero)."
        )

    return normalised


# ─────────────────────────────────────────────────────────────────────────────
# Infobip client
# ─────────────────────────────────────────────────────────────────────────────


class InfobipClient:
    """
    Lightweight synchronous wrapper around the Infobip SMS REST API.

    Parameters
    ----------
    api_key:
        Infobip App API key obtained from
        https://portal.infobip.com/dev/api-keys.
    base_url:
        Your Infobip base URL, e.g. ``https://XXXX.api.infobip.com``.
        Do **not** include a trailing slash.

    Example
    -------
    >>> client = InfobipClient(api_key="KEY", base_url="https://abc.api.infobip.com")
    >>> result = client.send_sms(to="+85512345678", text="Hello!")
    >>> if result.success:
    ...     print("Sent! Message ID:", result.message_id)
    """

    def __init__(self, api_key: str, base_url: str) -> None:
        if not api_key:
            raise ValueError("INFOBIP_API_KEY must not be empty.")
        if not base_url:
            raise ValueError("INFOBIP_BASE_URL must not be empty.")

        self._api_key: str = api_key
        self._base_url: str = base_url.rstrip("/")
        self._session: requests.Session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"App {self._api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def send_sms(
        self,
        to: str,
        text: str,
        sender: str = "SMSBot",
    ) -> SMSSendResult:
        """
        Send a single SMS message via the Infobip *Advanced* endpoint.

        The *to* number is automatically normalised to a valid Cambodian E.164
        format before the API call is made.

        Parameters
        ----------
        to:
            Recipient phone number (Cambodian format; see
            :func:`format_cambodian_number` for accepted forms).
        text:
            SMS body text.  Must be non-empty and ≤ 160 characters for a
            single-part message (longer messages are split by Infobip).
        sender:
            Alphanumeric sender ID shown on the recipient's device.
            The Infobip account must support the chosen sender ID.

        Returns
        -------
        SMSSendResult
            Outcome of the send operation.

        Raises
        ------
        ValueError
            When the phone number cannot be normalised (caller should handle
            and report back to the user).
        """
        # ── 1. Validate / normalise phone number ──────────────────────────
        normalised_to: str = format_cambodian_number(to)
        logger.info("send_sms: to=%s text_len=%d", normalised_to, len(text))

        # ── 2. Build request payload ───────────────────────────────────────
        payload: dict = {
            "messages": [
                {
                    "destinations": [{"to": normalised_to}],
                    "from": sender,
                    "text": text,
                }
            ]
        }

        url: str = self._base_url + _SMS_PATH

        # ── 3. Call the API ────────────────────────────────────────────────
        try:
            response = self._session.post(url, json=payload, timeout=_TIMEOUT)
            response.raise_for_status()
            data: dict = response.json()
        except requests.exceptions.HTTPError as exc:
            error_body = ""
            try:
                error_body = exc.response.json().get("requestError", {}).get(
                    "serviceException", {}
                ).get("text", str(exc))
            except Exception:
                error_body = str(exc)
            logger.warning("Infobip HTTP error: %s", error_body)
            return SMSSendResult(
                success=False,
                recipient=normalised_to,
                error=f"HTTP {exc.response.status_code}: {error_body}",
                raw_response=None,
            )
        except requests.exceptions.RequestException as exc:
            logger.warning("Infobip network error: %s", exc)
            return SMSSendResult(
                success=False,
                recipient=normalised_to,
                error=f"Network error: {exc}",
            )

        # ── 4. Parse response ──────────────────────────────────────────────
        try:
            messages_list: list = data.get("messages", [])
            if not messages_list:
                return SMSSendResult(
                    success=False,
                    recipient=normalised_to,
                    error="Infobip returned an empty messages list.",
                    raw_response=data,
                )

            msg_info: dict = messages_list[0]
            status_obj: dict = msg_info.get("status", {})
            group_name: str = status_obj.get("groupName", "")
            status_name: str = status_obj.get("name", "UNKNOWN")
            message_id: Optional[str] = msg_info.get("messageId")

            # Infobip uses groupName "PENDING" or "ACCEPTED" for successfully
            # submitted messages.
            success: bool = group_name in ("PENDING", "ACCEPTED")

            logger.info(
                "send_sms result: to=%s status=%s id=%s",
                normalised_to,
                status_name,
                message_id,
            )

            return SMSSendResult(
                success=success,
                recipient=normalised_to,
                message_id=message_id,
                status_name=status_name,
                error=None if success else f"Status: {status_name}",
                raw_response=data,
            )
        except (KeyError, IndexError, TypeError) as exc:
            logger.error("Unexpected Infobip response structure: %s | %s", exc, data)
            return SMSSendResult(
                success=False,
                recipient=normalised_to,
                error=f"Unexpected API response: {exc}",
                raw_response=data,
            )

    def close(self) -> None:
        """Release the underlying :class:`requests.Session`."""
        self._session.close()

    # ── Context-manager support ────────────────────────────────────────────

    def __enter__(self) -> "InfobipClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton factory
# ─────────────────────────────────────────────────────────────────────────────

_client: Optional[InfobipClient] = None


def get_infobip_client(api_key: str = "", base_url: str = "") -> InfobipClient:
    """
    Return the module-level :class:`InfobipClient` singleton, creating it on
    the first call.

    If *api_key* and *base_url* are provided they override any previously
    cached singleton (useful in tests).

    Parameters
    ----------
    api_key:
        Infobip API key.  Defaults to the value from :mod:`config`.
    base_url:
        Infobip base URL.  Defaults to the value from :mod:`config`.
    """
    global _client

    if api_key or base_url or _client is None:
        # Import lazily to avoid circular imports at module load time
        from config import INFOBIP_API_KEY, INFOBIP_BASE_URL  # noqa: PLC0415

        _client = InfobipClient(
            api_key=api_key or INFOBIP_API_KEY,
            base_url=base_url or INFOBIP_BASE_URL,
        )

    return _client
