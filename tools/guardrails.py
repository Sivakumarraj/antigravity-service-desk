# tools/guardrails.py
import json
import time
from typing import Tuple, Dict, Any
from pydantic import BaseModel, Field, ValidationError

class ServiceNowTicketSchema(BaseModel):
    category: str = Field(description="Must match: Network, Database, Hardware, IAM")
    priority: str = Field(description="Must match: HIGH, MEDIUM, LOW")
    justification: str = Field(description="System impact details summary.")

    class Config:
        extra = "forbid"

class TicketGuardrail:
    """Compliance tracking and FinOps observability guardrail for Neuro SAN loops."""
    
    def __init__(self, strict_pii_check: bool = True):
        self.strict_pii_check = strict_pii_check

    @classmethod
    def validate_output(cls, raw_llm_output: str) -> Tuple[bool, Dict[str, Any], str, Dict[str, Any]]:
        start_time = time.time()
        try:
            clean_str = raw_llm_output.strip().replace("```json", "").replace("```", "").strip()
            parsed_data = json.loads(clean_str)
            validated_data = ServiceNowTicketSchema(**parsed_data)
            
            # Calculate mock token metrics for FinOps observability tracking
            input_tokens = len(raw_llm_output) // 4
            output_tokens = len(clean_str) // 4
            estimated_cost = ((input_tokens / 1_000_000) * 0.075) + ((output_tokens / 1_000_000) * 0.30)
            latency = time.time() - start_time
            
            observability_metrics = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost_usd": round(estimated_cost, 6),
                "latency_seconds": round(latency, 4)
            }
            
            return True, validated_data.model_dump(), "", observability_metrics
            
        except (json.JSONDecodeError, ValidationError, ValueError) as err:
            latency = time.time() - start_time
            error_metrics = {"latency_seconds": round(latency, 4), "estimated_cost_usd": 0.0}
            return False, {}, str(err), error_metrics
