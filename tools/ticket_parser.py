# tools/ticket_parser.py
import re
from typing import Dict, Any

# ---------------------------------------------------------------------------
# Priority → urgency / impact map  (ServiceNow scale: 1=Critical, 2=High, 3=Low)
# ---------------------------------------------------------------------------
_PRIORITY_MAP: Dict[str, Dict[str, str]] = {
    "HIGH":   {"urgency": "1", "impact": "1", "priority": "1"},
    "MEDIUM": {"urgency": "2", "impact": "2", "priority": "2"},
    "LOW":    {"urgency": "3", "impact": "3", "priority": "3"},
}

_CATEGORY_TO_SUBCATEGORY: Dict[str, str] = {
    "Network":  "Connectivity",
    "Database": "Performance",
    "Hardware": "Failure",
    "IAM":      "Access Control",
}

# ---------------------------------------------------------------------------
# Redaction regex patterns
# ---------------------------------------------------------------------------

# Phone numbers (E.164, US, intl, dotted, dashed, parens)
_PHONE_RE = re.compile(
    r"""
    (?:\+?1[-.\s]?)?
    (?:\(\d{3}\)[-.\s]?|\d{3}[-.\s])
    \d{3}[-.\s]?\d{4}
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

# Email header chains — handles indented lines (leading whitespace before From:/To: etc.)
_HEADER_RE = re.compile(
    r"^\s*(?:From|To|Cc|Bcc|Sent|Date|Reply-To|Delivered-To|Return-Path|X-[\w-]+)\s*:[^\n]*",
    re.MULTILINE | re.IGNORECASE,
)

# Standalone email addresses
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Prose credential leak — catches: 'password was X', 'password is X', 'password: X' (no = needed)
_PROSE_CRED_RE = re.compile(
    r"(?P<key>password|passwd|pwd|token|secret|api[_-]?key)\s+(?:was|is|were|definition was|set to|used is)?\s*(?P<value>[A-Za-z0-9!@#$%^&*_\-+=.]{4,})",
    re.IGNORECASE,
)


class TicketParserTool:
    """
    Production-grade PII scrubber and ServiceNow payload builder.
    Supports both instance method (redact_pii) and static method (clean_raw_email)
    interfaces for compatibility with app.py.
    """

    REDACT_TOKEN = "[REDACTED]"

    def __init__(self, redact_token: str = "[REDACTED]"):
        self.redact_token = redact_token

    # ------------------------------------------------------------------
    # Static interface (used by app.py)
    # ------------------------------------------------------------------

    @staticmethod
    def clean_raw_email(raw_email: str) -> str:
        """Static wrapper — scrubs PII and returns clean text."""
        tool = TicketParserTool()
        clean, _ = tool.redact_pii(raw_email)
        return clean

    @staticmethod
    def map_to_servicenow_payload(
        clean_text: str,
        category: str,
        priority: str,
        caller_id: str = "api_ingest_agent",
        assignment_group: str = "NOC-L2-AutoClassify",
    ) -> Dict[str, Any]:
        """Build a standard ServiceNow Incident table JSON payload."""
        priority_upper   = priority.upper()
        category_title   = category.title()
        sn_fields        = _PRIORITY_MAP.get(priority_upper, _PRIORITY_MAP["LOW"])
        subcategory      = _CATEGORY_TO_SUBCATEGORY.get(category_title, "General")

        short_desc = next(
            (line.strip() for line in clean_text.splitlines() if line.strip()),
            "Auto-classified IT Incident",
        )[:160]

        return {
            "short_description": short_desc,
            "description":       clean_text,
            "category":          category_title,
            "subcategory":       subcategory,
            "urgency":           sn_fields["urgency"],
            "impact":            sn_fields["impact"],
            "priority":          sn_fields["priority"],
            "state":             "1",   # New
            "caller_id":         caller_id,
            "assignment_group":  assignment_group,
            "comments":          (
                f"Auto-ingested via Neuro SAN Pipeline.\n"
                f"Classifier priority={priority_upper}, category={category_title}."
            ),
            "work_notes": "PII scrubbed by TicketParserTool before ingestion.",
        }

    # ------------------------------------------------------------------
    # Instance interface (full redaction with audit report)
    # ------------------------------------------------------------------

    def redact_pii(self, raw_text: str) -> tuple[str, dict]:
        """Run 4-pass PII redaction. Returns (clean_text, audit_report)."""
        report = {
            "phones": 0, "credentials": 0,
            "email_headers": 0, "email_addresses": 0,
        }
        text = raw_text

        # Pass 1 — email headers
        def _hdr(m: re.Match) -> str:
            report["email_headers"] += 1
            return ""
        text = _HEADER_RE.sub(_hdr, text)

        # Pass 2a — structured credentials (password=value, token=value)
        def _cred(m: re.Match) -> str:
            report["credentials"] += 1
            return f"{m.group('key')}={self.redact_token}"
        text = _CRED_RE.sub(_cred, text)

        # Pass 2b — prose credentials (password was X, password definition was X)
        def _prose_cred(m: re.Match) -> str:
            report["credentials"] += 1
            return f"{m.group('key')}={self.redact_token}"
        text = _PROSE_CRED_RE.sub(_prose_cred, text)

        # Pass 3 — phone numbers
        def _phone(m: re.Match) -> str:
            report["phones"] += 1
            return self.redact_token
        text = _PHONE_RE.sub(_phone, text)

        # Pass 4 — residual email addresses
        def _email(m: re.Match) -> str:
            report["email_addresses"] += 1
            return self.redact_token
        text = _EMAIL_RE.sub(_email, text)

        # Collapse extra blank lines
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        report["total"] = sum(report.values())
        return text, report
