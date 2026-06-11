# tools/ticket_builder.py
#
# Neuro SAN Coded Tool — ServiceNow Ticket Builder
#
# This tool is invoked by the `ticket_classifier` agent in
# registries/it_service_desk.hocon after the LLM produces a
# category + priority classification.
#
# Implements the Neuro SAN CodedTool async interface.

from typing import Any


# ---------------------------------------------------------------------------
# ServiceNow field mappings
# ---------------------------------------------------------------------------

# ServiceNow urgency/impact/priority scale: 1=Critical/High, 2=Medium, 3=Low
_PRIORITY_MAP: dict[str, dict[str, str]] = {
    "HIGH":   {"urgency": "1", "impact": "1", "priority": "1"},
    "MEDIUM": {"urgency": "2", "impact": "2", "priority": "2"},
    "LOW":    {"urgency": "3", "impact": "3", "priority": "3"},
}

_CATEGORY_SUBCATEGORY: dict[str, str] = {
    "Network":  "Connectivity",
    "Database": "Performance",
    "Hardware": "Failure",
    "IAM":      "Access Control",
}


# ---------------------------------------------------------------------------
# Neuro SAN CodedTool interface
# ---------------------------------------------------------------------------

class TicketBuilderTool:
    """
    Neuro SAN coded tool that builds a ServiceNow Incident Table JSON payload
    from the classifier agent's output (category + priority + clean_text).

    Invoked by the `ticket_classifier` agent in registries/it_service_desk.hocon.
    """

    async def __call__(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """
        Neuro SAN async entry point.

        Args:
            tool_input: {
                "clean_text": "<PII-scrubbed request>",
                "category":   "Network" | "Database" | "Hardware" | "IAM",
                "priority":   "HIGH" | "MEDIUM" | "LOW",
            }

        Returns:
            ServiceNow-ready incident JSON dict.
        """
        clean_text: str = tool_input.get("clean_text", "")
        category: str   = tool_input.get("category", "Network").title()
        priority: str   = tool_input.get("priority", "LOW").upper()

        sn_fields  = _PRIORITY_MAP.get(priority, _PRIORITY_MAP["LOW"])
        subcategory = _CATEGORY_SUBCATEGORY.get(category, "General")

        # First non-empty line, capped at 160 chars, as the short description
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
