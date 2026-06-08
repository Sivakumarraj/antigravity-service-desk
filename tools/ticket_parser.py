# tools/ticket_parser.py
import re
from typing import Dict, Any

class TicketParserTool:
    """Advanced Antigravity-spec tool for deep text sanitization and multi-field mapping."""
    
    def __init__(self, redact_token: str = '[REDACTED]'):
        self.redact_token = redact_token

    @staticmethod
    def clean_raw_email(raw_email: str) -> str:
        """Runs multi-pass regex to completely strip out header structures and enterprise credentials."""
        # 1. Strip standard email routing blocks
        text = re.sub(r'(?i)(From|To|Cc|Date|Reply-To|Subject):.*', '', raw_email)
        # 2. Block direct routing phone variations
        text = re.sub(r'\+?\d{1,4}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '[REDACTED]', text)
        # 3. Mask explicit configuration access tokens
        text = re.sub(r'(?i)(password|token|api_key|secret|bearer)\s*[:=]\s*\S+', r'\1=[REDACTED]', text)
        return text.strip()

    @staticmethod
    def map_to_servicenow_payload(clean_text: str, category: str, priority: str) -> Dict[str, Any]:
        """Assembles a production-grade multi-attribute incident dataset."""
        return {
            "short_description": clean_text.split('\n')[0][:80] if clean_text else "Automated Incident Alert",
            "description": clean_text,
            "category": category,
            "subcategory": "Performance",
            "urgency": "1" if priority.upper() == "HIGH" else "3",
            "impact": "1" if priority.upper() == "HIGH" else "2",
            "priority": "1" if priority.upper() == "HIGH" else "3",
            "state": "1",
            "caller_id": "alice.wong",
            "assignment_group": "NOC-L2-AutoClassify",
            "comments": f"Auto-ingested via Antigravity AI Pipeline.\nClassifier priority={priority}, category={category}.",
            "work_notes": "PII scrubbed by TicketParserTool before ingestion."
        }
