from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from apps.api.app.db.database import get_db
from apps.api.app.db.models import EnterpriseTask, Approval, generate_uuid
from packages.agent.enterprise_worker import EnterpriseOperationsWorker

router = APIRouter(prefix="/tasks", tags=["Autonomous Tasks"])

# In-memory store for active graph states waiting for approval resume
_PAUSED_TASK_STATES: Dict[str, Dict[str, Any]] = {}


class RunTaskRequest(BaseModel):
    goal: str = Field(..., description="Natural language enterprise business goal")
    simulate_fault: Optional[str] = Field(None, description="Optional fault injection code (e.g. 'HTTP_500')")
    use_browser: bool = Field(False, description="Whether to execute actions via Playwright browser")
    max_retries: int = Field(3, description="Maximum bounded retries for transient errors")


class TaskApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., description="'approve' or 'reject'")
    reason: Optional[str] = Field("Authorized by operations manager", description="Approval notes")


@router.post("/run")
async def run_autonomous_task(
    req: RunTaskRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submits a natural-language business objective to the Autonomous Enterprise Operations Worker.
    The worker plans, discovers, extracts, enforces policy, requests approval if needed,
    executes (API or Browser), recovers from failures, and independently verifies outcomes.
    """
    task_id = f"task_{generate_uuid()[:8]}"
    worker = EnterpriseOperationsWorker()

    # Pre-create EnterpriseTask in DB
    db_task = EnterpriseTask(
        id=task_id,
        user_goal=req.goal,
        status="RUNNING"
    )
    db.add(db_task)
    await db.commit()

    state_input = {
        "task_id": task_id,
        "user_goal": req.goal,
        "session": db,
        "max_retries": req.max_retries,
        "retry_count": 0,
        "simulate_fault": req.simulate_fault,
        "use_browser": req.use_browser
    }

    result = await worker.graph.ainvoke(state_input)

    # If task paused for approval, store state so it can resume
    if result.get("status") == "WAITING_APPROVAL":
        # Keep non-session serializable state for resuming
        pause_state = dict(result)
        pause_state.pop("session", None)
        _PAUSED_TASK_STATES[task_id] = pause_state

    # Update DB task
    db_task.interpreted_goal = result.get("interpreted_goal")
    db_task.plan_json = result.get("plan")
    db_task.status = result.get("status", "SUCCESS")
    db_task.memory_json = result.get("memory")
    db_task.extracted_entities_json = result.get("extracted_entities")
    db_task.approval_id = result.get("approval_id")
    db_task.approval_status = result.get("approval_status")
    db_task.retry_count = result.get("retry_count", 0)
    db_task.verification_status = result.get("verification_results", {}).get("status", "NONE")
    db_task.verification_details_json = result.get("verification_results")
    db_task.final_summary = result.get("final_result")
    await db.commit()

    return {
        "task_id": task_id,
        "status": result.get("status"),
        "interpreted_goal": result.get("interpreted_goal"),
        "plan": result.get("plan", []),
        "current_step": result.get("current_step", 0),
        "memory": result.get("memory", {}),
        "extracted_entities": result.get("extracted_entities", {}),
        "approval_id": result.get("approval_id"),
        "approval_status": result.get("approval_status"),
        "retry_count": result.get("retry_count", 0),
        "verification_results": result.get("verification_results"),
        "evidence": result.get("evidence"),
        "final_result": result.get("final_result"),
        "events": result.get("events", [])
    }


@router.get("/{task_id}")
async def get_task_details(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(EnterpriseTask).where(EnterpriseTask.id == task_id)
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    return {
        "task_id": task.id,
        "user_goal": task.user_goal,
        "interpreted_goal": task.interpreted_goal,
        "plan": task.plan_json or [],
        "current_step": task.current_step,
        "status": task.status,
        "memory": task.memory_json or {},
        "extracted_entities": task.extracted_entities_json or {},
        "risk_level": task.risk_level,
        "approval_id": task.approval_id,
        "approval_status": task.approval_status,
        "retry_count": task.retry_count,
        "verification_status": task.verification_status,
        "verification_details": task.verification_details_json,
        "final_summary": task.final_summary,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None
    }


@router.post("/{task_id}/decision")
async def decide_task_approval(
    task_id: str,
    req: TaskApprovalDecisionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Decides on a pending human approval for a paused autonomous task (approve or reject)
    and resumes execution to completion.
    """
    stmt = select(EnterpriseTask).where(EnterpriseTask.id == task_id)
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    if task.status != "WAITING_APPROVAL":
        raise HTTPException(
            status_code=400,
            detail=f"Task '{task_id}' is in status '{task.status}', not WAITING_APPROVAL."
        )

    # Update Approval record in DB
    if task.approval_id:
        stmt_appr = select(Approval).where(Approval.id == task.approval_id)
        res_appr = await db.execute(stmt_appr)
        appr_obj = res_appr.scalar_one_or_none()
        if appr_obj:
            appr_obj.status = "approved" if req.decision == "approve" else "rejected"
            appr_obj.decided_by = "operations_manager"
            await db.commit()

    # Retrieve paused state
    paused_state = _PAUSED_TASK_STATES.get(task_id)
    if not paused_state:
        # Reconstruct minimal state from DB
        paused_state = {
            "task_id": task_id,
            "user_goal": task.user_goal,
            "interpreted_goal": task.interpreted_goal,
            "plan": task.plan_json or [],
            "current_step": task.current_step,
            "memory": task.memory_json or {},
            "extracted_entities": task.extracted_entities_json or {},
            "approval_id": task.approval_id,
            "max_retries": 3,
            "retry_count": task.retry_count,
            "events": []
        }

    paused_state["session"] = db
    paused_state["approval_status"] = "APPROVED" if req.decision == "approve" else "REJECTED"

    worker = EnterpriseOperationsWorker()
    resume_result = await worker.graph.ainvoke(paused_state)

    _PAUSED_TASK_STATES.pop(task_id, None)

    # Update task in DB
    task.status = resume_result.get("status", "SUCCESS")
    task.plan_json = resume_result.get("plan")
    task.memory_json = resume_result.get("memory")
    task.approval_status = paused_state["approval_status"]
    task.verification_status = resume_result.get("verification_results", {}).get("status", "NONE")
    task.verification_details_json = resume_result.get("verification_results")
    task.final_summary = resume_result.get("final_result")
    await db.commit()

    return {
        "task_id": task_id,
        "status": resume_result.get("status"),
        "approval_decision": req.decision,
        "plan": resume_result.get("plan", []),
        "verification_results": resume_result.get("verification_results"),
        "final_result": resume_result.get("final_result"),
        "events": resume_result.get("events", [])
    }


@router.get("")
async def list_tasks(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(EnterpriseTask).order_by(desc(EnterpriseTask.created_at)).limit(limit)
    res = await db.execute(stmt)
    tasks = res.scalars().all()
    return [{
        "task_id": t.id,
        "user_goal": t.user_goal,
        "interpreted_goal": t.interpreted_goal,
        "status": t.status,
        "verification_status": t.verification_status,
        "retry_count": t.retry_count,
        "created_at": t.created_at.isoformat() if t.created_at else None
    } for t in tasks]
