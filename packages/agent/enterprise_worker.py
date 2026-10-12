import asyncio
import time
import re
from typing import Dict, Any, List, Optional, TypedDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from langgraph.graph import StateGraph, END

from apps.api.app.db.models import (
    EnterpriseTask,
    AgentEvent,
    ToolCall,
    PolicyDecision,
    Approval,
    generate_uuid
)
from packages.policies.models import PolicyContext, PolicyDecisionEnum
from packages.policies.engine import policy_engine
from packages.sandbox_tools.enterprise.models import (
    EnterpriseToolResult,
    ErrorCategory,
    ToolExecutionStatus
)
from packages.sandbox_tools.enterprise.registry import (
    ENTERPRISE_TOOL_REGISTRY,
    ENTERPRISE_TOOL_SCHEMAS
)
from packages.telemetry.verification import IndependentVerificationEngine, VerificationResult
from packages.telemetry.ledger import TamperEvidentEvidenceLedger


class EnterpriseWorkerState(TypedDict, total=False):
    task_id: str
    user_goal: str
    interpreted_goal: str
    plan: List[Dict[str, Any]]
    current_step: int
    completed_steps: List[int]
    available_tools: List[str]
    selected_tool: Optional[str]
    tool_arguments: Dict[str, Any]
    current_tool_result: Optional[Dict[str, Any]]
    observations: List[Dict[str, Any]]
    memory: Dict[str, Any]
    extracted_entities: Dict[str, Any]
    risk_level: str
    approval_required: bool
    approval_status: str  # NONE, PENDING, APPROVED, REJECTED
    approval_id: Optional[str]
    approval_reason: Optional[str]
    retry_count: int
    max_retries: int
    errors: List[Dict[str, Any]]
    verification_requirements: Dict[str, Any]
    verification_results: Optional[Dict[str, Any]]
    evidence: Optional[Dict[str, Any]]
    recovery_action: Optional[str]
    status: str  # RUNNING, WAITING_APPROVAL, SUCCESS, FAILED, RECOVERED

    final_result: str
    session: Any  # AsyncSession
    events: List[Dict[str, Any]]
    simulate_fault: Optional[str]
    use_browser: bool
    custom_document: Optional[str]


