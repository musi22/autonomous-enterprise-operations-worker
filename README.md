# Autonomous Enterprise Operations Worker

> **Production-Grade AI Digital Employee with Autonomous Planning, Deterministic Policy Governance, Fault Recovery, and Independent Cryptographic Verification.**

[![Test Suite](https://img.shields.io/badge/Pytest%20%2B%20Playwright-29%2F29%20PASSED-success?style=for-the-badge&logo=pytest)](tests/)
[![Release Gate](https://img.shields.io/badge/Release%20Gate-PASSED%20(100%25)-emerald?style=for-the-badge)](results/ENTERPRISE_EVAL_SCORECARD.md)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](apps/api)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white)](apps/api)
[![LangGraph](https://img.shields.io/badge/LangGraph-11--Node%20State%20Machine-cyan?style=for-the-badge)](packages/agent/enterprise_worker.py)
[![Playwright](https://img.shields.io/badge/Playwright-E2E%20Browser%20Automation-orange?style=for-the-badge&logo=playwright)](packages/sandbox_tools/enterprise/browser_tools.py)
[![Next.js](https://img.shields.io/badge/Next.js-14%20Console-black?style=for-the-badge&logo=next.js)](apps/web)

---

## 📌 Recruiter & Technical Evaluator Summary

Most AI agent demonstrations are **fragile conversational wrappers**: they make blind API calls, crash on transient network errors, fail silently on malformed responses, and lack auditability.

This project demonstrates **production-grade enterprise agent engineering**. It is an autonomous operations worker designed for mission-critical back-office workflows (finance ERP entry, document discovery, cross-system reconciliation) equipped with:

- 🧠 **Genuine Autonomy:** Decomposes open-ended goals into dynamic 8-step plans without hard-coded workflow scripts.
- 🛡️ **Deterministic Governance:** Enforces strict boundary rules (cross-tenant isolation, prompt injection defenses, idempotency keys, and human-in-the-loop approvals for transactions > ₹100k).
- 🔁 **Self-Healing Fault Recovery:** Features automated fault classification with bounded exponential backoff (HTTP 500 retry recovery).
- 🔍 **Independent State Reconciliation:** Never trusts raw HTTP 200 responses; queries the target ERP out-of-band to assert persistent database integrity.
- 🔐 **Cryptographic Auditability:** Commits every state transition and action receipt into a tamper-evident SHA-256 hashchain ledger.

---

## 🏆 Key Metrics & Engineering Highlights

| Metric | Guarded AI Worker | Naive Baseline Agent |
|:---|:---:|:---:|
| **Task Success Rate** | **100%** (10/10 Enterprise Scenarios) | 60% |
| **Unauthorized / Policy Violation Rate** | **0.0%** | 40% (Leaks customer data) |
| **Duplicate Writes / Double Charges** | **0.0%** (Strict Idempotency) | 20% |
| **Fault Recovery Rate (HTTP 500)** | **100%** (Self-healing backoff) | 0% (Fatal crash) |
| **Automated Test Coverage** | **29 / 29 Passed** (Pytest + Playwright) | N/A |
| **Audit Completeness** | **100%** SHA-256 Cryptographic Proofs | 0% |

---

## 🏗️ Architecture & Execution Flow

```
                      NATURAL LANGUAGE OBJECTIVE
                                  │
                                  ▼
                     [ 1. Intent Classification ]
                                  │
                                  ▼
                   [ 2. Dynamic 8-Step Planning ]
                                  │
                                  ▼
                  [ 3. Task Working Memory Store ]
                                  │
                                  ▼
                 [ 4. Tool & Parameter Selection ]
                                  │
                                  ▼
                 [ 5. Deterministic Policy Check ]
                   │                             │
        (Threshold Exceeded)                  (Within Policy)
                   │                             │
                   ▼                             │
        [ 6. Human Approval (HITL) ]             │
           • Pauses execution                    │
           • Operator reviews & signs off        │
                   │                             │
                   └──────────────┬──────────────┘
                                  │
                                  ▼
                     [ 7. Tool Execution Layer ]
                     ├── REST API Transaction
                     └── Playwright Browser Automation
                                  │
                                  ▼
                  [ 8. Transient Fault Detected? ]
                   ├── Yes ──> Bounded Backoff & Self-Healing Retry
                   └── No
                                  │
                                  ▼
               [ 9. Independent State Reconciliation ]
                   • Queries target ERP out-of-band
                   • Compares 6 fields against working memory
                   • Flags partial writes / discrepancies
                                  │
                                  ▼
               [ 10. Tamper-Evident Evidence Ledger ]
                   • SHA-256 Hashchain commit
                   • Verified receipt emitted
```

---

## 💻 Tech Stack & Skills Demonstrated

| Domain | Technology / Library | What Was Built / Demonstrated |
|:---|:---|:---|
| **Agentic State Machine** | **LangGraph / Python 3.11** | 11-node cyclic state graph with checkpointing, pause/resume approval lifecycles, and working memory. |
| **API Backend** | **FastAPI + Pydantic v2** | High-throughput async REST API with typed request schemas, SSE streaming, and OpenAPI/Swagger documentation. |
| **Frontend Console** | **Next.js 14 + Tailwind CSS** | Real-time engineering dashboard with trace visualizer, scenario lab, approval inbox, and audit ledger. |
| **Browser Automation** | **Playwright (Chromium)** | Headless & headed DOM automation navigating synthetic ERP forms, table reads, and button actions. |
| **Resilience & Safety** | **Deterministic Policies** | Custom policy engine enforcing tenant boundaries, prompt injection filters, and financial approval gates. |
| **Data & Cryptography** | **SQLite3 + SHA-256** | ACID transactional store with cryptographic hash chaining and real-time tamper detection. |
| **Quality & Verification** | **Pytest + Playwright E2E** | 29 automated test cases spanning unit logic, integration endpoints, and full browser UI workflows. |

---

## 🎯 Core Features Evaluators Can Test

### 1. Primary Workflow: Autonomous Invoice Processing
- **Input:** *"Find the latest unpaid invoice from Acme, extract amount and due date, enter into our finance system, and verify."*
- **Execution:** Discovers file `ACM-2026-001`, extracts ₹45,000, generates idempotency key, posts to ERP, and verifies matching fields via out-of-band DB reconciliation.

### 2. Human-in-the-Loop Policy Governance (> ₹100,000)
- **Input:** *"Process the latest Contoso invoice, but do not enter invoices above ₹100,000 without my approval."*
- **Execution:** Detects ₹150,000 invoice, automatically halts execution in a safe state, generates an approval item in the UI inbox, and seamlessly resumes upon human approval.

### 3. Self-Healing Resilience (HTTP 500 Auto-Recovery)
- **Execution:** Simulates ERP crash (`HTTP 500 Internal Server Error`). The worker classifies the transient fault, executes bounded exponential backoff, retries safely, and succeeds without human intervention.

### 4. Cryptographic Evidence Ledger & Tamper Proofing
- **Execution:** Every state change is chained via SHA-256 hashes. Users can click **"Simulate DB Tampering"** in the UI to see the platform immediately flag the exact corrupted block index.

---

## 🚀 60-Second Quick Start

### 1. Clone & Setup Backend
```bash
git clone https://github.com/musi22/autonomous-enterprise-operations-worker.git
cd autonomous-enterprise-operations-worker

# Setup Python Virtual Environment
python -m venv .venv
.\.venv\Scripts\activate      # On Windows
# source .venv/bin/activate   # On Linux/macOS

# Install dependencies & Playwright browser
pip install -r requirements.txt
playwright install chromium

# Seed synthetic enterprise database
python -c "from apps.api.app.db.init_db import init_db; from apps.api.app.db.seed_data import seed_enterprise_data; import asyncio; asyncio.run(init_db()); asyncio.run(seed_enterprise_data())"

# Start FastAPI server on port 8000
python -m uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000
```

### 2. Setup Frontend Console
```bash
# In a new terminal window:
cd apps/web
npm install
npm run dev
```

### 3. Access Live Applications
- **Engineering Console:** [http://localhost:3000](http://localhost:3000)
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Synthetic ERP Finance Portal:** [http://localhost:8000/sandbox/finance](http://localhost:8000/sandbox/finance)

---

## 🧪 Automated Test Suite

Run the complete 29-test test suite covering unit, integration, and Playwright browser E2E tests:

```bash
# Run full test suite
pytest tests/ -v

# Run Playwright end-to-end browser feature suite
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

## 📁 Repository Directory Structure

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

## 📄 License & Attribution

Distributed under the MIT License. Built with modern enterprise AI engineering standards.
