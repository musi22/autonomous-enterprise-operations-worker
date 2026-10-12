from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.models import Approval, generate_uuid
from packages.sandbox_tools.enterprise.models import (
    EnterpriseToolResult,
    ErrorCategory,
    ToolExecutionStatus
)


async def request_human_approval(
    session: AsyncSession,
    run_id: str,
    action_type: str,
    reason: str,
    proposed_payload: Dict[str, Any]
) -> EnterpriseToolResult:
    """
    Submits a human-in-the-loop approval request when an autonomous action requires explicit authorization.
    Pauses agent execution until approved or rejected.
    """
    try:
        approval_id = generate_uuid()
        approval = Approval(
            id=approval_id,
            run_id=run_id,
            action_type=action_type,
            proposed_payload_json=proposed_payload,
            status="pending",
            reason=reason
        )
        session.add(approval)
        await session.commit()

        amount_str = f"₹{proposed_payload.get('amount', 0):,.2f}" if "amount" in proposed_payload else "N/A"
        return EnterpriseToolResult(
            success=True,
            status=ToolExecutionStatus.APPROVAL_REQUIRED,
            data={
                "approval_id": approval_id,
                "status": "pending",
                "action_type": action_type,
                "reason": reason,
                "proposed_payload": proposed_payload
            },
            error="Action requires human approval before proceeding.",
            error_category=ErrorCategory.APPROVAL_REQUIRED,
            retryable=False,
            action_summary=f"Created approval request {approval_id}: {reason} (Amount: {amount_str}). Paused for human decision."
        )
    except Exception as e:
        await session.rollback()
        return EnterpriseToolResult(
            success=False,
            status=ToolExecutionStatus.ERROR,
            error=f"Failed to create approval request: {str(e)}",
            error_category=ErrorCategory.TOOL_ERROR,
            retryable=False
        )
