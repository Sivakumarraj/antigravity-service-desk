# Neuro SAN Studio — Enterprise IT Service Desk Pipeline

An enterprise-grade, fault-tolerant multi-agent IT helpdesk automation pipeline built natively on the **Cognizant Neuro SAN Studio Platform**. This application is structured as a decoupled standalone project utilizing the modern `uv` toolchain to orchestrate, validate, and secure enterprise IT workflows with zero human intervention.

---

## 🚀 Key Production Challenges Solved

1. **Resilient Vendor Fallback (HOCON)**: Implements declarative vendor-agnostic fallback chains inside `registries/it_service_desk.hocon` to survive mid-workflow token throttling (`status_429`) — instantly shifting from Google Gemini to fallback providers.
2. **Deterministic Output Guardrails (Pydantic v2)**: Deploys strict enum-locked runtime interceptors to eliminate LLM hallucinations — automatically trapping illegal values like `CRITICAL` and driving self-healing correction prompt routines.
3. **Secure Pipeline Boundaries (Regex Scrubbing)**: Employs multi-pass PII pre-processors (5 passes) to intercept and mask phone numbers, inline credentials (`password=`, `token=`), prose credentials (`password was X`), email headers, and email addresses before any payload transmission.

---

## 📂 Project Structure

```text
neuro-san-service-desk-pipeline/
├── config/
│   ├── llm_config.hocon          # Core Neuro SAN Studio LLM model config
│   └── plugins.hocon             # Observability and logging plugin config
├── registries/
│   ├── manifest.hocon            # Agent network registry manifest
│   └── it_service_desk.hocon    # Multi-agent network with fallback chain
├── mcp/
│   └── mcp_info.hocon            # MCP server tool configuration
├── tools/
│   ├── guardrails.py            # Pydantic v2 enum-locked ServiceNow schema
│   └── ticket_parser.py         # 5-pass PII scrubber & ServiceNow payload builder
├── .env                          # Local API credentials (not committed to git)
├── pyproject.toml                # uv project dependencies
├── uv.lock                       # Dependency lockfile
└── app.py                        # Pipeline execution entrypoint
```

---

## 🛠️ Installation & Quick Start

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.14+.

### 1. Clone the Repository
```bash
git clone https://github.com/Sivakumarraj/antigravity-service-desk.git
cd antigravity-service-desk
```

### 2. Sync Dependencies
```bash
uv sync
```

### 3. Set Your API Key
Create a `.env` file in the project root:
```text
GEMINI_API_KEY="your-google-ai-studio-key-here"
```
Get a free key at: https://aistudio.google.com/app/apikey

### 4. Run the Pipeline
```bash
uv run python app.py
```

---

## 📊 Live Output

Running `uv run python app.py` produces this output:

```text
========================================================================
  Neuro SAN IT Service Desk -- Auto-Classifier Pipeline
========================================================================

[Stage 1] Initializing Neuro SAN Core Studio Architecture Module...
          Loaded configuration registry: config/llm_config.hocon
          Active Core Endpoint Engine: google/gemini-1.5-flash

[Stage 2] Triggering TicketParserTool: Cleaning PII Data Boundaries...
          Scrubbing Operation complete. PII instances redacted safely.

[Stage 3] Routing Context to 'structured_classifier_agent' via Google Tier...
          [LLM] Calling google/gemini-1.5-flash ...
          [GUARDRAIL] Intercepting output string for Pydantic parsing...
          [!] Guardrail Loop Triggered: Value error, Invalid priority 'CRITICAL'. Allowed: ['HIGH', 'MEDIUM', 'LOW']
          Automatically re-routing back to Gemini for correction protocol...
          [GUARDRAIL] [PASSED] Validation cleared successfully on attempt 2.

[Stage 4] Building Final ServiceNow Incident Payload...

================ FINAL SERVICENOW METADATA PAYLOAD ================
{
  "short_description": "Our prod Postgres cluster (10.12.5.200) started throwing connection timeouts.",
  "description": "Our prod Postgres cluster (10.12.5.200) started throwing connection timeouts. \n    Call my mobile at [REDACTED] for verification. Temp verification password=[REDACTED]",
  "category": "Database",
  "subcategory": "Performance",
  "urgency": "1",
  "impact": "1",
  "priority": "1",
  "state": "1",
  "caller_id": "api_ingest_agent",
  "assignment_group": "NOC-L2-AutoClassify",
  "comments": "Auto-ingested via Neuro SAN Pipeline.\nClassifier priority=HIGH, category=Database.",
  "work_notes": "PII scrubbed by TicketParserTool before ingestion."
}
====================================================================

Pipeline Execution Complete. State saved.
```

---

## 🛡️ PII Redaction — What Gets Scrubbed

| PII Type | Example Input | Output |
|---|---|---|
| Email header lines | `From: alice.wong@acmecorp.com` | *(line removed)* |
| Structured credentials | `password=Tr0ub4dor&3` | `password=[REDACTED]` |
| Prose credentials | `password was dbPass123` | `password=[REDACTED]` |
| Phone numbers | `+1-800-555-0199` | `[REDACTED]` |
| Email addresses | `bob.smith@corp.com` | `[REDACTED]` |

---

## 🤖 Agent Network — `registries/it_service_desk.hocon`

| Agent | Role |
|---|---|
| `ingestion_agent` | PII data cleansing and redaction specialist |
| `structured_classifier_agent` | Strict JSON classifier (category + priority + justification) |

LLM fallback chain: `gemini-1.5-flash` → `gemini-1.5-pro`

---

## ✅ Guardrail Enforcement

The `TicketGuardrail` enforces:
- `category` must be one of: `Network`, `Database`, `Hardware`, `IAM`
- `priority` must be one of: `HIGH`, `MEDIUM`, `LOW`
- Extra/hallucinated fields → immediately rejected (`extra = "forbid"`)
- Justification containing raw credentials → rejected

---

## 🏆 Open Source Status

- **Framework**: Built on [`neuro-san-studio`](https://github.com/cognizant-ai-lab/neuro-san-studio)
- **Community**: Listed in [Neuro SAN Studio Community Projects](https://github.com/cognizant-ai-lab/neuro-san-studio#community-projects)
- **Reviewed by**: `@ofrancon` — Cognizant AI Lab (`lgtm, thanks!`)
- **License**: MIT
