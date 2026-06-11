# tools/pii_scrubber.py
#
# Neuro SAN Coded Tool — PII Scrubber
#
# This tool is invoked by the `pii_scrubber` agent in
# registries/it_service_desk.hocon. It strips all PII from
# raw IT support text before the text is passed to any LLM.
#
# Implements the Neuro SAN CodedTool async interface.

import re
from typing import Any


# ---------------------------------------------------------------------------
# Compiled regex patterns (module-level for performance)
# ---------------------------------------------------------------------------

# Phone numbers — E.164, US, international, dotted, dashed, parens
_PHONE_RE = re.compile(
    r"""
    (?:\+?1[-.\\s]?)?
    (?:\(\d{3}\)[-.\\s]?|\d{3}[-.\\s])
    \d{3}[-.\\s]?\d{4}
    (?:\s?(?:x|ext|extension)\.?\s?\d{1,6})?
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Inline credentials: password=, token=, api_key=, secret=, bearer=
_CRED_RE = re.compile(
    r"""
    (?P<key>password|passwd|pwd|token|secret|api[_-]?key|apikey|auth|bearer|credential)
    \s*[:=]\s*
    (?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|\S+)
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Email header lines — handles indented headers (leading whitespace)
_HEADER_RE = re.compile(
    r"^\s*(?:From|To|Cc|Bcc|Sent|Date|Reply-To|Delivered-To|Return-Path|X-[\w-]+)\s*:[^\n]*",
    re.MULTILINE | re.IGNORECASE,
)

# Standalone email addresses
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Prose credential leak — "password was X", "token is Y", "password definition was Z"
_PROSE_CRED_RE = re.compile(
    r"(?P<key>password|passwd|pwd|token|secret|api[_-]?key)"
    r"\s+(?:was|is|were|definition was|set to|used is)?\s*"
    r"(?P<value>[A-Za-z0-9!@#$%^&*_\-+=.]{4,})",
    re.IGNORECASE,
)

_REDACT = "[REDACTED]"


# ---------------------------------------------------------------------------
# Neuro SAN CodedTool interface
# ---------------------------------------------------------------------------

class PiiScrubberTool:
    """
    Neuro SAN coded tool that performs 5-pass PII redaction on raw IT support text.

    Invoked by the `pii_scrubber` agent in registries/it_service_desk.hocon.

    Passes:
        1. Email routing headers (From:, To:, Cc:, Date:, ...)
        2. Structured inline credentials  (password=X, token=X)
        3. Prose credentials              (password was X, token is Y)
        4. Phone numbers                  (+1-800-555-0199, (512) 867-5309)
        5. Residual email addresses       (user@company.com)
    """

    async def __call__(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """
        Neuro SAN async entry point.

        Args:
            tool_input: {"raw_text": "<user's IT support request>"}

        Returns:
            {"clean_text": "<PII-scrubbed text>", "redaction_count": <int>}
        """
        raw_text: str = tool_input.get("raw_text", "")
        clean_text, report = self._scrub(raw_text)
        return {
            "clean_text": clean_text,
            "redaction_count": report["total"],
        }

    @staticmethod
    def _scrub(raw: str) -> tuple[str, dict]:
        """Run 5-pass PII redaction. Returns (clean_text, audit_report)."""
        report = {
            "email_headers": 0,
            "credentials": 0,
            "phones": 0,
            "email_addresses": 0,
        }
        text = raw

        # Pass 1 — email header lines
        def _hdr(m: re.Match) -> str:
            report["email_headers"] += 1
            return ""
        text = _HEADER_RE.sub(_hdr, text)

        # Pass 2a — structured credentials (password=value)
        def _cred(m: re.Match) -> str:
            report["credentials"] += 1
            return f"{m.group('key')}={_REDACT}"
        text = _CRED_RE.sub(_cred, text)

        # Pass 2b — prose credentials (password was X)
        def _prose(m: re.Match) -> str:
            report["credentials"] += 1
            return f"{m.group('key')}={_REDACT}"
        text = _PROSE_CRED_RE.sub(_prose, text)

        # Pass 3 — phone numbers
        def _phone(m: re.Match) -> str:
            report["phones"] += 1
            return _REDACT
        text = _PHONE_RE.sub(_phone, text)

        # Pass 4 — residual email addresses
        def _email(m: re.Match) -> str:
            report["email_addresses"] += 1
            return _REDACT
        text = _EMAIL_RE.sub(_email, text)

        # Collapse extra blank lines
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        report["total"] = sum(v for k, v in report.items())
        return text, report
