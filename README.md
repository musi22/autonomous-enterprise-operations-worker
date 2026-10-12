# Autonomous Enterprise Operations Worker

> **An AI employee that converts natural-language business objectives into verified actions across enterprise tools.**

[![Build Status](https://img.shields.io/badge/Release%20Gate-PASSED-emerald?style=for-the-badge)](results/ENTERPRISE_EVAL_SCORECARD.md)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue?style=for-the-badge&logo=python)](apps/api)
[![LangGraph](https://img.shields.io/badge/LangGraph-11--Node%20State%20Machine-cyan?style=for-the-badge)](packages/agent/enterprise_worker.py)
[![Playwright](https://img.shields.io/badge/Playwright-Browser%20Automation-orange?style=for-the-badge)](packages/sandbox_tools/enterprise/browser_tools.py)
[![Next.js](https://img.shields.io/badge/Next.js-14%20Console-black?style=for-the-badge&logo=next.js)](apps/web)
[![Evaluations](https://img.shields.io/badge/Evaluations-10%2F10%20(100%25)-success?style=for-the-badge)](results/enterprise_eval_results.json)

---

## 📌 Executive Summary

Traditional LLM agent demonstrations are chatbots: they output conversational text, make optimistic API calls without verification, and fail silently when network hiccups or schema mismatches occur.

The **Autonomous Enterprise Operations Worker** is built as a genuine **digital back-office employee**. Given a high-level natural language prompt, the worker autonomously plans and decomposes the objective, discovers files, extracts and validates structured entities, enforces deterministic policy guardrails, requests human supervisor approvals when thresholds are crossed, interacts via APIs or browser automation, recovers self-healingly from transient failures, and **independently verifies state persistence in the target enterprise ledger** before producing cryptographic evidence of completion.

```
USER GOAL
   ↓
INTENT / GOAL UNDERSTANDING
   ↓
DYNAMIC PLANNING
   ↓
CONTEXT / WORKING MEMORY
   ↓
SELECT TOOL & PARAMS
   ↓
DETERMINISTIC POLICY CHECK ──[Requires Approval]──> HUMAN SUPERVISOR APPROVAL
   ↓ (Allowed)                                                │ (Approved)
EXECUTE TOOL (API / Browser) <────────────────────────────────┘
   ↓
OBSERVE & VALIDATE RESULT
   ↓
FAILURE DETECTED? ──[Yes]──> CLASSIFY & BOUNDED RETRY / REPLAN
   ↓ (No)
MORE PLAN STEPS? ───[Yes]──> SELECT NEXT TOOL
   ↓ (No)
INDEPENDENT LEDGER RECONCILIATION (PASS / FAIL)
   ↓
CRYPTOGRAPHIC SHA-256 EVIDENCE LEDGER
   ↓
FINAL AUDITED SUMMARY
```

---

## 🎯 Primary Demo Workflows

### 1. Primary Workflow: Autonomous Invoice Processing & Verification
> **Prompt:** *"Find the latest unpaid invoice from Acme, extract the invoice number, amount and due date, enter it into our finance system, verify that it was saved correctly, and tell me when it is done."*

**Autonomous Execution Trace:**
1. **Goal Understanding:** Extracts target vendor `Acme`, action `finance_create_invoice`, and verification requirement.
2. **Plan Generation:** Synthesizes 5 sub-steps: locate invoices, extract fields, pre-check ERP, enter finance record, verify finance ledger.
3. **Invoice Discovery:** Calls `search_company_files("Acme")` and identifies `INV-2026-1042`.
4. **Field Extraction & Validation:** Reads document and normalizes fields:
   * **Vendor:** Acme Corp
   * **Invoice ID:** `INV-2026-1042`
   * **Amount:** ₹84,500
   * **Due Date:** `2026-10-18`
   * **Currency:** INR
5. **Duplicate Pre-check:** Queries finance system; confirms no existing record.
6. **Policy Check:** Confirms ₹84,500 is within standard auto-approval limits (< ₹100,000).
7. **ERP Execution:** Idempotently submits record with key `TASK-...-INV-2026-1042-CREATE`.
8. **Independent Reconciliation:** Issues an independent read query to the ERP database; asserts 6 fields match.
9. **Final Summary:**
```text
Task completed successfully.
Invoice: INV-2026-1042
Vendor: Acme
Amount: ₹84,500
Due date: 18 October 2026
Finance record: FIN-82914
Verification: PASSED
Evidence: SHA-256 Hashchain verified against ERP ledger
```

---

### 2. Second Workflow: Human-in-the-Loop Governance (> ₹100,000)
> **Prompt:** *"Process the latest Contoso invoice, but do not enter invoices above ₹100,000 without my approval."*

* **Invoice Identified:** `CONT-8893` from Contoso for **₹150,000**.
* **Autonomous Behavior:**
  1. Locates and extracts invoice data into working memory.
  2. Policy engine flags amount exceeds threshold (₹150,000 > ₹100,000).
  3. Pauses execution and creates pending approval record.
  4. Real-time approval modal appears in the Next.js UI.
  5. Operator clicks **Approve**.
  6. Worker seamlessly resumes, records finance entry `FIN-94182`, independently verifies ERP state, and emits evidence.

---

### 3. Third Workflow: Deterministic Fault Recovery (HTTP 500)
> **Fault Simulation:** Finance ERP returns `HTTP 500 Internal Server Error` on initial submission.

* **Autonomous Behavior:**
  1. Execution detects error and passes it to the **Error Taxonomy Classifier**.
  2. Classified as `TRANSIENT_500`.
  3. Triggers bounded exponential backoff (`Retry 1/3`).
  4. Re-executes tool using identical idempotency key.
  5. Second attempt succeeds; ledger creates record `FIN-82914`.
  6. Idempotency guarantees zero duplicate records.
  7. Verification confirms record integrity.

---

## 🏗️ Architecture & Component Reuse Matrix

To respect engineering best practices, this project evolved the existing repository without starting from scratch.

| Component | Status | Description |
| :--- | :--- | :--- |
| **LangGraph Engine** | **EXTENDED** | Evolved from 9-node retail graph to an 11-node `EnterpriseOperationsWorker` with planning, approval pause/resume, error classification, and independent verification. |
| **Enterprise Sandbox** | **NEW** | Added synthetic ERP database (`finance_records`), invoice repository, and interactive web application (`/sandbox/finance`). |
| **Tool Registry** | **NEW** | Built typed enterprise tools: `search_company_files`, `extract_invoice_fields`, `finance_create_invoice`, and Playwright browser actions. |
| **Browser Automation** | **NEW** | Integrated Playwright (`browser_navigate`, `browser_type`, `browser_click`, `browser_read`) for DOM interaction. |
| **Policy Engine** | **REUSED & EXTENDED** | Reused `PolicyEngine` architecture; added `HighValueInvoiceApprovalRule` (> ₹100k) and `IdempotencyKeyPresenceRule`. |
| **Human-in-the-Loop** | **REUSED & EXTENDED** | Reused approval schema and database tables; wired directly into LangGraph state machine pause/resume lifecycle. |
| **Verification Engine**| **NEW** | Created `EnterpriseVerificationEngine` performing 6-point independent post-write reconciliation against ERP tables. |
| **Evidence Ledger** | **REUSED & EXTENDED** | Reused SHA-256 hashchain ledger; generates cryptographic proofs linking invoice source, tool inputs, and verification proofs. |
| **Next.js Web Console**| **EXTENDED** | Added `AutonomousWorkerTab` with goal input, preset chips, dynamic plan checklist, working memory cards, live reconciliation table, and approval modal. |
| **Evaluation Suite** | **NEW** | Created 10 deterministic YAML evaluation scenarios (`scenarios/enterprise/`) and benchmark runner. |

---

## 🛠️ Tool Registry & Browser Automation

Every tool implements strict argument types, risk classifications, and structured telemetry:

```python
class ToolMetadata(BaseModel):
    name: str
    description: str
    risk_level: RiskLevel  # LOW, MEDIUM, HIGH, CRITICAL
    is_write: bool         # Mutating vs Read-Only
```

### Registered Tools
1. `search_company_files(query, vendor)`: Searches synthetic document store.
2. `list_invoices(vendor, status)`: Lists matching synthetic invoices.
3. `read_invoice(invoice_id)`: Retrieves full invoice text.
4. `extract_invoice_fields(invoice_id, raw_content)`: Normalizes invoice fields into structured JSON.
5. `search_vendor(vendor_name)`: Looks up vendor payment profile.
6. `finance_find_invoice(invoice_id)`: Queries ERP database for existing records.
7. `finance_create_invoice(invoice_id, vendor, amount, due_date, currency, idempotency_key)`: Submits ERP record with idempotency deduplication.
8. `finance_get_invoice(finance_record_id)`: Fetches verified ERP record by reference ID.
9. `browser_navigate(url)`: Directs Playwright browser to finance web portal.
10. `browser_type(selector, text)`: Simulates keyboard input into form fields.
11. `browser_click(selector)`: Clicks DOM buttons and triggers form submissions.
12. `browser_read(selector)`: Extracts rendered DOM table content.
13. `request_human_approval(task_id, reason, details)`: Suspends execution for human sign-off.

---

## 📊 Evaluation Suite & Benchmark Results

The evaluation harness evaluates 10 comprehensive scenarios across 8 quantitative metrics:

| Scenario ID | Name | Focus | Result | Duplicate Writes |
| :--- | :--- | :--- | :---: | :---: |
| `01` | `successful_invoice_processing` | Happy-path Acme processing | **PASS** | 0.0% |
| `02` | `invoice_requires_approval` | Contoso ₹150k approval gate | **PASS** | 0.0% |
| `03` | `transient_finance_failure_then_success`| HTTP 500 retry & recovery | **PASS** | 0.0% |
| `04` | `duplicate_invoice` | Idempotent duplicate conflict handling | **PASS** | 0.0% |
| `05` | `invoice_not_found` | Missing invoice handling | **PASS** | 0.0% |
| `06` | `invalid_invoice_data` | Malformed date/amount validation | **PASS** | 0.0% |
| `07` | `approval_rejected` | Human supervisor rejection flow | **PASS** | 0.0% |
| `08` | `verification_failure` | State mismatch detection | **PASS** | 0.0% |
| `09` | `tool_timeout` | Timeout backoff recovery | **PASS** | 0.0% |
| `10` | `alternative_vendor` | Generalization across vendors (Globex) | **PASS** | 0.0% |

**Summary Metrics:**
* **Overall Scenario Pass Rate:** `100.0%` (10/10)
* **Duplicate Write Rate:** `0.0%`
* **Policy Compliance:** `100.0%`
* **Independent Verification Accuracy:** `100.0%`

*Detailed outputs available in:*
* [`results/ENTERPRISE_EVAL_SCORECARD.md`](results/ENTERPRISE_EVAL_SCORECARD.md)
* [`results/enterprise_eval_results.json`](results/enterprise_eval_results.json)
* [`results/enterprise_eval_results.csv`](results/enterprise_eval_results.csv)

---

## 🚀 Local Setup & Quickstart

### Prerequisites
* Python 3.11+
* Node.js 18+ & npm
* SQLite3

### 1. Backend Setup
```bash
# From workspace root
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install playwright
playwright install chromium

# Seed synthetic enterprise database
python -c "from apps.api.app.db.init_db import init_db; from apps.api.app.db.seed_data import seed_enterprise_data; import asyncio; asyncio.run(init_db()); asyncio.run(seed_enterprise_data())"

# Start FastAPI backend (port 8000)
uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup
```bash
# Navigate to web app
cd apps/web

# Install dependencies
npm install

# Start Next.js development server (port 3000)
npm run dev
```

Open your browser to: **`http://localhost:3000/`** (Defaults to the **Autonomous AI Employee** view).

### 3. Finance Sandbox Web Portal
The simulated internal finance portal is accessible at:
* **Interactive Sandbox UI:** `http://localhost:8000/sandbox/finance`
* **Swagger API Documentation:** `http://localhost:8000/docs`

---

## 🧪 Running Tests & Evaluations

```bash
# Run unit tests
python -m pytest tests/unit/test_enterprise_worker.py -v

# Run integration tests
python -m pytest tests/integration/test_autonomous_worker_api.py -v

# Run the 10-scenario evaluation suite
python -m packages.evaluators.enterprise_evaluator
```

---

## 🐳 Docker Deployment Setup

Run the entire platform with Docker Compose:

```bash
docker compose up --build
```
* **Frontend:** `http://localhost:3000`
* **API & Sandbox:** `http://localhost:8000`

---

## 📚 Technical Documentation Index

* [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): Detailed 11-node LangGraph specification, state schema, and lifecycle flow.
* [`docs/DESIGN_DECISIONS.md`](docs/DESIGN_DECISIONS.md): Architectural decisions and rationale (LangGraph, Playwright, idempotency, decoupled verification).
* [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md): Scope boundaries, assumptions, and production evolution paths.
* [`docs/PRODUCTION_ROADMAP.md`](docs/PRODUCTION_ROADMAP.md): Temporal durable workflows, containerized browser pods, MCP integration, and RBAC.
* [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md): 3.5-minute video demonstration script and timing outline.
* [`results/ENTERPRISE_EVAL_SCORECARD.md`](results/ENTERPRISE_EVAL_SCORECARD.md): Quantitative benchmark results across all 10 scenarios.
