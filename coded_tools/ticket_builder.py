# coded_tools/ticket_builder.py
#
# Neuro SAN Coded Tool — ServiceNow Ticket Builder
#
# Invoked by the `ticket_builder` agent in registries/it_service_desk.hocon.
# Builds a complete ServiceNow Incident Table JSON payload from LLM output.
#
# Uses the official neuro_san.interfaces.coded_tool.CodedTool interface.

from typing import Any
from typing import Dict
from typing import Union

from neuro_san.interfaces.coded_tool import CodedTool


# ---------------------------------------------------------------------------
# ServiceNow field mappings
# ---------------------------------------------------------------------------

# ServiceNow urgency/impact/priority scale: 1=High, 2=Medium, 3=Low
_PRIORITY_MAP: Dict[str, Dict[str, str]] = {
    "HIGH":   {"urgency": "1", "impact": "1", "priority": "1"},
    "MEDIUM": {"urgency": "2", "impact": "2", "priority": "2"},
    "LOW":    {"urgency": "3", "impact": "3", "priority": "3"},
}

_CATEGORY_SUBCATEGORY: Dict[str, str] = {
    "Network":  "Connectivity",
    "Database": "Performance",
    "Hardware": "Failure",
    "IAM":      "Access Control",
}


class TicketBuilderTool(CodedTool):
    """
    Neuro SAN coded tool that builds a ServiceNow Incident Table JSON payload
    from the classifier agent's output (category + priority + clean_text).

    Invoked by the `ticket_builder` agent in registries/it_service_desk.hocon.
    """

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Called by the Neuro SAN agent hierarchy when ticket_builder is invoked.

        :param args: {
            "clean_text": "<PII-scrubbed request>",
            "category":   "Network" | "Database" | "Hardware" | "IAM",
            "priority":   "HIGH" | "MEDIUM" | "LOW",
        }
        :param sly_data: Sly data passed through the agent hierarchy (read-only).
        :return: ServiceNow-ready incident JSON dict.
        """
        clean_text: str = args.get("clean_text", "")
        category: str   = args.get("category", "Network").strip().title()
        priority: str   = args.get("priority", "LOW").strip().upper()

        sn_fields   = _PRIORITY_MAP.get(priority, _PRIORITY_MAP["LOW"])
        subcategory = _CATEGORY_SUBCATEGORY.get(category, "General")

        # First non-empty line, capped at 160 chars
        short_desc = next(
            (line.strip() for line in clean_text.splitlines() if line.strip()),
            "Auto-classified IT Incident",
        )[:160]

        return {
            "short_description": short_desc,
            "description":       clean_text,
            "category":          category,
            "subcategory":       subcategory,
            "urgency":           sn_fields["urgency"],
            "impact":            sn_fields["impact"],
            "priority":          sn_fields["priority"],
            "state":             "1",  # New
            "caller_id":         "api_ingest_agent",
            "assignment_group":  "NOC-L2-AutoClassify",
            "comments": (
                f"Auto-ingested via Neuro SAN Pipeline.\n"
                f"Classifier priority={priority}, category={category}."
            ),
            "work_notes": "PII scrubbed by PiiScrubberTool before ingestion.",
        }
