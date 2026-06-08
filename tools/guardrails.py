# tools/guardrails.py
import json
from typing import Tuple, Dict, Any
from pydantic import BaseModel, Field, ValidationError

class ServiceNowTicketSchema(BaseModel):
    category: str = Field(description="Must match: Network, Database, Hardware, IAM")
    priority: str = Field(description="Must match: HIGH, MEDIUM, LOW")
    justification: str = Field(description="System impact details summary.")

    class Config:
        extra = "forbid"  # Instantly drops unauthorized structural inputs

class TicketGuardrail:
    """Compliance tracking guardrail designed for Antigravity state isolation validation layers."""
    
    def __init__(self, strict_pii_check: bool = True):
        self.strict_pii_check = strict_pii_check

    @classmethod
    def validate_output(cls, raw_llm_output: str) -> Tuple[bool, Dict[str, Any], str]:
        try:
            # Drop structural markdown block formatting
            clean_str = raw_llm_output.strip().replace("```json", "").replace("```", "").strip()
            parsed_data = json.loads(clean_str)
            
            # Enforce schema constraints
            validated_data = ServiceNowTicketSchema(**parsed_data)
            return True, validated_data.model_dump(), ""
            
        except (json.JSONDecodeError, ValidationError, ValueError) as err:
            return False, {}, str(err)
