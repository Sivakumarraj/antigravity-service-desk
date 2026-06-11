# Enterprise IT Service Desk — Neuro SAN Community Project

> **A native [Neuro SAN STUDIO](https://github.com/cognizant-ai-lab/neuro-san-studio) multi-agent pipeline
> that automatically classifies IT support requests into structured ServiceNow incident
> payloads — with 5-pass PII redaction, LLM-powered classification, and deterministic
> coded-tool output validation.**

[![Neuro SAN](https://img.shields.io/badge/Neuro%20SAN-Community%20Project-blue)](https://github.com/cognizant-ai-lab/neuro-san-studio)
[![Python](https://img.shields.io/badge/Python-3.11%2B-green)](https://python.org)
[![LLM](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-orange)](https://ai.google.dev)
[![uv](https://img.shields.io/badge/Managed%20by-uv-purple)](https://github.com/astral-sh/uv)

---

## Overview

This project is a community contribution to
[Neuro SAN Studio](https://github.com/cognizant-ai-lab/neuro-san-studio) — Cognizant
AI Lab's open-source multi-agent orchestration platform.

It solves a real enterprise problem: **IT helpdesk teams receive hundreds of unstructured
support emails per day** containing mixed PII, jargon, and ambiguous priorities. This
pipeline transforms those raw emails into clean, structured ServiceNow incident records
automatically — with no human triage required.

---

## Architecture

```
User Input (raw IT email)
        │
        ▼
┌───────────────────┐
│  it_service_desk  │  Front orchestrator agent (LLM)
│  (front agent)    │  Coordinates the full pipeline
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│   pii_scrubber    │  Coded Tool (deterministic, no LLM)
│                   │  5-pass regex: headers, credentials,
│                   │  prose creds, phones, email addresses
└────────┬──────────┘
         │  clean_text (PII-free)
         ▼
┌───────────────────┐
│ ticket_classifier │  LLM Agent (gemini-2.5-flash)
│                   │  Strict controlled vocabulary:
│                   │  category: Network|Database|Hardware|IAM
│                   │  priority: HIGH|MEDIUM|LOW
└────────┬──────────┘
         │  category + priority + justification
         ▼
┌───────────────────┐
│  ticket_builder   │  Coded Tool (deterministic, no LLM)
│                   │  Maps to ServiceNow Incident Table fields
│                   │  urgency/impact/priority (1/2/3 scale)
└────────┬──────────┘
         │
         ▼
ServiceNow Incident Payload (JSON)
```

---

## Key Features

| Feature | Implementation |
|---|---|
| **PII Redaction** | 5-pass regex: phone numbers, emails, passwords, tokens, headers |
| **LLM Classification** | `gemini-2.5-flash` with strict prompt guardrails |
| **Controlled Vocabulary** | Rejects any output outside `Network/Database/Hardware/IAM` × `HIGH/MEDIUM/LOW` |
| **Coded Tools** | Deterministic `pii_scrubber` and `ticket_builder` — no LLM ambiguity |
| **ServiceNow Ready** | Full Incident Table payload with urgency/impact/priority mapping |
| **Native Neuro SAN** | `tools` array, `function`/`instructions`/`parameters`, `class` bindings |

---

## Project Structure

```
antigravity-service-desk/
├── registries/
│   ├── it_service_desk.hocon   ← Native Neuro SAN agent network (main config)
│   └── manifest.hocon          ← Registers the network with Neuro SAN
├── tools/
│   ├── pii_scrubber.py         ← Coded Tool: 5-pass PII redaction
│   ├── ticket_builder.py       ← Coded Tool: ServiceNow payload builder
│   ├── ticket_parser.py        ← Shared PII utilities (used by demo)
│   └── guardrails.py           ← Pydantic v2 schema validation (used by demo)
├── config/
│   ├── llm_config.hocon        ← Default LLM: gemini-2.5-flash
│   └── plugins.hocon           ← Neuro SAN plugin configuration
├── demo.py                     ← Local simulation (does not require ns serve)
├── pyproject.toml              ← uv project config with neuro-san dependency
└── README.md
```

---

## Prerequisites

- **Python 3.11+**
- **[uv](https://github.com/astral-sh/uv)** package manager
- **Google API Key** — free tier at [aistudio.google.com](https://aistudio.google.com/app/apikey)

---

## Installation

```bash
git clone https://github.com/Sivakumarraj/antigravity-service-desk.git
cd antigravity-service-desk
uv sync
```

Set your API key:

```bash
# .env
GOOGLE_API_KEY="AIza..."
GEMINI_API_KEY="AIza..."
```

---

## Running with Neuro SAN

Start the Neuro SAN agent server:

```bash
uv run ns serve
```

In a separate terminal, chat with the IT Service Desk agent:

```bash
uv run ns chat it_service_desk
```

Example session:

```
You: Our prod Postgres cluster started throwing connection timeouts.
     Call me at +1-800-555-0199. Password was dbPass123.

Agent: {
  "category": "Database",
  "priority": "HIGH",
  "short_description": "Our prod Postgres cluster started throwing connection timeouts.",
  "urgency": "1",
  "impact": "1",
  ...
}
```

---

## Running the Local Demo

A standalone simulation (no `ns serve` required):

```bash
uv run python demo.py
```

Expected output:

```
[Stage 1] Initializing Neuro SAN Core Studio Architecture Module...
          Active Core Endpoint Engine: google/gemini-2.5-flash

[Stage 2] PII Scrubbing...
          Scrubbing complete. PII instances redacted safely.

[Stage 3] LLM Classification via gemini-2.5-flash...
          [GUARDRAIL] Validation cleared successfully.

[Stage 4] ServiceNow Payload Built.

{
  "short_description": "Our prod Postgres cluster started throwing connection timeouts.",
  "category": "Database",
  "priority": "1",
  "urgency": "1",
  ...
}
```

---

## Verifying the Neuro SAN Config

```bash
uv run ns check-config --hocon-path registries/it_service_desk.hocon
```

Expected result:

```
Working (1 unique config):
  model: gemini-2.5-flash | it_service_desk, pii_scrubber, ticket_classifier, ticket_builder
All LLM configurations are working.
```

---

## PII Redaction — 5 Passes

| Pass | Pattern | Example |
|---|---|---|
| 1 | Email headers | `From: alice@acme.com` → `` |
| 2a | Structured credentials | `password=dbPass123` → `password=[REDACTED]` |
| 2b | Prose credentials | `password was dbPass123` → `password=[REDACTED]` |
| 3 | Phone numbers | `+1-800-555-0199` → `[REDACTED]` |
| 4 | Email addresses | `user@company.com` → `[REDACTED]` |

---

## ServiceNow Field Mapping

| Neuro SAN Priority | ServiceNow `urgency` | `impact` | `priority` |
|---|---|---|---|
| `HIGH` | 1 (High) | 1 (High) | 1 (Critical) |
| `MEDIUM` | 2 (Medium) | 2 (Medium) | 2 (High) |
| `LOW` | 3 (Low) | 3 (Low) | 3 (Moderate) |

---

## Configuration

All LLM and agent settings are in `registries/it_service_desk.hocon`. To change
the model, update `llm_config.model_name`. Any model supported by Neuro SAN
can be used — see the
[Neuro SAN LLM reference](https://github.com/cognizant-ai-lab/neuro-san/blob/main/docs/agent_hocon_reference.md#model_name).

---

## License

Apache License 2.0
