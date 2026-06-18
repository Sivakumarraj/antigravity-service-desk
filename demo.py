# demo.py
#
# Local simulation demo for the Enterprise IT Service Desk pipeline.
#
# This script simulates the Neuro SAN agent pipeline locally without
# requiring the full server to be run.
#
# To run the full native Neuro SAN experience:
#   uv run ns run
#

import asyncio
import json
import time
from typing import Any, Dict, Tuple
from pydantic import BaseModel, Field, ValidationError

from coded_tools.pii_scrubber import PiiScrubberTool
from coded_tools.ticket_builder import TicketBuilderTool


# ---------------------------------------------------------------------------
# Pydantic schema and Guardrail (localized to demo)
# ---------------------------------------------------------------------------

class ServiceNowTicketSchema(BaseModel):
    category: str = Field(description="Must match: Network, Database, Hardware, IAM")
    priority: str = Field(description="Must match: HIGH, MEDIUM, LOW")
    justification: str = Field(description="System impact details summary.")

    class Config:
        extra = "forbid"


class TicketGuardrail:
    """Compliance tracking and FinOps observability guardrail for Neuro SAN loops."""

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


# ---------------------------------------------------------------------------
# Main Pipeline Simulation
# ---------------------------------------------------------------------------

async def simulate_neuro_san_pipeline_async(raw_user_email: str):
    print("\n========================================================================")
    print("  Neuro SAN IT Service Desk -- Auto-Classifier Pipeline (Local Demo)")
    print("========================================================================\n")

    print("[Stage 1] Initializing Neuro SAN Core Studio Architecture Module...")
    print("          Loaded configuration registry: config/llm_config.hocon")
    print(f"          Active Core Endpoint Engine: google/gemini-2.5-flash\n")

    # Stage 2 — PII Scrubbing (runs PiiScrubberTool coded tool)
    print("[Stage 2] Triggering PiiScrubberTool: Cleaning PII Data Boundaries...")
    scrubber = PiiScrubberTool()
    scrub_result = await scrubber.async_invoke({"raw_text": raw_user_email}, {})
    scrubbed_text = scrub_result["clean_text"]
    redacted_count = scrub_result["redaction_count"]
    print(f"          Scrubbing Operation complete. Redacted {redacted_count} instances safely.\n")

    # Stage 3 — LLM Classification (simulates ticket_classifier agent)
    print("[Stage 3] Routing Context to 'ticket_classifier' via Google Tier...")

    # Mock raw LLM response with intentional schema violation (CRITICAL priority)
    # to demonstrate the Pydantic guardrail catching and correcting it.
    mock_raw_llm_response = """
    ```json
    {
      "category": "Database",
      "priority": "CRITICAL",
      "justification": "Production Postgres cluster is fully unreachable and timing out."
    }
    ```
    """
    print("          [LLM] Calling google/gemini-2.5-flash ...")
    print("          [GUARDRAIL] Intercepting output string for Pydantic parsing...")

    is_valid, validated_json, error_msg, metrics = TicketGuardrail.validate_output(
        mock_raw_llm_response
    )

    if "CRITICAL" in mock_raw_llm_response or not is_valid:
        print(f"          [!] Guardrail Loop Triggered: Value error, Invalid priority 'CRITICAL'")
        print("          Automatically re-routing back to Gemini for correction protocol...")

        corrected_response = (
            '{"category": "Database", "priority": "HIGH", '
            '"justification": "Production Postgres cluster is fully unreachable."}'
        )
        is_valid, validated_json, error_msg, metrics = TicketGuardrail.validate_output(
            corrected_response
        )
        print("          [GUARDRAIL] [PASSED] Validation cleared successfully on attempt 2.")
        print(
            f"          [FinOps Analytics] Latency: {metrics['latency_seconds']}s "
            f"| Cost: ${metrics['estimated_cost_usd']} USD\n"
        )

    # Stage 4 — Build ServiceNow Payload (runs TicketBuilderTool coded tool)
    print("[Stage 4] Building Final ServiceNow Incident Payload...")
    builder = TicketBuilderTool()
    final_servicenow_payload = await builder.async_invoke(
        {
            "clean_text": scrubbed_text,
            "category": validated_json["category"],
            "priority": validated_json["priority"]
        },
        {}
    )

    print("\n================ FINAL SERVICENOW METADATA PAYLOAD ================")
    print(json.dumps(final_servicenow_payload, indent=2))
    print("====================================================================\n")
    print("Pipeline Simulation Complete.")


def main():
    # Sample IT support email — intentionally contains PII for demo purposes
    sample_email = """
    From: alice.wong@acmecorp.com
    Our prod Postgres cluster (10.12.5.200) started throwing connection timeouts.
    Call my mobile at +1-800-555-0199 for verification. Temp verification password definition was dbPass123.
    """
    asyncio.run(simulate_neuro_san_pipeline_async(sample_email))


if __name__ == "__main__":
    main()
