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

---

## 🎥 End-to-End Platform Walkthrough Video

![Platform Demo Walkthrough](docs/screenshots/platform_demo_walkthrough.webp)

*Interactive tour demonstrating autonomous planning, execution, HITL approval gates, and cryptographic tamper verification.*

---

## 📸 Feature-by-Feature Visual Tour & Screenshots

### 1. Autonomous Operations Worker Execution
> *Autonomously synthesizes an 8-step execution plan, normalizes multi-currency fields, and reconciles state out-of-band against the target ERP.*

![Autonomous Worker Execution](docs/screenshots/02_autonomous_worker_execution.png)

- **Dynamic Task Plan:** Steps tick off sequentially (`COMPLETED`) with microsecond execution latency tracking.
- **Task-Scoped Working Memory:** Live display of discovered vendor, invoice ID, payable amount, and idempotency key.
- **Independent Final-State Reconciliation:** Explicit assertion table comparing expected vs. actual database values (`VERIFICATION: PASSED`).

---

### 2. Overview Dashboard & Enterprise Release Gate
> *Aggregates real-time operational safety KPIs and release criteria checklists.*

![Overview Dashboard](docs/screenshots/01_overview_dashboard.png)

- **KPI Metrics:** 100% Task Success, 0.0% Unauthorized Actions, 100% Fault Recovery, 100% Evidence Completeness.
- **Release Gate Evaluation Checklist:** 5 deterministic criteria gating deployment to production.
- **Observed Failure Taxonomy:** Live categorization of security, schema, and network exceptions.

---

### 3. Scenario Lab & Deterministic Policy Enforcement
> *Demonstrates how Guarded Mode intercepts adversarial cross-customer access and prompt injection attacks.*

![Scenario Lab Policy Enforcement](docs/screenshots/03_scenario_lab_policy.png)

- **Policy Interception:** Blocks unauthorized orders (`06_cross_customer_access`) with `REJECTED_POLICY`.
- **Zero Hallucination:** Emits a deterministic policy violation audit receipt rather than executing dangerous actions.

---

### 4. Trace Explorer (9-Node LangGraph Timeline)
> *Full white-box observability into internal agent state transitions.*

![Trace Explorer Timeline](docs/screenshots/04_trace_explorer_timeline.png)

- **9-Node Graph:** `classify_intent` → `create_plan` → `authorize_plan` → `check_preconditions` → `execute_action` → `verify_effects` → `handle_fault_or_retry` → `reconcile_state` → `emit_evidence_receipt`.
- **State Inspection:** Inspect exact input/output payloads at any step in the lifecycle.

---

### 5. Human-in-the-Loop Approval Queue (HITL Governance)
> *Centralized operational governance for actions exceeding financial thresholds.*

![Approval Inbox](docs/screenshots/05_approval_inbox.png)

- **Threshold Alerts:** Pauses high-value transactions (> ₹100,000) before mutating internal ledgers.
- **Supervisor Actions:** Operations leads can review proposed vendor and amount before approving or rejecting.

---

### 6. Dual-Agent Comparative Benchmarks
> *Head-to-head empirical evaluation across 20 enterprise scenarios.*

![Benchmark Comparison](docs/screenshots/06_benchmark_comparison.png)

- **Guarded Worker:** 100% task success rate, 0% unauthorized actions.
- **Baseline Worker:** 60% success rate, 40% unauthorized actions (frequently violates tenant isolation).
- **Export Actions:** Download full benchmark datasets via CSV or raw JSON.

---

### 7. Tamper-Evident Cryptographic Evidence Ledger
> *Sequential SHA-256 hashchain ensuring non-repudiation and immediate corruption detection.*

![Evidence Ledger Tamper Detection](docs/screenshots/07_evidence_ledger_tamper.png)

- **Integrity Verification:** Traverses previous block hashes to confirm 100% unaltered audit logs.
- **Tamper Simulation:** Click *Simulate DB Tampering* to witness the system pinpoint the exact corrupted block index in real time.

---

### 8. Synthetic ERP Finance Portal
> *Internal ERP sandbox mimicking SAP / NetSuite operational environments.*

![Synthetic ERP Sandbox](docs/screenshots/08_synthetic_erp_sandbox.png)

- **Direct Portal:** Inspect invoices created by the agent in real time at `http://localhost:8000/sandbox/finance`.
- **Fault Injection Controls:** Built-in triggers for synthetic HTTP 500 crashes and idempotency conflicts.

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
