# Phase 1: Repository Audit & Implementation Plan

## 1. System Objective
Evolve the existing **Enterprise Agent Trust Platform** into an **Autonomous Enterprise Operations Worker**:
An AI employee that accepts a natural-language business objective and autonomously plans, discovers, extracts, validates, executes (via browser and APIs), handles failures/retries, seeks human approval when policy requires, independently verifies outcomes, and produces cryptographic evidence.

---

## 2. Component Audit

### KEEP (Reuse Existing Working Assets)
- **`packages/telemetry/ledger.py`**: Cryptographic SHA-256 hash chaining, Merkle/linear verification, tamper detection, HMAC digital signatures, and secret redaction.
- **`packages/fault_injection/proxy.py`**: Fault injection proxy capable of intercepting tool invocations to deterministically trigger HTTP 500, timeouts, connection drops, and transient failures.
- **`packages/agent/providers/`**: Multi-provider abstraction (`BaseModelProvider`, `DeterministicMockProvider`, `GeminiProvider`) providing offline zero-cost deterministic mock runs or live LLM execution.
- **`apps/api/app/db/`**: SQLite / Postgres async database layer with SQLAlchemy models (`AgentRun`, `AgentEvent`, `ToolCall`, `PolicyDecision`, `Approval`, `EvidenceReceipt`).
- **`apps/api/app/api/v1/routers/`**: Health checks, approvals, policies, evidence verification, and admin reset routes.
- **`apps/web/`**: Next.js 14 console with Tailwind CSS, dark aesthetic, and trace/approval/evidence inspection tabs.
- **Testing & Tooling**: Pytest, AsyncIO fixtures, Playwright e2e test harness.

### MODIFY (Extend & Modernize)
- **`packages/agent/guarded_graph.py`**:
  - Upgrade state from retail customer support to **Autonomous Task Worker State**:
    - `task_id`, `user_goal`, `interpreted_goal`, `plan`, `current_step`, `completed_steps`, `available_tools`, `selected_tool`, `tool_arguments`, `observations`, `memory`, `extracted_entities`, `risk_level`, `approval_required`, `approval_status`, `retry_count`, `errors`, `verification_requirements`, `verification_results`, `evidence`, `status`, `final_result`.
  - Add explicit graph nodes:
    `interpret_goal` → `create_plan` → `context_memory_lookup` → `select_tool` → `evaluate_policy` → `request_approval` → `execute_tool` → `observe_and_validate` → `recover_or_replan` → `independent_verification` → `emit_evidence` → `complete_task`.
  - Implement full error classification taxonomy (`TRANSIENT`, `VALIDATION_ERROR`, `AUTHORIZATION_ERROR`, `NOT_FOUND`, `TOOL_ERROR`, `BROWSER_ERROR`, `CONFLICT`, `DUPLICATE`, `POLICY_DENIED`, `APPROVAL_REQUIRED`, `UNKNOWN`).
- **`packages/policies/rules.py`**:
  - Add enterprise finance policy rules:
    - High-value finance threshold (invoices > ₹100,000 require human approval).
    - Vendor authorization checks.
    - Idempotency key requirement for state-changing writes.
- **`apps/api/app/db/models.py`**:
  - Add `Invoice`, `FinanceRecord`, `TaskRun`, and sandbox models.
  - Extend run models with goal interpretation, plan JSON, working memory, and independent verification status.
- **`apps/api/app/api/v1/routers/runs.py` & `approvals.py`**:
  - Expose autonomous task execution endpoint `POST /api/v1/tasks/run` accepting arbitrary natural language goals.
  - Support real-time pause and resume on human approval decisions.
- **`apps/web/src/app/page.tsx` & components**:
  - Add a dedicated **AI Employee Operations Console** tab as the default view.
  - Interactive goal input, plan progress bar, step execution timeline, live working memory drawer, independent verification badge, and embedded Sandbox Finance app view.

### REMOVE
- None. Maintain backward compatibility for original benchmark tests while establishing the Autonomous Enterprise Worker as the primary platform capability.

### ADD (New Features)
- **`packages/sandbox_tools/enterprise/`**:
  - Typed tool abstraction and registry:
    - `search_company_files`, `list_invoices`, `read_invoice`, `extract_invoice_fields`, `search_vendor`
    - `finance_find_invoice`, `finance_create_invoice`, `finance_update_invoice`, `finance_get_invoice`
    - `browser_navigate`, `browser_click`, `browser_type`, `browser_read`
    - `request_human_approval`
  - Synthetic enterprise sandbox data (Acme Corp, Contoso, Globex, Initech) with realistic documents and metadata.
- **`packages/browser/`**:
  - Playwright browser execution engine capable of navigating, typing, clicking, and reading sandbox finance web pages.
- **`apps/api/app/api/v1/routers/finance_sandbox.py`**:
  - Internal simulated finance application endpoints (`/sandbox/inbox`, `/sandbox/invoices`, `/sandbox/finance`, `/sandbox/finance/invoices`, `/sandbox/approvals`).
- **Independent Verification Engine**:
  - Reads target finance system directly after execution, cross-checks fields, verifies idempotency, logs audit evidence.
- **Scenarios & Evaluation Suite**:
  - 10 deterministic enterprise scenarios (`01_successful_invoice_processing` to `10_alternative_vendor`).
  - Automated benchmark runner outputting metrics JSON/CSV and markdown scorecard.
- **Documentation**:
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/DESIGN_DECISIONS.md`
  - `docs/LIMITATIONS.md`
  - `docs/PRODUCTION_ROADMAP.md`
  - `docs/DEMO_SCRIPT.md`
