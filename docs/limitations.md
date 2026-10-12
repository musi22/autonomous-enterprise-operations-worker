# System Limitations & Constraints

To ensure engineering rigor, this document outlines the boundary conditions, current limitations, and intentional design scope of the Autonomous Enterprise Operations Worker prototype, alongside the evolutionary path to production.

---

## 1. Current Prototype Limitations

### 1.1 Scope of Enterprise Environment
* **Current State:** The system executes workflows within a synthetic enterprise sandbox consisting of internal document repositories, SQLite ERP databases, and an internal finance web portal (`/sandbox/finance`).
* **Boundary:** It intentionally does not connect to live corporate production systems (SAP, NetSuite, Salesforce) or use live corporate banking credentials.
* **Production Evolution:** Integration via OAuth2/mTLS connectors to enterprise ERPs with strictly scoped service principals, read-only staging replicas, and canary rollout rings.

### 1.2 Browser Automation Boundary
* **Current State:** Playwright automation interacts with DOM elements in the simulated `/sandbox/finance` portal using semantic CSS selectors (`input[name="invoice_id"]`).
* **Boundary:** The worker does not attempt unrestricted general-purpose desktop control (e.g. mouse drag-and-drop across native Windows apps) or bypass CAPTCHA challenges, SMS OTPs, or biometric MFA.
* **Production Evolution:** For legacy systems without DOM access, integrate vision-based computer-use models (such as OSWorld-style coordinate models) operating inside isolated virtual display containers with human escalation for MFA.

### 1.3 Tool Registry & Planner Extensibility
* **Current State:** The planner reasons over a typed, curated registry of enterprise tools (`search_company_files`, `extract_invoice_fields`, `finance_create_invoice`, etc.).
* **Boundary:** Dynamic runtime tool discovery (e.g. dynamically parsing arbitrary OpenAPI 3.0 specs on the fly and creating tools without human review) is not supported.
* **Production Evolution:** Implement the Model Context Protocol (MCP) to allow dynamic server-sent tool discovery with automated static analysis and policy sandboxing before exposing tools to the agent.

### 1.4 Verification Engine
* **Current State:** Verification performs strict, deterministic semantic reconciliation against the SQLite database and ERP ledger across 6 discrete fields (`invoice_id`, `vendor`, `amount`, `currency`, `due_date`, `status`).
* **Boundary:** It relies on predictable database schema representations and does not perform OCR on scanned paper checks or verify physical banking wire acknowledgments.
* **Production Evolution:** Multi-modal reconciliation comparing bank statement PDFs, automated clearing house (ACH) transaction IDs, and ERP balance sheets with LLM-assisted semantic diffing.

---

## 2. Assumptions
1. **Invoice Formatting:** Invoices are provided as structured synthetic JSON files simulating scanned PDF extractions.
2. **Network Reliability:** Network failures within the local sandbox environment are simulated deterministically via `error_mode="transient_500"` to evaluate retry mechanisms without flakiness.
3. **Single Active Workflow:** The prototype tracks tasks sequentially per session, though the database and state schema support concurrent multi-tenant tasks.
