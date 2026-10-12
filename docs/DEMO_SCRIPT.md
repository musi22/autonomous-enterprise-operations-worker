# Video Demonstration Script & Presentation Plan

**Target Duration:** 3:30 – 4:00 Minutes  
**System:** Autonomous Enterprise Operations Worker  
**Presenting Engineer:** Senior AI Engineering Intern Candidate  

---

### Phase 1: Problem Definition & Operational Reality (0:00 – 0:20)
* **Visual:** Slide or Console header showing the Autonomous Enterprise Operations Worker.
* **Narration:**
  > *"Most enterprise agent demos today are chatbots that stop at generating text or hallucinating tool outputs without verification. In a real corporate back-office, an AI employee must autonomously convert natural-language business goals into verified actions across internal systems, enforce strict risk boundaries, self-heal through network errors, and independently verify that records actually landed in the database before declaring success. Here is our Autonomous Enterprise Operations Worker."*

---

### Phase 2: System Architecture Overview (0:20 – 0:45)
* **Visual:** Architecture diagram from [`docs/ARCHITECTURE.md`](file:///c:/Users/RASHMI/Desktop/ai/docs/ARCHITECTURE.md) showing LangGraph 11-node state machine.
* **Narration:**
  > *"The system is built on LangGraph with an 11-node state graph. It separates LLM reasoning from code-enforced policy gates. Notice four key innovations: first, task-scoped working memory that avoids redundant reads; second, strict idempotency keys preventing duplicate financial records; third, an error classification taxonomy with bounded retries; and fourth, an independent post-write verification engine that queries the target ledger directly rather than trusting HTTP 200 responses."*

---

### Phase 3: Primary Demo — Autonomous Invoice Processing (0:45 – 1:40)
* **Visual:** Browser opened to `http://localhost:3000/`. Operator clicks Preset 1 or types:
  `"Find the latest unpaid invoice from Acme, extract the invoice number, amount and due date, enter it into our finance system, verify that it was saved correctly, and tell me when it is done."`
  Clicks **Run Task**.
* **Action:**
  1. UI shifts to `RUNNING`.
  2. Plan steps highlight sequentially:
     - ✓ Locate Acme invoices
     - ✓ Extract & validate details (`INV-2026-1042`, ₹84,500, Due 2026-10-18)
     - ✓ Check existing records (None found)
     - ✓ Submit to finance ERP
     - ✓ Verify finance ledger
  3. Working Memory Card populates in real time.
  4. Final Reconciliation Table displays:
     - Target ERP Record: `FIN-82914`
     - Status: `RECORDED`
     - Verification: `PASSED`
* **Narration:**
  > *"We enter our business goal. The worker analyzes the objective, generates an execution plan, locates invoice INV-2026-1042 for Acme Corp, extracts ₹84,500, checks the internal ERP for duplicates, enters the record, and then independently queries the ledger to confirm record FIN-82914 exists with identical fields. Task completed with verified evidence."*

---

### Phase 4: Second Demo — Failure Recovery & Idempotent Retry (1:40 – 2:20)
* **Visual:** Run scenario with transient fault injection:
  `"Process invoice INV-2026-1042 from Acme with transient finance fault simulation."`
* **Action:**
  1. The finance submission fails on attempt 1 with `HTTP 500 Internal Server Error`.
  2. The UI event trace highlights:
     - `✗ Finance submission failed: HTTP 500 (TRANSIENT)`
     - `↻ Retry 1/3 (Exponential backoff 1.0s)`
     - `✓ Retry succeeded! Finance record FIN-82914 created`
  3. Show that no duplicate records were created due to the idempotency key `TASK-...-CREATE`.
* **Narration:**
  > *"Next, we test reliability under failure. The target finance system injects an HTTP 500 fault. Rather than crashing or silently failing, the worker classifies the error as TRANSIENT, calculates backoff, and executes an idempotent retry. The write succeeds on retry without duplicate records, and completes verified reconciliation."*

---

### Phase 5: Third Demo — Human-in-the-Loop Policy Gate (2:20 – 2:55)
* **Visual:** Operator enters:
  `"Process the latest Contoso invoice, but do not enter invoices above ₹100,000 without my approval."`
* **Action:**
  1. Worker plans and reads Contoso invoice `CONT-8893` (₹150,000).
  2. Deterministic policy engine flags amount > ₹100,000.
  3. Execution pauses with status: `WAITING_FOR_APPROVAL`.
  4. Human Approval modal pops up in UI showing:
     - Vendor: Contoso
     - Invoice: CONT-8893
     - Amount: ₹150,000
     - Threshold: ₹100,000
  5. Operator clicks **Approve Invoice Entry**.
  6. Worker resumes, writes to finance, and completes verification.
* **Narration:**
  > *"Now we test governance. Contoso has an invoice for ₹150,000, exceeding our ₹100,000 policy threshold. The deterministic policy engine intercepts the tool call before execution, halts the agent, and presents an approval card. Once approved by the human operator, the workflow resumes seamlessly, records FIN-94182, and verifies the write."*

---

### Phase 6: Independent Verification & Audit Ledger (2:55 – 3:20)
* **Visual:** Click on the **Evidence Ledger** and **Audit Details** drawer in the UI.
* **Narration:**
  > *"Every single step, policy evaluation, approval decision, and verification check produces an immutable audit record with SHA-256 integrity hashing. The verification engine independently queried the database post-write, validating that all 6 fields match the source invoice."*

---

### Phase 7: Evaluation Suite & Benchmark Results (3:20 – 3:40)
* **Visual:** Show evaluation scorecard from [`results/ENTERPRISE_EVAL_SCORECARD.md`](file:///c:/Users/RASHMI/Desktop/ai/results/ENTERPRISE_EVAL_SCORECARD.md).
* **Narration:**
  > *"To ensure this wasn't an isolated happy-path demo, we built a comprehensive evaluation harness covering 10 distinct failure and edge-case scenarios: transient faults, duplicate detection, missing invoices, malformed data, rejected approvals, and alternative vendors. All 10 scenarios passed with zero duplicate writes and 100% policy compliance."*

---

### Phase 8: Limitations & Production Roadmap (3:40 – 4:00)
* **Visual:** Conclusion slide referencing [`docs/LIMITATIONS.md`](file:///c:/Users/RASHMI/Desktop/ai/docs/LIMITATIONS.md) and [`docs/PRODUCTION_ROADMAP.md`](file:///c:/Users/RASHMI/Desktop/ai/docs/PRODUCTION_ROADMAP.md).
* **Narration:**
  > *"This prototype is scoped to synthetic enterprise environments without live banking connections. Our production roadmap outlines migration to Temporal for durable execution, containerized browser pods, and Model Context Protocol integration. Thank you!"*
