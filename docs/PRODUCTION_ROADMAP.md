# Production Roadmap: Scaling to Enterprise Fleet Operations

This document details the engineering roadmap for taking the Autonomous Enterprise Operations Worker prototype into a resilient, production-grade enterprise platform.

---

## 1. Durable Workflow Execution & Distributed Workers
* **Temporal / Celery Integration:** Migrate state transitions to a durable execution engine like **Temporal** or **Cadence**. If a worker crashes mid-task, the workflow resumes deterministically from the last committed checkpoint rather than restarting from step zero.
* **Worker Fleet Scaling:** Decouple workers from the web tier using asynchronous message queues (RabbitMQ, Kafka, AWS SQS) enabling auto-scaling of worker pods based on queue backlog.

---

## 2. Browser Sandboxing & Container Isolation
* **Remote Browser Pods:** Run Playwright inside dedicated, short-lived Kubernetes browser pods (e.g., using Browserless or Dockerized Chromium).
* **Network & Memory Egress Isolation:** Each browser pod operates in an isolated VPC with strict egress firewall rules, preventing lateral movement into corporate internal networks.
* **Ephemeral Sessions:** Browser containers are terminated and destroyed after task completion to guarantee zero cross-tenant session leakage or credential persistence.

---

## 3. Multi-Tenant Isolation & Role-Based Access Control (RBAC)
* **Tenant Isolation:** Enforce row-level security (RLS) in PostgreSQL schemas, ensuring that tasks, invoice documents, and audit logs are strictly partitioned by organization ID.
* **Granular Tool Permissions:** Define per-role tool policies (e.g., *Junior Accountant* can execute `finance_find_invoice`, but only *Finance Director* can execute `finance_create_invoice` > ₹1,000,000).

---

## 4. Secret Management & Credential Injection
* **Vault / AWS Secrets Manager:** Dynamically inject short-lived enterprise service tokens at the moment of tool execution, eliminating plain-text credentials in state dictionaries or environment variables.
* **Just-In-Time (JIT) Privileges:** Issue temporary tokens valid for the duration of a single task run and automatically revoked upon completion.

---

## 5. Model Context Protocol (MCP) & Extensibility
* **Dynamic MCP Servers:** Implement standardized Model Context Protocol (MCP) clients, allowing enterprise departments to expose legacy SQL databases, Jira instances, and SAP interfaces as standardized MCP tools without modifying the core agent codebase.
* **Automated Security Sandboxing:** Automatically scan incoming MCP tool definitions for destructive actions before admitting them into the worker's tool registry.

---

## 6. Cost Controls, Rate Limiting & LLM Fallback
* **Token Budgeting:** Assign max token limits and dollar caps per task execution.
* **Multi-Model Routing:** Route simple extraction tasks to smaller, cost-effective models (e.g., Gemini Flash or Claude 3.5 Haiku) and escalate complex planning or recovery decisions to frontier models (Gemini 1.5 Pro or Claude 3.5 Sonnet).
* **Local Fallback:** Support on-premise open weights models (vLLM / Ollama with Llama 3.3 70B) for regulated healthcare and banking environments with zero external data egress.

---

## 7. Continuous Evaluation & Shadow Pipelines
* **Automated Regression CI/CD:** Run the 10 enterprise evaluation scenarios (`scenarios/enterprise/`) on every pull request.
* **Shadow Execution in Production:** Run autonomous worker tasks in shadow mode alongside human operators, comparing the agent's extracted data and proposed ERP writes against real human actions to calculate ground-truth alignment before granting write autonomy.
