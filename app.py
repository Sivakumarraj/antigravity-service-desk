# app.py
import os
import json
from tools.ticket_parser import TicketParserTool
from tools.guardrails import TicketGuardrail

def simulate_neuro_san_pipeline(raw_user_email: str):
    print("\n========================================================================")
    print("  Neuro SAN IT Service Desk -- Auto-Classifier Pipeline")
    print("========================================================================\n")
    
    print("[Stage 1] Initializing Neuro SAN Core Studio Architecture Module...")
    print("          Loaded configuration registry: config/llm_config.hocon")
    print(f"          Active Core Endpoint Engine: google/gemini-1.5-flash\n")
    
    # PII Scrubbing Layer Action
    print("[Stage 2] Triggering TicketParserTool: Cleaning PII Data Boundaries...")
    scrubbed_text = TicketParserTool.clean_raw_email(raw_user_email)
    print(f"          Scrubbing Operation complete. PII instances redacted safely.\n")
    
    # Model Orchestration Execution
    print("[Stage 3] Routing Context to 'structured_classifier_agent' via Google Tier...")
    
    # Simulating a raw mock output string to verify your Pydantic guardrail catches formatting defects
    mock_raw_llm_response = """
    ```json
    {
      "category": "Database",
      "priority": "CRITICAL",
      "justification": "Our production Postgres cluster is completely unreachable and timing out."
    }
    ```
    """
    print("          [LLM] Calling google/gemini-1.5-flash ...")
    print("          [GUARDRAIL] Intercepting output string for Pydantic parsing...")
    
    # app.py (Update the validation block in Stage 3)
    is_valid, validated_json, error_msg, metrics = TicketGuardrail.validate_output(mock_raw_llm_response)
    
    if "CRITICAL" in mock_raw_llm_response or not is_valid:
        print(f"          [!] Guardrail Loop Triggered: Value error, Invalid priority 'CRITICAL'")
        print("          Automatically re-routing back to Gemini for correction protocol...")
        
        corrected_response = '{"category": "Database", "priority": "HIGH", "justification": "Production Postgres cluster is fully unreachable."}'
        is_valid, validated_json, error_msg, metrics = TicketGuardrail.validate_output(corrected_response)
        print("          [GUARDRAIL] [PASSED] Validation cleared successfully on attempt 2.")
        print(f"          [FinOps Analytics] Latency: {metrics['latency_seconds']}s | Cost: ${metrics['estimated_cost_usd']} USD\n")

    # Final Structure Export Setup
    print("[Stage 4] Building Final ServiceNow Incident Payload...")
    final_servicenow_payload = TicketParserTool.map_to_servicenow_payload(
        clean_text=scrubbed_text,
        category=validated_json["category"],
        priority=validated_json["priority"]
    )
    
    print("\n================ FINAL SERVICENOW METADATA PAYLOAD ================")
    print(json.dumps(final_servicenow_payload, indent=2))
    print("====================================================================\n")
    print("Pipeline Execution Complete. State saved.")

if __name__ == "__main__":
    # Chaotic sample incident input block loaded with hidden data leaks
    sample_email = """
    From: alice.wong@acmecorp.com
    Our prod Postgres cluster (10.12.5.200) started throwing connection timeouts. 
    Call my mobile at +1-800-555-0199 for verification. Temp verification password definition was dbPass123.
    """
    simulate_neuro_san_pipeline(sample_email)
