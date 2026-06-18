# Enterprise IT Service Desk — Neuro SAN Community Project

> **A native [Neuro SAN](https://github.com/cognizant-ai-lab/neuro-san) multi-agent pipeline
> that automatically classifies IT support requests into structured ServiceNow incident
> payloads — with 5-pass PII redaction, LLM-powered classification, and deterministic
> coded-tool output validation.**

[![Neuro SAN](https://img.shields.io/badge/Neuro%20SAN-Community%20Project-blue)](https://github.com/cognizant-ai-lab/neuro-san-studio)
[![Python](https://img.shields.io/badge/Python-3.12%2B-green)](https://python.org)
[![LLM](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-orange)](https://ai.google.dev)
[![uv](https://img.shields.io/badge/Managed%20by-uv-purple)](https://github.com/astral-sh/uv)

---

## Overview

This is a community project for
[Neuro SAN Studio](https://github.com/cognizant-ai-lab/neuro-san-studio) — Cognizant AI Lab's
open-source multi-agent orchestration platform.

The project automates enterprise IT helpdesk triage. IT support teams receive hundreds of
unstructured emails daily. This Neuro SAN agent network transforms those raw emails into
clean, structured ServiceNow incident records automatically — with zero manual work.

---

## Architecture

The agent network is defined in `registries/it_service_desk.hocon` and consists of
four agents arranged in a pipeline:

```
User Input (raw IT support email)
        │
        ▼
┌───────────────────────┐
│   it_service_desk     │  LLM Agent — Front orchestrator.
│                       │  Coordinates the full pipeline.
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│    pii_scrubber       │  Coded Tool (no LLM — deterministic regex).
│                       │  5-pass PII redaction: removes phone numbers,
│                       │  email addresses, passwords, tokens, headers.
└──────────┬────────────┘
           │  clean_text
           ▼
┌───────────────────────┐
│  ticket_classifier    │  LLM Agent (gemini-2.5-flash).
│                       │  Classifies: category (Network/Database/Hardware/IAM)
│                       │  and priority (HIGH/MEDIUM/LOW).
└──────────┬────────────┘
           │  category + priority
           ▼
┌───────────────────────┐
│   ticket_builder      │  Coded Tool (no LLM — deterministic mapping).
│                       │  Builds complete ServiceNow Incident Table payload.
└──────────┬────────────┘
           │
           ▼
   ServiceNow Incident Payload (JSON)
```

---

## Project Structure

```
antigravity-service-desk/
├── registries/
│   ├── it_service_desk.hocon   ← Native Neuro SAN agent network definition
│   └── manifest.hocon          ← Registers the agent network
├── coded_tools/
│   ├── pii_scrubber.py         ← CodedTool: 5-pass PII redaction
│   └── ticket_builder.py       ← CodedTool: ServiceNow payload builder
├── config/
│   └── llm_config.hocon        ← Default LLM: gemini-2.5-flash
├── demo.py                     ← Standalone local demo (no server needed)
├── pyproject.toml
└── README.md
```

---

## Prerequisites

- **Python 3.12+**
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
# .env (never commit this file)
GOOGLE_API_KEY="AIza..."
```

---

## Running with Neuro SAN

To start both the backend Neuro SAN server and the frontend client UI in this project, run the standard Neuro SAN Studio startup command:

```bash
uv run ns run
```

This will automatically load the agent network configuration defined in `registries/manifest.hocon` and serve the agents.

---

## Running the Local Demo

A standalone simulation that does not require a running Neuro SAN server:

```bash
uv run python demo.py
```

Expected output:

```
[Stage 1] Initializing Neuro SAN Core Studio Architecture Module...
          Active Core Endpoint Engine: google/gemini-2.5-flash

[Stage 2] PiiScrubberTool: Cleaning PII Data Boundaries...
          Scrubbing complete. PII instances redacted safely.

[Stage 3] Routing to ticket_classifier via Google Tier...
          [LLM] Calling google/gemini-2.5-flash ...
          [GUARDRAIL] Validation cleared successfully.

[Stage 4] Building Final ServiceNow Incident Payload...

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
  model: gemini-2.5-flash | it_service_desk, ticket_classifier
All LLM configurations are working.
```

---

## Coded Tools

Coded tools inherit from `neuro_san.interfaces.coded_tool.CodedTool` and implement
`async_invoke(args, sly_data)`. They run deterministically with no LLM call.

| Tool | Class | Purpose |
|---|---|---|
| `pii_scrubber` | `coded_tools.pii_scrubber.PiiScrubberTool` | 5-pass regex PII redaction |
| `ticket_builder` | `coded_tools.ticket_builder.TicketBuilderTool` | ServiceNow payload builder |

---

## PII Redaction — 5 Passes

| Pass | Pattern | Example |
|---|---|---|
| 1 | Email headers | `From: alice@acme.com` → removed |
| 2a | Structured credentials | `password=dbPass123` → `password=[REDACTED]` |
| 2b | Prose credentials | `password was dbPass123` → `password=[REDACTED]` |
| 3 | Phone numbers | `+1-800-555-0199` → `[REDACTED]` |
| 4 | Email addresses | `user@company.com` → `[REDACTED]` |

---

## ServiceNow Field Mapping

| Priority | ServiceNow `urgency` | `impact` | `priority` |
|---|---|---|---|
| `HIGH` | 1 | 1 | 1 |
| `MEDIUM` | 2 | 2 | 2 |
| `LOW` | 3 | 3 | 3 |

---

## License

Apache License 2.0
