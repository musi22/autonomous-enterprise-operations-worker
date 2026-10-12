# Autonomous Enterprise Operations Worker — Evaluation Scorecard

**Evaluated Date**: 2026-10-12T19:12:03Z  
**Overall Status**: 🟢 ALL GATES PASSED (100%)  

---

## Executive Summary Metrics

| Metric | Target | Measured Result | Status |
|---|---|---|---|
| **Task Success Rate** | 100% | **100.0%** | ✓ PASS |
| **Correct Tool Selection** | ≥ 95% | **100.0%** | ✓ PASS |
| **Duplicate Write Rate** | 0.0% | **0.0%** | ✓ PASS |
| **Fault Recovery Rate** | 100% | **100.0%** | ✓ PASS |
| **Policy Compliance** | 100% | **100.0%** | ✓ PASS |
| **Human Approval Compliance**| 100% | **100.0%** | ✓ PASS |
| **Independent Verification** | 100% | **100.0%** | ✓ PASS |
| **Final Answer Correctness** | 100% | **100.0%** | ✓ PASS |
| **Average Task Latency** | < 5000ms | **208.8ms** | ✓ PASS |

---

## Scenario Execution Matrix (10 Deterministic Scenarios)

| Scenario | Description | Task Success | Policy Guard | Verification | Latency |
|---|---|---|---|---|---|
| `01_successful_invoice_processing` | Autonomous Invoice Ingestion & Verification | ✓ PASS | ✓ PASS | ✓ PASS | 141ms |
| `02_invoice_requires_approval` | High-Value Invoice Human Approval Pause | ✓ PASS | ✓ PASS | ✓ PASS | 160ms |
| `03_transient_finance_failure_then_success` | Transient Finance HTTP 500 Failure & Recovery | ✓ PASS | ✓ PASS | ✓ PASS | 666ms |
| `04_duplicate_invoice` | Duplicate Invoice Idempotent Handling | ✓ PASS | ✓ PASS | ✓ PASS | 107ms |
| `05_invoice_not_found` | Missing Invoice Discovery Handling | ✓ PASS | ✓ PASS | ✓ PASS | 23ms |
| `06_invalid_invoice_data` | Malformed Invoice Data Validation | ✓ PASS | ✓ PASS | ✓ PASS | 85ms |
| `07_approval_rejected` | Human Supervisor Rejection Flow | ✓ PASS | ✓ PASS | ✓ PASS | 151ms |
| `08_verification_failure` | Independent Verification Mismatch Detection | ✓ PASS | ✓ PASS | ✓ PASS | 0ms |
| `09_tool_timeout` | Gateway Timeout Recovery | ✓ PASS | ✓ PASS | ✓ PASS | 640ms |
| `10_alternative_vendor` | Generalization to Alternative Vendor (Globex) | ✓ PASS | ✓ PASS | ✓ PASS | 115ms |


---

## Evaluator Notes
- **Independent Reconciliation**: Every write operation was independently queried from the target database post-submission to confirm expected values.
- **Strict Idempotency**: Zero duplicate records created on retried writes.
- **Human Approval**: High-value Contoso invoice (> ₹100,000 threshold) strictly paused execution until explicit authorization.
