# Design Decisions: Autonomous Enterprise Operations Worker

This document records the architectural and engineering rationale behind the core design choices in the Autonomous Enterprise Operations Worker.

---

## 1. Why LangGraph for Agentic Orchestration?
* **Alternative Considered:** Simple ReAct loops (`while True: think -> act -> observe`), raw LangChain chains, or hardcoded state machines.
* **Decision:** Built on **LangGraph**.
* **Rationale:**
  1. **State Explainability & Introspection:** ReAct loops obscure intermediate decisions inside conversational message lists. LangGraph's explicit `EnterpriseWorkerState` exposes every step, entity, policy check, and retry count directly in typed dictionaries.
  2. **First-Class Human-in-the-Loop Pausing:** LangGraph allows pausing execution indefinitely at approval nodes (`request_approval`) and resuming with external payloads when the operator approves or rejects.
  3. **Conditional Branching for Recovery:** Directed graphs allow clean separation between the happy path and recovery pathways (`recover_or_replan`), eliminating messy conditional spaghetti code.

---

## 2. Why Deterministic Authorization Over LLM Self-Policing?
* **Alternative Considered:** Prompting the LLM: *"Please do not submit invoices over ₹100,000 without asking the user."*
* **Decision:** Strict, code-level policy enforcement in `packages/policies/rules.py` intercepting every tool call prior to dispatch.
* **Rationale:**
  1. **Prompt Injection & Hallucination Resistance:** LLMs are susceptible to goal hijacking, sycophancy, and parameter misinterpretation. Code-level rules guarantee that policy compliance is mathematical and absolute.
  2. **Audit & Regulatory Compliance:** Enterprise regulators require demonstrable, auditable proof that spending caps and dual-control rules cannot be circumvented under any prompt phrasing.

---

## 3. Why Playwright for Browser / Computer Use?
* **Alternative Considered:** Selenium, Puppeteer, raw HTTP scraping, or OS-level coordinate clicking (VNC/pyautogui).
* **Decision:** **Playwright** browser automation against a simulated internal web application (`/sandbox/finance`).
* **Rationale:**
  1. **True Enterprise Reality:** Many legacy enterprise ERPs, SAP screens, and billing portals lack programmatic REST APIs. Providing real browser automation proves the agent can act as an actual digital employee.
  2. **Semantic DOM Interaction:** Playwright provides robust selector support (`input[name="invoice_id"]`), eliminating the fragility of coordinate-based vision models that break on window resizing or font rendering shifts.
  3. **Visual Transparency:** The operator can visibly watch form fields fill and submit buttons click during live operations.

---

## 4. Why Decouple Independent Verification from Tool Execution?
* **Alternative Considered:** Trusting `response.status_code == 200` or `{ "success": true }` returned by the write tool.
* **Decision:** Dedicated `verify_outcome` node that independently queries the target database/ledger and asserts field equality across 6 dimensions.
* **Rationale:**
  1. **Silent Failure & Partial Writes:** In distributed enterprise architectures, an API might return HTTP 200 after queuing a message, but the background consumer might drop the write, truncate fields, or write with corrupted currency symbols.
  2. **High-Stakes Accountability:** An autonomous worker cannot claim success based on intent or unverified tool outputs. True operational autonomy requires post-write verification against the system of record.

---

## 5. Why Strict Idempotency Keys?
* **Alternative Considered:** Allowing raw database inserts on every write tool execution.
* **Decision:** Synthetic idempotency keys composed of `task_id + invoice_id + action` enforced at both the tool layer and ERP database schema.
* **Rationale:**
  1. **Network Partition Resiliency:** If a transient network failure or timeout occurs *after* the ERP commits a record but *before* the HTTP response reaches the agent, a naive retry would cause a double payment or duplicate invoice record.
  2. **Safe Retries:** With idempotency keys, the retry automatically retrieves the already-created record, preventing duplicate writes and turning a potential catastrophe into a smooth recovery.

---

## 6. Why Bounded Retries with Exponential Backoff?
* **Alternative Considered:** Infinite retry loops or immediate failure on the first transient error.
* **Decision:** Bounded retries (default max: 3) with exponential backoff and error classification (`TRANSIENT` vs `UNRECOVERABLE`).
* **Rationale:**
  1. **Infinite Loop Prevention:** Unbounded retry loops waste compute tokens, risk API rate exhaustion, and can hammer struggling backend services.
  2. **Self-Healing Grace:** Temporary 500 errors or rate spikes recover within 1-2 retries, allowing the worker to finish autonomously without human escalation.

---

## 7. Why Simulated Enterprise Sandboxes Over Real Systems?
* **Alternative Considered:** Connecting to real live QuickBooks, Stripe, or corporate accounting APIs.
* **Decision:** Fully contained synthetic sandbox with mock documents, simulated database tables, and deliberate fault injection modes (`error_mode="transient_500"`).
* **Rationale:**
  1. **Safety & Zero Liability:** Prevents accidental financial transactions, data leakage, or credential exposure during testing and intern evaluation.
  2. **Deterministic Reproducibility:** Every evaluator can spin up the environment from scratch, test transient 500 errors, duplicate conflicts, and high-value approvals without relying on external SaaS rate limits or paid accounts.

---

## 8. Why Task-Scoped Working Memory?
* **Alternative Considered:** Re-reading the invoice document from disk before every downstream tool call, or dumping the entire raw JSON text into every LLM prompt.
* **Decision:** Structured `memory` dictionary stored in state (`vendor`, `invoice_id`, `amount`, `due_date`, `finance_record_id`).
* **Rationale:**
  1. **Context Window Efficiency:** Eliminates repetitive reading of multi-kilobyte documents, reducing token consumption and latency.
  2. **Data Consistency:** Guarantees that the exact vendor and amount extracted during step 1 are passed identically to policy checks, finance creation, and post-write verification.
