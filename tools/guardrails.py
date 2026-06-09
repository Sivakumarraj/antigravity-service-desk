# tools/guardrails.py
import json
import re
from enum import Enum
from typing import Tuple, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError


# ---------------------------------------------------------------------------
# Controlled vocabularies — enforced at Pydantic level, not just description
# ---------------------------------------------------------------------------

class CategoryEnum(str, Enum):
    Network  = "Network"
    Database = "Database"
    Hardware = "Hardware"
    IAM      = "IAM"


class PriorityEnum(str, Enum):
    HIGH   = "HIGH"
    MEDIUM = "MEDIUM"
    LOW    = "LOW"


# ---------------------------------------------------------------------------
# Strict Pydantic schema
# ---------------------------------------------------------------------------

class ServiceNowTicketSchema(BaseModel):
    """
    Strict schema for structured-classifier agent output.
    Extra fields are forbidden — blocks hallucinated keys.
    Category and priority are enum-locked — blocks invalid values.
    """

    model_config = {
        "extra": "forbid",               # reject any unknown field immediately
        "str_strip_whitespace": True,
        "use_enum_values": True,
    }

    category: CategoryEnum = Field(
        ...,
        description="ITSM category — strictly: Network, Database, Hardware, IAM",
    )
    priority: PriorityEnum = Field(
        ...,
        description="Incident priority — strictly: HIGH, MEDIUM, LOW",
    )
    justification: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Plain-text rationale (10–1000 chars)",
    )

    @field_validator("category", mode="before")
    @classmethod
    def normalise_category(cls, v: Any) -> str:
        """Accept 'network' -> 'Network', case-insensitive."""
        if isinstance(v, str):
            mapped = {c.lower(): c for c in CategoryEnum.__members__}
            normalised = mapped.get(v.strip().lower())
            if normalised is None:
                raise ValueError(
                    f"Invalid category '{v}'. "
                    f"Allowed: {list(CategoryEnum.__members__.keys())}"
                )
            return normalised
        return v

    @field_validator("priority", mode="before")
    @classmethod
    def normalise_priority(cls, v: Any) -> str:
        """Accept 'high', 'High', 'HIGH' — rejects 'CRITICAL', 'P1', etc."""
        if isinstance(v, str):
            upper = v.strip().upper()
            if upper not in PriorityEnum.__members__:
                raise ValueError(
                    f"Invalid priority '{v}'. "
                    f"Allowed: {list(PriorityEnum.__members__.keys())}"
                )
            return upper
        return v

    @model_validator(mode="after")
    def justification_no_pii(self) -> "ServiceNowTicketSchema":
        """Defence-in-depth: reject if justification still contains raw credentials."""
        pii_hint = re.search(
            r"(password\s*[:=]|passwd\s*[:=]|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b)",
            self.justification,
            re.IGNORECASE,
        )
        if pii_hint:
            raise ValueError(
                "Justification contains PII or credentials. "
                "Run PII scrubber before classification."
            )
        return self


# ---------------------------------------------------------------------------
# Guardrail interceptor
# ---------------------------------------------------------------------------

_MARKDOWN_FENCE_RE = re.compile(r"```(?:json|JSON)?\s*([\s\S]*?)```", re.MULTILINE)
_JSON_BLOCK_RE     = re.compile(r"\{[\s\S]+\}", re.MULTILINE)


class TicketGuardrail:
    """
    LLM output interceptor:
    1. Strips markdown fences (```json ... ```)
    2. Parses JSON
    3. Validates against ServiceNowTicketSchema (enum-locked fields)
    4. Returns (is_valid, data_dict, error_message)
    """

    def __init__(self, strict_pii_check: bool = True):
        self.strict_pii_check = strict_pii_check

    @classmethod
    def validate_output(cls, raw_llm_output: str) -> Tuple[bool, Dict[str, Any], str]:
        if not raw_llm_output or not raw_llm_output.strip():
            return False, {}, "LLM returned an empty response."

        # Step 1 — extract JSON from markdown or prose
        json_str = cls._extract_json(raw_llm_output)
        if json_str is None:
            return False, {}, "No JSON object found in LLM output."

        # Step 2 — parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return False, {}, f"JSON parse error: {e}"

        # Step 3 — Pydantic validation (enum enforcement happens here)
        try:
            ticket = ServiceNowTicketSchema(**data)
            return True, ticket.model_dump(), ""
        except ValidationError as e:
            errors = "; ".join(
                f"[{' -> '.join(str(l) for l in err['loc'])}] {err['msg']}"
                for err in e.errors()
            )
            return False, {}, f"Validation errors: {errors}"

    @staticmethod
    def _extract_json(text: str) -> str | None:
        fence = _MARKDOWN_FENCE_RE.search(text)
        if fence:
            candidate = fence.group(1).strip()
            if candidate:
                return candidate
        block = _JSON_BLOCK_RE.search(text)
        if block:
            return block.group(0).strip()
        stripped = text.strip()
        if stripped.startswith("{"):
            return stripped
        return None
