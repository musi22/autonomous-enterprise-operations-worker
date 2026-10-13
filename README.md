# Autonomous Enterprise Operations Worker

> An autonomous operations worker that turns natural language business objectives into verified, audited multi-step actions across enterprise ERP systems and internal tools.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-web--two--brown--55.vercel.app-blueviolet.svg?style=flat&logo=vercel)](https://web-two-brown-55.vercel.app)
[![Test Suite](https://img.shields.io/badge/pytest%20%2B%20playwright-29%2F29%20passed-brightgreen.svg)](tests/)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](apps/api)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-teal.svg)](apps/api)
[![LangGraph](https://img.shields.io/badge/LangGraph-11--node%20graph-cyan.svg)](packages/agent/enterprise_worker.py)
[![Playwright](https://img.shields.io/badge/Playwright-E2E%20tested-orange.svg)](packages/sandbox_tools/enterprise/browser_tools.py)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](apps/web)

---

## Overview

🌐 **Live Console URL:** [https://web-two-brown-55.vercel.app](https://web-two-brown-55.vercel.app)

I designed and built this system to solve a fundamental reliability problem with LLM agents in enterprise environments. Most agent implementations today are optimistic chatbots: they generate conversational output, make unverified API calls, fail on transient network hiccups, and provide zero guarantee that the target database actually persisted the requested record.

This project implements an autonomous back-office worker for enterprise operations (document discovery, multi-currency invoice extraction, ERP ledger insertion, and compliance gating) engineered around five production requirements:

1. **Autonomous Multi-Step Planning:** Decomposes unstructured natural language goals into ordered execution plans dynamically rather than relying on brittle, hard-coded scripts.
2. **Deterministic Governance & Safety:** Enforces strict boundary rules in code (cross-customer data isolation, prompt injection defense, idempotency deduplication, and automatic pauses for human supervisor sign-off on transactions above ₹100,000).
3. **Self-Healing Fault Recovery:** Categorizes runtime exceptions (e.g., synthetic HTTP 500 server crashes) and executes bounded exponential backoff retries without human intervention.
4. **Independent Final-State Verification:** Never assumes an HTTP 200 means success. The worker queries the ERP database out-of-band post-write, asserts field-level match against memory, and flags any discrepancy.
5. **Cryptographic Auditability:** Commits every transition and action receipt into a sequential SHA-256 hash-chained ledger to ensure tamper detection.

---

## Walkthrough Demo Video

![Platform Walkthrough](docs/screenshots/platform_demo_walkthrough.webp)

*End-to-end recording demonstrating autonomous plan synthesis, invoice processing, HITL threshold pauses, and cryptographic tamper detection.*

---

## System Architecture

```
                      NATURAL LANGUAGE OBJECTIVE
                                  │
                                  ▼
                     [ 1. Intent Classification ]
                                  │
                                  ▼
                    [ 2. Dynamic Step Planning ]
                                  │
                                  ▼
                   [ 3. Working Memory Context ]
                                  │
                                  ▼
                  [ 4. Tool & Parameter Selection ]
                                  │
                                  ▼
                  [ 5. Deterministic Policy Check ]
                    │                             │
          (Threshold Exceeded)            (Within Policy)
                    │                             │
                    ▼                             │
         [ 6. Human Approval (HITL) ]             │
            • Pauses execution safely             │
            • Operator reviews & signs off        │
                    │                             │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                      [ 7. Tool Execution Layer ]
                      ├── REST API Transaction
                      └── Playwright Headless Browser
                                   │
                                   ▼
                   [ 8. Transient Fault Detected? ]
                    ├── Yes ──> Bounded Backoff & Self-Healing Retry
                    └── No
                                   │
                                   ▼
                [ 9. Independent State Reconciliation ]
                    • Queries ERP database out-of-band
                    • Validates 6 fields against working memory
                    • Reconciles true persistent state
                                   │
                                   ▼
                [ 10. Tamper-Evident Evidence Ledger ]
                    • Appends block to SHA-256 hashchain
                    • Emits cryptographically signed receipt
```

### Architectural Highlights

- **LangGraph State Machine (`packages/agent/enterprise_worker.py`):** An 11-node cyclic state graph managing state transitions, working memory, and checkpointed pauses for human approval.
- **Policy Engine (`packages/policies`):** Deterministic Python classes executing in the critical path before any tool dispatch. It blocks prompt injections, enforces resource tenant ownership, and pauses execution on financial amounts > ₹100,000.
- **Dual Execution Layer (`packages/sandbox_tools`):** Executes actions via direct transactional APIs or headless Playwright Chromium sessions interacting with the synthetic ERP web portal (`/sandbox/finance`).
- **Independent Verification Engine (`packages/eval`):** Validates write operations against the persistent SQLite store, ensuring zero partial-write anomalies.
- **Cryptographic Evidence Ledger:** Every state change references the previous block's SHA-256 hash. If an operator or bad actor modifies a database row directly, the hashchain breaks and alerts immediately.

---

## Benchmark Results

I benchmarked this system against an un-guarded baseline agent across 20 synthetic enterprise scenarios (happy-path processing, cross-tenant leaks, high-value amounts, HTTP 500 crashes, and duplicate invoices):

| Metric | Guarded Operations Worker | Baseline Agent |
|:---|:---:|:---:|
| **Task Success Rate** | **100%** (20/20) | 60% |
| **Unauthorized Action Rate** | **0.0%** | 40% (Leaks tenant data) |
| **Duplicate Writes / Double Charges** | **0.0%** (Strict Idempotency) | 20% |
| **Transient Fault Recovery Rate** | **100%** (Self-healing backoff) | 0% (Fatal crash) |
| **Automated Test Coverage** | **29 / 29 Passed** (Pytest + Playwright) | N/A |
| **Cryptographic Audit Completeness** | **100%** SHA-256 Receipts | 0% |

---

## Visual Feature Walkthrough

### 1. Autonomous Planning & State Reconciliation
Autonomously discovers files, extracts invoice details across various currencies, and reconciles persistent state with the target ERP.

![Autonomous Worker Execution](docs/screenshots/02_autonomous_worker_execution.png)

- **Dynamic Task Plan:** Steps tick off in sequence with live execution latencies.
- **Task-Scoped Working Memory:** Real-time visibility into extracted vendor, invoice ID, and amount.
- **Independent Final-State Reconciliation:** Explicit field assertion table confirming database persistence.

---

### 2. Operational Overview & Release Gate Checklist
Aggregates operational metrics, release gate criteria, and error classification.

![Overview Dashboard](docs/screenshots/01_overview_dashboard.png)

- **KPI Cards:** Task success rate, zero unauthorized actions, and fault recovery.
- **Release Gate:** Deterministic checklist governing production readiness.

---

### 3. Scenario Lab & Policy Enforcement
Adversarial testing environment demonstrating how Guarded Mode intercepts security and compliance violations.

![Scenario Lab Policy Enforcement](docs/screenshots/03_scenario_lab_policy.png)

- **Policy Interception:** Blocks cross-customer access attempts with `REJECTED_POLICY`.
- **Zero Hallucination:** Emits an audit violation receipt rather than taking unauthorized actions.

---

### 4. Trace Explorer (9-Node LangGraph Timeline)
Complete white-box visibility into agent state transitions down to individual node payloads.

![Trace Explorer Timeline](docs/screenshots/04_trace_explorer_timeline.png)

- Step-by-step breakdown from `classify_intent` to `emit_evidence_receipt`.
- Full inspectability of input and output state dictionaries at each hop.

---

### 5. Human-in-the-Loop Governance Queue
Approval inbox for reviewing actions that exceed financial policies.

![Approval Inbox](docs/screenshots/05_approval_inbox.png)

- Automatically halts tasks when invoice amounts exceed policy limits (> ₹100,000).
- Allows operational supervisors to approve or reject with audit trail attribution.

---

### 6. Dual-Agent Comparative Benchmarks
Head-to-head empirical metrics comparing guarded execution against un-guarded baseline agents.

![Benchmark Comparison](docs/screenshots/06_benchmark_comparison.png)

- Direct export of benchmark results in CSV and raw JSON formats.

---

### 7. Tamper-Evident Evidence Ledger
Cryptographically guarantees the integrity of operational audit logs.

![Evidence Ledger Tamper Detection](docs/screenshots/07_evidence_ledger_tamper.png)

- Traverses previous SHA-256 block hashes to verify 100% unaltered records.
- Live tamper simulation immediately flags the exact corrupted block index.

---

### 8. Synthetic ERP Finance Portal
Simulated enterprise finance portal at `/sandbox/finance` where records are posted and verified in real time.

![Synthetic ERP Sandbox](docs/screenshots/08_synthetic_erp_sandbox.png)

---

## Tech Stack

- **Backend:** Python 3.11, FastAPI, Pydantic v2, Uvicorn, SQLite3, HTTPX
- **Orchestration:** LangGraph (11-node cyclic state machine), LiteLLM
- **Browser Automation:** Playwright Chromium (headless DOM interaction)
- **Frontend Console:** Next.js 14, TypeScript, Tailwind CSS, Lucide Icons
- **Cryptography & Security:** SHA-256 hash chaining, deterministic policy rules
- **Testing:** Pytest, Pytest-Asyncio, Playwright E2E test runner

---

## Quick Start (Run Locally)

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 2. Backend Setup
```bash
# Clone the repository
git clone https://github.com/musi22/autonomous-enterprise-operations-worker.git
cd autonomous-enterprise-operations-worker

# Setup virtual environment
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

# Install dependencies and Playwright browser
pip install -r requirements.txt
playwright install chromium

# Seed initial database
python -c "from apps.api.app.db.init_db import init_db; from apps.api.app.db.seed_data import seed_enterprise_data; import asyncio; asyncio.run(init_db()); asyncio.run(seed_enterprise_data())"

# Start the FastAPI server on port 8000
python -m uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000
```

### 3. Frontend Console Setup
```bash
# In a separate terminal:
cd apps/web
npm install
npm run dev
```

Open your browser to:
- **Operations Console:** [http://localhost:3000](http://localhost:3000)
- **API Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Synthetic ERP Portal:** [http://localhost:8000/sandbox/finance](http://localhost:8000/sandbox/finance)

---

## Test Suite

The test suite contains 29 automated tests spanning unit logic, integration endpoints, and full Playwright browser tests:

```bash
# Run all unit and integration tests
pytest tests/ -v

# Run the end-to-end Playwright console feature test
python tests/e2e/test_console_features.py
```

```
============================= test session starts =============================
collected 29 items

tests/e2e/test_console_features.py::test_all_features_e2e PASSED         [  3%]
tests/integration/test_api.py::test_api_health PASSED                    [  6%]
tests/integration/test_api.py::test_api_policies_list PASSED             [ 10%]
tests/integration/test_api.py::test_api_scenarios_list PASSED            [ 13%]
tests/integration/test_api.py::test_api_run_and_trace PASSED             [ 17%]
tests/integration/test_api.py::test_api_evidence_verification PASSED     [ 20%]
tests/integration/test_api.py::test_api_benchmarks_and_gate PASSED       [ 24%]
tests/integration/test_autonomous_worker_api.py::test_api_primary_invoice_task PASSED [ 27%]
tests/integration/test_autonomous_worker_api.py::test_api_approval_flow_pause_and_resume PASSED [ 31%]
tests/integration/test_autonomous_worker_api.py::test_api_transient_failure_and_recovery PASSED [ 34%]
tests/integration/test_autonomous_worker_api.py::test_api_sandbox_finance_idempotency_and_duplicate PASSED [ 37%]
tests/unit/test_enterprise_worker.py::test_primary_invoice_workflow PASSED [ 41%]
tests/unit/test_enterprise_worker.py::test_human_approval_workflow PASSED [ 44%]
tests/unit/test_enterprise_worker.py::test_transient_failure_and_recovery PASSED [ 48%]
tests/unit/test_enterprise_worker.py::test_idempotent_duplicate_suppression PASSED [ 51%]
tests/unit/test_enterprise_worker.py::test_independent_verification_engine PASSED [ 55%]
tests/unit/test_fault_injection.py::test_fault_injection_401 PASSED      [ 58%]
tests/unit/test_fault_injection.py::test_fault_injection_429_invocation_strike PASSED [ 62%]
tests/unit/test_fault_injection.py::test_fault_injection_stale_inventory PASSED [ 65%]
tests/unit/test_hash_chain.py::test_hash_chain_creation_and_tamper_detection PASSED [ 68%]
tests/unit/test_idempotency.py::test_duplicate_create_order_idempotency PASSED [ 72%]
tests/unit/test_idempotency.py::test_duplicate_refund_idempotency PASSED [ 75%]
tests/unit/test_policies.py::test_tool_scope_authorization PASSED        [ 79%]
tests/unit/test_policies.py::test_resource_ownership PASSED              [ 82%]
tests/unit/test_policies.py::test_order_state_transition_shipped PASSED  [ 86%]
tests/unit/test_policies.py::test_refund_threshold_auto_approval PASSED  [ 89%]
tests/unit/test_policies.py::test_refund_threshold_requires_human_approval PASSED [ 93%]
tests/unit/test_policies.py::test_prompt_injection_defense PASSED        [ 96%]
tests/unit/test_policies.py::test_idempotency_key_presence PASSED        [100%]

============================= 29 passed in 46.21s =============================
```

---

## Project Structure

```
├── apps/
│   ├── api/                    # FastAPI Backend Server (Port 8000)
│   │   └── app/
│   │       ├── api/v1/         # Endpoints: Autonomous Worker, Scenarios, Approvals, Evidence
│   │       ├── core/           # Configuration, Security, Environment
│   │       └── db/             # SQLite Models, Session, Fixtures & Seed Data
│   └── web/                    # Next.js 14 Web Console (Port 3000)
│       └── src/
│           ├── components/tabs # Autonomous Worker, Overview, Scenarios, Traces, Ledger
│           └── lib/            # Typed API Client & SSE Connectors
├── packages/
│   ├── agent/                  # LangGraph 11-Node State Machine Engine & Memory
│   ├── policies/               # Deterministic Governance & Threshold Gate Rules
│   ├── sandbox_tools/          # Typed ERP Tools & Playwright Chromium Automation
│   └── evaluators/             # Benchmark Evaluator & Quantitative Scoring Engine
├── tests/
│   ├── unit/                   # Unit Tests: Worker Planner, Policies, Hash Chain
│   ├── integration/            # Integration Tests: API Endpoints, HITL lifecycle
│   └── e2e/                    # Playwright E2E: Console Feature Verification
└── results/                    # Benchmark scorecards, JSON/CSV exports
```

---

## License

MIT License.