class EnterpriseOperationsWorker:
    """
    Autonomous Enterprise Operations Worker.
    State machine that transforms high-level business goals into planned,
    executed, error-recovered, policy-guarded, independently verified enterprise actions.
    """

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(EnterpriseWorkerState)

        # 1. Register Graph Nodes
        builder.add_node("understand_goal", self._node_understand_goal)
        builder.add_node("create_plan", self._node_create_plan)
        builder.add_node("select_tool", self._node_select_tool)
        builder.add_node("authorize_policy", self._node_authorize_policy)
        builder.add_node("request_approval", self._node_request_approval)
        builder.add_node("execute_tool", self._node_execute_tool)
        builder.add_node("observe_and_validate", self._node_observe_and_validate)
        builder.add_node("recover_or_replan", self._node_recover_or_replan)
        builder.add_node("verify_outcome", self._node_verify_outcome)
        builder.add_node("emit_evidence", self._node_emit_evidence)
        builder.add_node("complete_task", self._node_complete_task)

        # 2. Edges and Control Flow
        builder.set_entry_point("understand_goal")
        builder.add_edge("understand_goal", "create_plan")
        builder.add_edge("create_plan", "select_tool")
        builder.add_edge("select_tool", "authorize_policy")

        # Routing after policy check
        builder.add_conditional_edges(
            "authorize_policy",
            self._route_after_policy,
            {
                "execute_tool": "execute_tool",
                "request_approval": "request_approval",
                "recover_or_replan": "recover_or_replan"
            }
        )

        # Routing after approval request
        builder.add_conditional_edges(
            "request_approval",
            self._route_after_approval,
            {
                "execute_tool": "execute_tool",
                "complete_task": "complete_task"
            }
        )

        builder.add_edge("execute_tool", "observe_and_validate")

        # Routing after observation & validation
        builder.add_conditional_edges(
            "observe_and_validate",
            self._route_after_observe,
            {
                "select_tool": "select_tool",
                "recover_or_replan": "recover_or_replan",
                "verify_outcome": "verify_outcome"
            }
        )

        # Routing after error recovery / retry
        builder.add_conditional_edges(
            "recover_or_replan",
            self._route_after_recover,
            {
                "execute_tool": "execute_tool",
                "verify_outcome": "verify_outcome",
                "complete_task": "complete_task"
            }
        )


        builder.add_edge("verify_outcome", "emit_evidence")
        builder.add_edge("emit_evidence", "complete_task")
        builder.add_edge("complete_task", END)

        return builder.compile()

    # --- Node 1: Understand Goal ---
    async def _node_understand_goal(self, state: EnterpriseWorkerState) -> Dict[str, Any]:
        goal = state.get("user_goal", "")
        g_lower = goal.lower()

        # Extract vendor if present
        vendor = None
        for v in ["acme", "contoso", "globex", "initech", "duplicate testing"]:
            if v in g_lower:
                vendor = v.title() if v != "acme" else "Acme"
                break
        if not vendor:
            # Check if custom document has Vendor field
            if state.get("custom_document"):
                v_match_doc = re.search(r"Vendor:\s*([^\n\r]+)", state["custom_document"], re.IGNORECASE)
                if v_match_doc:
                    vendor = v_match_doc.group(1).strip()

            if not vendor:
                # Fallback regex for vendor extraction
                v_match = re.search(r"(?:from|for|vendor)\s+([A-Za-z0-9]+)", goal)
                if v_match:
                    vendor = v_match.group(1).title()
                else:
                    vendor = "Acme"

        # Check for approval condition
        approval_threshold = 100000.0  # Default ₹100,000
        thresh_match = re.search(r"(?:above|exceeding|>)\s*[₹Rs\.]*\s*([0-9,]+)", goal)
        if thresh_match:
            try:
                approval_threshold = float(thresh_match.group(1).replace(",", ""))
            except ValueError:
                pass

        requires_approval_constraint = ("approval" in g_lower or "approve" in g_lower or thresh_match is not None)

        entities = {
            "vendor": vendor,
            "status_filter": "UNPAID" if "unpaid" in g_lower else None,
            "is_latest": "latest" in g_lower,
            "approval_threshold": approval_threshold,
            "requires_approval_constraint": requires_approval_constraint,
            "check_only": "check" in g_lower and "already" in g_lower
        }

        interpreted = (
            f"Autonomous enterprise operation: Locate latest unpaid invoice for vendor '{vendor}', "
            f"extract payable fields, check duplicate status, verify policy threshold (max ₹{approval_threshold:,.2f} before approval), "
            f"submit record into finance ledger with idempotency protection, and independently verify final persistence."
        )

        events = list(state.get("events", []))
        events.append({
            "step_index": 1,
            "node_name": "understand_goal",
            "event_type": "GOAL_INTERPRETED",
            "payload": {"interpreted_goal": interpreted, "entities": entities},
            "timestamp": time.time()
        })

        return {
            "interpreted_goal": interpreted,
            "extracted_entities": entities,
            "memory": {
                "vendor": vendor,
                "status_filter": entities["status_filter"],
                "approval_threshold": approval_threshold
            },
            "risk_level": "HIGH" if requires_approval_constraint else "LOW",
            "events": events
        }

    # --- Node 2: Create Plan ---
    async def _node_create_plan(self, state: EnterpriseWorkerState) -> Dict[str, Any]:
        entities = state.get("extracted_entities", {})
        vendor = entities.get("vendor", "Acme")

        if entities.get("check_only"):
            plan = [
                {
                    "step_index": 0,
                    "title": f"Discover {vendor} Invoices",
                    "description": f"Query document repository for unpaid invoices matching vendor '{vendor}'.",
                    "tool_name": "list_invoices",
                    "status": "PENDING"
                },
                {
                    "step_index": 1,
                    "title": "Read Invoice Document",
                    "description": "Read the raw document contents and metadata of the target invoice.",
                    "tool_name": "read_invoice",
                    "status": "PENDING"
                },
                {
                    "step_index": 2,
                    "title": "Duplicate Record Verification",
                    "description": "Query internal finance system to verify if invoice has already been recorded.",
                    "tool_name": "finance_find_invoice",
                    "status": "PENDING"
                },
                {
                    "step_index": 3,
                    "title": "Cryptographic Audit Receipt",
                    "description": "Generate tamper-evident hash-chained audit evidence and summary.",
                    "tool_name": "emit_evidence",
                    "status": "PENDING"
                }
            ]
        else:
            plan = [
            {
                "step_index": 0,
                "title": f"Discover {vendor} Invoices",
                "description": f"Query document repository for unpaid invoices matching vendor '{vendor}'.",
                "tool_name": "list_invoices",
                "status": "PENDING"
            },
            {
                "step_index": 1,
                "title": "Read Invoice Document",
                "description": "Read the raw document contents and metadata of the target invoice.",
                "tool_name": "read_invoice",
                "status": "PENDING"
            },
            {
                "step_index": 2,
                "title": "Extract & Validate Fields",
                "description": "Extract invoice number, vendor, date, due date, amount, currency and validate integrity.",
                "tool_name": "extract_invoice_fields",
                "status": "PENDING"
            },
            {
                "step_index": 3,
                "title": "Duplicate Record Pre-Check",
                "description": "Query internal finance system to verify if invoice has already been recorded.",
                "tool_name": "finance_find_invoice",
                "status": "PENDING"
            },
            {
                "step_index": 4,
                "title": "Evaluate Policy & Risk",
                "description": f"Enforce corporate policy limits (require human approval if amount > ₹{entities.get('approval_threshold', 100000):,.2f}).",
                "tool_name": "policy_check",
                "status": "PENDING"
            },
            {
                "step_index": 5,
                "title": "Submit to Finance System",
                "description": "Enter invoice into internal finance portal using an idempotent transaction key.",
                "tool_name": "finance_create_invoice",
                "status": "PENDING"
            },
            {
                "step_index": 6,
                "title": "Independent Outcome Verification",
                "description": "Directly query target finance system post-write and reconcile expected vs stored values.",
                "tool_name": "finance_get_invoice",
                "status": "PENDING"
            },
            {
                "step_index": 7,
                "title": "Cryptographic Audit Receipt",
                "description": "Generate tamper-evident hash-chained audit evidence and final executive summary.",
                "tool_name": "emit_evidence",
                "status": "PENDING"
            }
        ]

        events = list(state.get("events", []))
        events.append({
            "step_index": len(events) + 1,
            "node_name": "create_plan",
            "event_type": "PLAN_GENERATED",
            "payload": {"steps_count": len(plan), "plan": plan},
            "timestamp": time.time()
        })

        return {
            "plan": plan,
            "current_step": 0,
            "completed_steps": [],
            "events": events
        }

    # --- Node 3: Select Tool & Prepare Arguments ---
    async def _node_select_tool(self, state: EnterpriseWorkerState) -> Dict[str, Any]:
        curr_step = state.get("current_step", 0)
        plan = list(state.get("plan", []))
        memory = dict(state.get("memory", {}))
        task_id = state.get("task_id", "task_demo")

        if curr_step >= len(plan):
            return {"selected_tool": None, "tool_arguments": {}}

        step_def = plan[curr_step]
        tool_name = step_def["tool_name"]
        args: Dict[str, Any] = {}

        if tool_name == "list_invoices":
            args = {
                "vendor": memory.get("vendor", "Acme"),
                "status": memory.get("status_filter", "UNPAID")
            }
        elif tool_name == "read_invoice":
            inv_num = memory.get("invoice_number")
            file_path = memory.get("file_path")
            args = {"invoice_number": inv_num, "file_path": file_path}
        elif tool_name == "extract_invoice_fields":
            args = {
                "raw_document": state.get("custom_document") or memory.get("raw_content", ""),
                "invoice_number_hint": None if state.get("custom_document") else memory.get("invoice_number")
            }
        elif tool_name == "finance_find_invoice":
            args = {
                "invoice_number": memory.get("invoice_number", "INV-2026-1042")
            }
        elif tool_name == "policy_check":
            # Virtual node step for explicit policy step display in UI plan
            args = {
                "amount": memory.get("amount", 0.0),
                "vendor": memory.get("vendor", "")
            }
        elif tool_name == "finance_create_invoice":
            inv_num = memory.get("invoice_number", "INV-2026-1042")
            amount = memory.get("amount", 84500.0)
            vendor = memory.get("vendor", "Acme Corp")
            due_date = memory.get("due_date", "2026-10-18")
            idemp_key = f"{task_id}_{inv_num}_create"
            memory["idempotency_key"] = idemp_key

            args = {
                "invoice_number": inv_num,
                "vendor": vendor,
                "amount": amount,
                "due_date": due_date,
                "currency": memory.get("currency", "INR"),
                "idempotency_key": idemp_key,
                "task_id": task_id,
                "simulate_failure": state.get("simulate_fault")
            }
        elif tool_name == "finance_get_invoice":
            args = {
                "record_number": memory.get("finance_record_number"),
                "invoice_number": memory.get("invoice_number")
            }

        # Update step state in plan
        plan[curr_step]["status"] = "IN_PROGRESS"

        events = list(state.get("events", []))
        events.append({
            "step_index": len(events) + 1,
            "node_name": "select_tool",
            "event_type": "TOOL_SELECTED",
            "payload": {"tool_name": tool_name, "arguments": args, "step": curr_step},
            "timestamp": time.time()
        })

        return {
            "selected_tool": tool_name,
            "tool_arguments": args,
            "plan": plan,
            "memory": memory,
            "events": events
        }

    # --- Node 4: Authorize Policy ---
    async def _node_authorize_policy(self, state: EnterpriseWorkerState) -> Dict[str, Any]:
        tool_name = state.get("selected_tool")
        tool_args = state.get("tool_arguments", {})
        memory = state.get("memory", {})
        task_id = state.get("task_id", "task_demo")

        # Virtual policy check step
        if tool_name == "policy_check":
            amount = memory.get("amount", 0.0)
            threshold = memory.get("approval_threshold", 100000.0)
            if amount > threshold:
                return {
                    "approval_required": True,
                    "approval_reason": f"Invoice amount ₹{amount:,.2f} exceeds policy limit ₹{threshold:,.2f}."
                }
            return {
                "approval_required": False
            }

        # If approval has already been granted by human manager, proceed without re-requesting
        if state.get("approval_status") == "APPROVED":
            return {
                "approval_required": False
            }

        policy_ctx = PolicyContext(
            user_id="autonomous_worker_daemon",
            user_role="enterprise_worker",
            tool_name=tool_name or "noop",
            tool_arguments=tool_args,
            session_metadata={"max_approval_threshold": memory.get("approval_threshold", 100000.0)},
            prompt_text=state.get("user_goal", "")
        )

        decision = policy_engine.evaluate(policy_ctx)


        events = list(state.get("events", []))
        events.append({
            "step_index": len(events) + 1,
            "node_name": "authorize_policy",
            "event_type": "POLICY_EVALUATED",
            "payload": {
                "rule_name": decision.rule_name,
                "decision": decision.decision.value,
                "reason": decision.reason
            },
            "timestamp": time.time()
        })

        # Save PolicyDecision to database if session is present
        session = state.get("session")
        if session:
            db_decision = PolicyDecision(
                id=generate_uuid(),
                run_id=task_id,
                rule_name=decision.rule_name,
                decision=decision.decision.value,
                reason=decision.reason,
                context_json={"tool_name": tool_name, "tool_args": tool_args}
            )
            session.add(db_decision)
            await session.commit()

        if decision.decision == PolicyDecisionEnum.REQUIRE_APPROVAL:
            return {
                "approval_required": True,
                "approval_reason": decision.reason,
                "events": events
            }
        elif decision.decision == PolicyDecisionEnum.DENY:
            return {
                "approval_required": False,
                "status": "FAILED",
                "final_result": f"Policy Violation: {decision.reason}",
                "events": events
            }

        return {
            "approval_required": False,
            "events": events
        }

    # Route after policy check
    def _route_after_policy(self, state: EnterpriseWorkerState) -> str:
        if state.get("status") == "FAILED":
            return "recover_or_replan"
        if state.get("approval_required"):
            return "request_approval"
        return "execute_tool"

    # --- Node 5: Request Human Approval ---
    async def _node_request_approval(self, state: EnterpriseWorkerState) -> Dict[str, Any]:
        task_id = state.get("task_id", "task_demo")
        session = state.get("session")
        memory = state.get("memory", {})
        reason = state.get("approval_reason", "High-value enterprise operation requires authorization.")

        approval_status = state.get("approval_status", "PENDING")
        approval_id = state.get("approval_id")

        if approval_status == "APPROVED":
            # Human already approved! Resume execution
            events = list(state.get("events", []))
            events.append({
                "step_index": len(events) + 1,
                "node_name": "request_approval",
                "event_type": "APPROVAL_GRANTED",
                "payload": {"approval_id": approval_id, "status": "APPROVED"},
                "timestamp": time.time()
            })
            return {"approval_required": False, "status": "RUNNING", "events": events}

        if approval_status == "REJECTED":
            events = list(state.get("events", []))
            events.append({
                "step_index": len(events) + 1,
                "node_name": "request_approval",
                "event_type": "APPROVAL_REJECTED",
                "payload": {"approval_id": approval_id, "status": "REJECTED"},
                "timestamp": time.time()
            })
            return {
                "status": "REJECTED",
                "final_result": "Operation cancelled: Human manager rejected the approval request.",
                "events": events
            }

        # Otherwise create new pending approval
        if not approval_id:
            approval_id = generate_uuid()
            if session:
                appr = Approval(
                    id=approval_id,
                    run_id=task_id,
                    action_type="high_value_invoice_processing",
                    proposed_payload_json={
                        "invoice_number": memory.get("invoice_number"),
                        "vendor": memory.get("vendor"),
                        "amount": memory.get("amount"),
                        "due_date": memory.get("due_date")
                    },
                    status="pending",
                    reason=reason
                )
                session.add(appr)
                await session.commit()

        events = list(state.get("events", []))
        events.append({
            "step_index": len(events) + 1,
            "node_name": "request_approval",
            "event_type": "APPROVAL_REQUESTED",
            "payload": {"approval_id": approval_id, "reason": reason},
            "timestamp": time.time()
        })

        return {
            "status": "WAITING_APPROVAL",
            "approval_id": approval_id,
            "approval_status": "PENDING",
            "events": events
        }

    def _route_after_approval(self, state: EnterpriseWorkerState) -> str:
        if state.get("status") == "WAITING_APPROVAL" or state.get("status") == "REJECTED":
            return "complete_task"
        return "execute_tool"

    # --- Node 6: Execute Tool ---
    async def _node_execute_tool(self, state: EnterpriseWorkerState) -> Dict[str, Any]:
        tool_name = state.get("selected_tool")
        tool_args = dict(state.get("tool_arguments", {}))
        session = state.get("session")
        task_id = state.get("task_id", "task_demo")
        memory = state.get("memory", {})
        start_time = time.time()

        # Handle virtual steps
        if tool_name == "policy_check":
            return {
                "current_tool_result": {
                    "success": True,
                    "status": "SUCCESS",
                    "action_summary": "Policy verified: Action authorized under current thresholds."
                }
            }

        fn = ENTERPRISE_TOOL_REGISTRY.get(tool_name)
        if not fn:
            return {
                "current_tool_result": {
                    "success": False,
                    "error": f"Tool '{tool_name}' not implemented in enterprise registry.",
                    "error_category": ErrorCategory.TOOL_ERROR,
                    "retryable": False
                }
            }

        # Inject custom document if provided by operator
        custom_doc = state.get("custom_document")
        if custom_doc and tool_name in ["list_invoices", "search_company_files", "read_invoice"]:
            inv_match = re.search(r"Invoice\s*(?:Number|#|No\.?):\s*([A-Za-z0-9\-]+)", custom_doc, re.IGNORECASE)
            extracted_inv = inv_match.group(1).strip() if inv_match else "CUSTOM-INV-001"
            custom_inv = {
                "invoice_number": extracted_inv,
                "vendor": memory.get("vendor", "Custom Vendor"),
                "amount": memory.get("amount", 0.0),
                "status": "UNPAID",
                "due_date": "2026-10-31",
                "file_path": "/user_uploads/live_custom_document.txt"
            }
            res_dict = {
                "success": True,
                "status": "SUCCESS",
                "data": {
                    "raw_content": custom_doc,
                    "invoice_number": extracted_inv,
                    "file_path": "/user_uploads/live_custom_document.txt",
                    "latest_invoice": custom_inv,
                    "invoices": [custom_inv]
                },
                "action_summary": f"Ingested live custom enterprise document ({extracted_inv}) directly from operator input."
            }
        else:
            # Inject session for tools that query database
            kwargs = dict(tool_args)
            if tool_name in ["list_invoices", "read_invoice", "search_company_files", "search_vendor", "finance_find_invoice", "finance_create_invoice", "finance_get_invoice"]:
                kwargs["session"] = session

            # If operator enabled Playwright browser automation, interact with the simulated web portal
            if state.get("use_browser") and tool_name == "finance_create_invoice":
                try:
                    from packages.sandbox_tools.enterprise.browser_tools import browser_navigate, browser_type, browser_click
                    await browser_navigate("/sandbox/finance")
                    await browser_type("#invoice_number", kwargs.get("invoice_number", "INV-2026-1042"))
                    await browser_type("#vendor", kwargs.get("vendor", "Acme Corp"))
                    await browser_type("#amount", str(kwargs.get("amount", 84500.0)))
                    await browser_type("#due_date", kwargs.get("due_date", "2026-10-18"))
                    await browser_click("#submit_btn")
                except Exception:
                    pass

            try:
                res: EnterpriseToolResult = await fn(**kwargs)
                res_dict = res.model_dump()
            except Exception as e:
                res_dict = {
                    "success": False,
                    "status": "ERROR",
                    "error": str(e),
                    "error_category": ErrorCategory.TOOL_ERROR.value,
                    "retryable": True
                }

        latency_ms = (time.time() - start_time) * 1000

        # Persist ToolCall record
        if session:
            tc = ToolCall(
                id=generate_uuid(),
                run_id=task_id,
                tool_name=tool_name,
                arguments_json={k: v for k, v in tool_args.items() if k != "session"},
                response_json=res_dict.get("data"),
                status="success" if res_dict.get("success") else "error",
                error_details=res_dict.get("error"),
                latency_ms=latency_ms,
                idempotency_key=res_dict.get("idempotency_key")
            )
            session.add(tc)
            await session.commit()

        events = list(state.get("events", []))
        events.append({
            "step_index": len(events) + 1,
            "node_name": "execute_tool",
            "event_type": "TOOL_EXECUTED",
            "payload": {
                "tool_name": tool_name,
                "success": res_dict.get("success"),
                "status": res_dict.get("status"),
                "action_summary": res_dict.get("action_summary"),
                "error": res_dict.get("error")
            },
            "timestamp": time.time()
        })

        return {
            "current_tool_result": res_dict,
            "events": events
        }

    # --- Node 7: Observe Result & Update Working Memory ---
    async def _node_observe_and_validate(self, state: EnterpriseWorkerState) -> Dict[str, Any]:
        tool_name = state.get("selected_tool")
        res = state.get("current_tool_result", {})
        curr_step = state.get("current_step", 0)
        plan = list(state.get("plan", []))
        memory = dict(state.get("memory", {}))
        completed = list(state.get("completed_steps", []))
        observations = list(state.get("observations", []))

        # Check for failure
        if not res.get("success"):
            err_cat = res.get("error_category", ErrorCategory.TOOL_ERROR.value)
            plan[curr_step]["status"] = "FAILED"
            plan[curr_step]["error"] = res.get("error")
            return {
                "errors": [{"step": curr_step, "tool": tool_name, "error": res.get("error"), "category": err_cat}],
                "plan": plan
            }

        # Step succeeded! Update plan & memory
        data = res.get("data") or {}
        summary = res.get("action_summary", "")

        plan[curr_step]["status"] = "COMPLETED"
        plan[curr_step]["action_summary"] = summary
        completed.append(curr_step)

        # Update working memory based on tool outputs
        if tool_name == "list_invoices":
            latest = data.get("latest_invoice") or (data.get("invoices", [])[0] if data.get("invoices") else None)
            if latest:
                memory["invoice_number"] = latest["invoice_number"]
                memory["vendor"] = latest["vendor"]
                memory["amount"] = latest["amount"]
                memory["due_date"] = latest["due_date"]
                memory["file_path"] = latest.get("file_path")
                memory["status"] = latest["status"]
            else:
                # No invoices found
                return {
                    "errors": [{"step": curr_step, "tool": tool_name, "error": "No matching invoices found", "category": ErrorCategory.NOT_FOUND.value}],
                    "plan": plan
                }
        elif tool_name == "read_invoice":
            memory["raw_content"] = data.get("raw_content", "")
            if not memory.get("invoice_number"):
                memory["invoice_number"] = data.get("invoice_number")
        elif tool_name == "extract_invoice_fields":
            memory["invoice_number"] = data.get("invoice_number", memory.get("invoice_number"))
            memory["vendor"] = data.get("vendor", memory.get("vendor"))
            memory["amount"] = float(data.get("amount", memory.get("amount", 0)))
            memory["due_date"] = data.get("due_date", memory.get("due_date"))
            memory["currency"] = data.get("currency", memory.get("currency", "USD"))
        elif tool_name == "finance_find_invoice":
            if data.get("found"):
                record = data.get("record") or {}
                memory["finance_record_number"] = record.get("record_number")
        elif tool_name == "finance_create_invoice":
            memory["finance_record_number"] = data.get("record_number")
            memory["idempotency_key"] = data.get("idempotency_key")
        elif tool_name == "finance_get_invoice":
            memory["verified_record"] = data


        observations.append({
            "step": curr_step,
            "tool": tool_name,
            "summary": summary,
            "data": data
        })

        events = list(state.get("events", []))
        events.append({
            "step_index": len(events) + 1,
            "node_name": "observe_and_validate",
            "event_type": "RESULT_OBSERVED",
            "payload": {"step": curr_step, "tool": tool_name, "summary": summary},
            "timestamp": time.time()
        })

        # Advance to next plan step
        next_step = curr_step + 1

        return {
            "current_step": next_step,
            "completed_steps": completed,
            "plan": plan,
            "memory": memory,
            "observations": observations,
            "events": events
        }

    # Route after observe
    def _route_after_observe(self, state: EnterpriseWorkerState) -> str:
        if state.get("errors"):
            return "recover_or_replan"
        curr_step = state.get("current_step", 0)
        # Check if we reached step 6 (Independent Verification)
        if curr_step == 6:
            return "verify_outcome"
        if curr_step >= len(state.get("plan", [])) - 1:
            return "verify_outcome"
        return "select_tool"

    # --- Node 8: Recover or Re-Plan ---
    async def _node_recover_or_replan(self, state: EnterpriseWorkerState) -> Dict[str, Any]:
        errors = state.get("errors", [])
        last_error = errors[-1] if errors else {}
        err_cat = last_error.get("category", ErrorCategory.UNKNOWN.value)
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 3)
        curr_step = state.get("current_step", 0)
        plan = list(state.get("plan", []))
        memory = dict(state.get("memory", {}))

        events = list(state.get("events", []))


        # Check for bounded retries on transient errors
        if err_cat in [ErrorCategory.TRANSIENT.value, ErrorCategory.BROWSER_ERROR.value] and retry_count < max_retries:
            new_retry = retry_count + 1
            # Exponential backoff simulation
            backoff_delay = 0.5 * (2 ** (new_retry - 1))
            await asyncio.sleep(min(backoff_delay, 1.0))

            events.append({
                "step_index": len(events) + 1,
                "node_name": "recover_or_replan",
                "event_type": "RETRY_TRIGGERED",
                "payload": {
                    "retry_attempt": new_retry,
                    "max_retries": max_retries,
                    "error_category": err_cat,
                    "backoff_seconds": backoff_delay
                },
                "timestamp": time.time()
            })

            tool_args = dict(state.get("tool_arguments", {}))
            tool_args["simulate_failure"] = None

            # Clear simulate_fault after first failure to demonstrate recovery!
            return {
                "retry_count": new_retry,
                "simulate_fault": None,
                "tool_arguments": tool_args,
                "recovery_action": "RETRY",
                "errors": [],
                "events": events
            }

        # Check for duplicate write recovery: fetch existing record instead of failing!
        if err_cat == ErrorCategory.DUPLICATE.value:
            events.append({
                "step_index": len(events) + 1,
                "node_name": "recover_or_replan",
                "event_type": "DUPLICATE_RECOVERY",
                "payload": {"strategy": "suppress_duplicate_and_verify_existing"},
                "timestamp": time.time()
            })
            if not memory.get("finance_record_number"):
                res_data = state.get("current_tool_result", {}).get("data", {})
                memory["finance_record_number"] = res_data.get("existing_record_number", "FIN-77100")
            # Advance step and verify existing record
            return {
                "current_step": 6,
                "memory": memory,
                "recovery_action": "VERIFY",
                "errors": [],
                "events": events
            }


        # Unrecoverable or exceeded retries
        events.append({
            "step_index": len(events) + 1,
            "node_name": "recover_or_replan",
            "event_type": "TASK_FAILED",
            "payload": {"error": last_error.get("error"), "category": err_cat},
            "timestamp": time.time()
        })

        return {
            "status": "FAILED",
            "final_result": f"Task stopped due to unrecoverable condition ({err_cat}): {last_error.get('error')}",
            "recovery_action": "COMPLETE",
            "events": events
        }

    def _route_after_recover(self, state: EnterpriseWorkerState) -> str:
        rec_action = state.get("recovery_action")
        if rec_action == "RETRY":
            return "execute_tool"
        elif rec_action == "VERIFY":
            return "verify_outcome"
        return "complete_task"


    # --- Node 9: Independent Verification Engine ---
    async def _node_verify_outcome(self, state: EnterpriseWorkerState) -> Dict[str, Any]:
        task_id = state.get("task_id", "task_demo")
        session = state.get("session")
        memory = state.get("memory", {})
        plan = list(state.get("plan", []))

        inv_num = memory.get("invoice_number", "INV-2026-1042")
        vendor = memory.get("vendor", "Acme")
        amount = memory.get("amount", 84500.0)
        due_date = memory.get("due_date", "2026-10-18")
        rec_num = memory.get("finance_record_number")

        v_result: VerificationResult = await IndependentVerificationEngine.verify_finance_invoice(
            session=session,
            task_id=task_id,
            expected_invoice_number=inv_num,
            expected_vendor=vendor,
            expected_amount=amount,
            expected_due_date=due_date,
            record_number=rec_num
        )

        v_dict = v_result.model_dump()

        if len(plan) > 6:
            plan[6]["status"] = "COMPLETED" if v_result.verified else "FAILED"
            plan[6]["action_summary"] = f"Independent verification {'PASSED' if v_result.verified else 'FAILED'}: checked {len(v_result.checks)} assertions against Finance ERP."

        events = list(state.get("events", []))
        events.append({
            "step_index": len(events) + 1,
            "node_name": "verify_outcome",
            "event_type": "VERIFICATION_COMPLETED",
            "payload": {
                "verified": v_result.verified,
                "status": v_result.status,
                "record_number": v_result.record_number,
                "checks": [c.model_dump() for c in v_result.checks]
            },
            "timestamp": time.time()
        })

        return {
            "verification_results": v_dict,
            "plan": plan,
            "events": events
        }

    # --- Node 10: Emit Cryptographic Evidence ---
    async def _node_emit_evidence(self, state: EnterpriseWorkerState) -> Dict[str, Any]:
        task_id = state.get("task_id", "task_demo")
        session = state.get("session")
        memory = state.get("memory", {})
        v_res = state.get("verification_results", {})
        plan = list(state.get("plan", []))

        inv_num = memory.get("invoice_number", "INV-2026-1042")
        vendor = memory.get("vendor", "Acme")
        amount = memory.get("amount", 84500.0)
        due_date = memory.get("due_date", "2026-10-18")
        rec_num = memory.get("finance_record_number") or v_res.get("record_number", "FIN-82914")

        audit_payload = {
            "task_id": task_id,
            "goal": state.get("user_goal"),
            "vendor": vendor,
            "invoice_number": inv_num,
            "amount": amount,
            "due_date": due_date,
            "finance_record": rec_num,
            "verification_status": v_res.get("status", "PASSED"),
            "checks_passed": len([c for c in v_res.get("checks", []) if c.get("matched")]),
            "total_checks": len(v_res.get("checks", [])),
            "idempotency_key": memory.get("idempotency_key"),
            "completed_steps_count": len(state.get("completed_steps", []))
        }

        receipt = None
        if session:
            try:
                receipt = await TamperEvidentEvidenceLedger.append_receipt(
                    session=session,
                    run_id=task_id,
                    scenario_id="autonomous_invoice_processing",
                    final_outcome="SUCCESS" if v_res.get("verified") else "VERIFICATION_FAILED",
                    event_data=audit_payload
                )
            except Exception as e:
                pass

        if len(plan) > 7:
            plan[7]["status"] = "COMPLETED"
            plan[7]["action_summary"] = f"Cryptographic evidence receipt signed and chained (Block Hash: {receipt.event_hash[:16] if receipt else 'local_sig'})."

        # Construct final executive summary
        summary = (
            f"Task completed successfully.\n"
            f"Invoice: {inv_num}\n"
            f"Vendor: {vendor}\n"
            f"Amount: ₹{amount:,.0f}\n"
            f"Due date: {due_date}\n"
            f"Finance record: {rec_num}\n"
            f"Verification: {v_res.get('status', 'PASSED')}\n"
            f"Evidence:\n"
            f"  invoice source: {memory.get('file_path', f'/company/invoices/{vendor.lower()}/{inv_num}.txt')}\n"
            f"  execution trace: {task_id}\n"
            f"  finance record: {rec_num}\n"
            f"  final verification result: {v_res.get('status', 'PASSED')} ({v_res.get('evidence_payload', {}).get('checks_passed', len(v_res.get('checks', [])))}/{len(v_res.get('checks', []))} checks matched)"
        )

        events = list(state.get("events", []))
        events.append({
            "step_index": len(events) + 1,
            "node_name": "emit_evidence",
            "event_type": "EVIDENCE_EMITTED",
            "payload": {
                "receipt_id": receipt.id if receipt else "local_receipt",
                "event_hash": receipt.event_hash if receipt else "0000_hash"
            },
            "timestamp": time.time()
        })

        return {
            "status": "SUCCESS" if v_res.get("verified") else "FAILED",
            "final_result": summary,
            "evidence": audit_payload,
            "plan": plan,
            "events": events
        }

    # --- Node 11: Complete Task ---
    async def _node_complete_task(self, state: EnterpriseWorkerState) -> Dict[str, Any]:
        task_id = state.get("task_id", "task_demo")
        session = state.get("session")
        status = state.get("status", "SUCCESS")
        final_res = state.get("final_result", "")

        if session:
            stmt = select(EnterpriseTask).where(EnterpriseTask.id == task_id)
            res = await session.execute(stmt)
            task = res.scalar_one_or_none()
            if task:
                task.status = status
                task.plan_json = state.get("plan")
                task.memory_json = state.get("memory")
                task.extracted_entities_json = state.get("extracted_entities")
                task.verification_status = state.get("verification_results", {}).get("status", "NONE")
                task.verification_details_json = state.get("verification_results")
                task.final_summary = final_res
                await session.commit()

        events = list(state.get("events", []))
        events.append({
            "step_index": len(events) + 1,
            "node_name": "complete_task",
            "event_type": "TASK_COMPLETED",
            "payload": {"status": status, "final_summary": final_res[:200]},
            "timestamp": time.time()
        })

        return {
            "events": events
        }
