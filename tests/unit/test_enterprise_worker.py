import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.app.db.models import FinanceRecord, Approval
from packages.agent.enterprise_worker import EnterpriseOperationsWorker
from packages.telemetry.verification import IndependentVerificationEngine


@pytest.mark.asyncio
async def test_primary_invoice_workflow(db_session: AsyncSession):
    """
    Primary Demo Workflow:
    Find latest unpaid Acme invoice, extract details, enter into finance, verify independently.
    """
    worker = EnterpriseOperationsWorker()
    task_id = "test_primary_wf_01"
    goal = "Find the latest unpaid invoice from Acme, extract the invoice number, amount and due date, enter it into our finance system, verify that it was saved correctly, and tell me when it is done."

    state_input = {
        "task_id": task_id,
        "user_goal": goal,
        "session": db_session,
        "max_retries": 3,
        "retry_count": 0
    }

    result = await worker.graph.ainvoke(state_input)

    assert result["status"] == "SUCCESS", f"Task failed: {result.get('final_result')}"
    assert result["verification_results"] is not None
    assert result["verification_results"]["verified"] is True
    assert result["verification_results"]["status"] == "PASSED"

    memory = result["memory"]
    assert memory["invoice_number"] == "INV-2026-1042"
    assert memory["amount"] == 84500.0
    assert memory["due_date"] == "2026-10-18"

    # Confirm record truly exists in target system
    stmt = select(FinanceRecord).where(FinanceRecord.invoice_number == "INV-2026-1042")
    res = await db_session.execute(stmt)
    saved_rec = res.scalar_one_or_none()
    assert saved_rec is not None
    assert saved_rec.record_number == "FIN-82914"
    assert saved_rec.amount == 84500.0

    # Verify final result text formatting
    final_text = result["final_result"]
    assert "Task completed successfully" in final_text
    assert "INV-2026-1042" in final_text
    assert "₹84,500" in final_text
    assert "FIN-82914" in final_text
    assert "Verification: PASSED" in final_text


@pytest.mark.asyncio
async def test_human_approval_workflow(db_session: AsyncSession):
    """
    Second Demo: Human approval required for high-value invoice (> ₹100,000).
    Contoso invoice is ₹150,000 -> pause and request approval.
    """
    worker = EnterpriseOperationsWorker()
    task_id = "test_approval_wf_02"
    goal = "Process the latest Contoso invoice, but do not enter invoices above ₹100,000 without my approval."

    state_input = {
        "task_id": task_id,
        "user_goal": goal,
        "session": db_session,
        "max_retries": 3,
        "retry_count": 0
    }

    # First invocation should pause at approval
    res_pause = await worker.graph.ainvoke(state_input)
    assert res_pause["status"] == "WAITING_APPROVAL"
    assert res_pause["approval_id"] is not None

    # Check approval in database
    stmt = select(Approval).where(Approval.run_id == task_id)
    appr_res = await db_session.execute(stmt)
    approval_rec = appr_res.scalar_one_or_none()
    assert approval_rec is not None
    assert approval_rec.status == "pending"

    # Now simulate human manager approving the request
    approval_rec.status = "approved"
    await db_session.commit()

    # Resume the workflow with approved status
    res_pause["approval_status"] = "APPROVED"
    res_resume = await worker.graph.ainvoke(res_pause)

    assert res_resume["status"] == "SUCCESS"
    assert res_resume["verification_results"]["verified"] is True
    assert res_resume["memory"]["invoice_number"] == "CONT-8893"
    assert res_resume["memory"]["amount"] == 150000.0


@pytest.mark.asyncio
async def test_transient_failure_and_recovery(db_session: AsyncSession):
    """
    Third Demo: Finance submission fails with transient HTTP 500 error,
    system detects error category, retries with backoff, and succeeds.
    """
    worker = EnterpriseOperationsWorker()
    task_id = "test_recovery_wf_03"
    goal = "Find the latest unpaid invoice from Acme, extract amount and due date, enter into finance system, and verify."

    state_input = {
        "task_id": task_id,
        "user_goal": goal,
        "session": db_session,
        "max_retries": 3,
        "retry_count": 0,
        "simulate_fault": "HTTP_500"  # Deterministic simulated failure
    }

    result = await worker.graph.ainvoke(state_input)
    assert result["status"] == "SUCCESS"
    assert result["retry_count"] >= 1  # Verify retry occurred
    assert result["verification_results"]["verified"] is True

    # Execution trace should contain the RETRY_TRIGGERED event
    events = result["events"]
    retry_events = [e for e in events if e.get("event_type") == "RETRY_TRIGGERED"]
    assert len(retry_events) >= 1
    assert retry_events[0]["payload"]["error_category"] == "TRANSIENT"


@pytest.mark.asyncio
async def test_idempotent_duplicate_suppression(db_session: AsyncSession):
    """
    Idempotency: Re-submitting the same invoice with matching key returns
    existing record without creating duplicate entries.
    """
    from packages.sandbox_tools.enterprise.finance_tools import finance_create_invoice

    idemp_key = "idemp_test_repeat_01"
    # First write
    r1 = await finance_create_invoice(
        session=db_session,
        invoice_number="INV-IDEMP-01",
        vendor="Acme Corp",
        amount=50000.0,
        due_date="2026-10-30",
        idempotency_key=idemp_key
    )
    assert r1.success is True
    rec_num = r1.data["record_number"]

    # Replay write with same key
    r2 = await finance_create_invoice(
        session=db_session,
        invoice_number="INV-IDEMP-01",
        vendor="Acme Corp",
        amount=50000.0,
        due_date="2026-10-30",
        idempotency_key=idemp_key
    )
    assert r2.success is True
    assert r2.data["record_number"] == rec_num
    assert r2.data.get("is_idempotent_replay") is True


@pytest.mark.asyncio
async def test_independent_verification_engine(db_session: AsyncSession):
    """
    Independent Verification Engine tests: verifies field matching and detects tampering/mismatch.
    """
    from packages.sandbox_tools.enterprise.finance_tools import finance_create_invoice

    await finance_create_invoice(
        session=db_session,
        invoice_number="INV-VERIF-TEST",
        vendor="Acme Corp",
        amount=75000.0,
        due_date="2026-11-15",
        idempotency_key="idemp_verif_test_1"
    )

    # 1. Matching case
    v_pass = await IndependentVerificationEngine.verify_finance_invoice(
        session=db_session,
        task_id="t_v1",
        expected_invoice_number="INV-VERIF-TEST",
        expected_vendor="Acme Corp",
        expected_amount=75000.0,
        expected_due_date="2026-11-15"
    )
    assert v_pass.verified is True
    assert v_pass.status == "PASSED"

    # 2. Amount mismatch case
    v_fail = await IndependentVerificationEngine.verify_finance_invoice(
        session=db_session,
        task_id="t_v2",
        expected_invoice_number="INV-VERIF-TEST",
        expected_vendor="Acme Corp",
        expected_amount=99999.0,  # Mismatched amount
        expected_due_date="2026-11-15"
    )
    assert v_fail.verified is False
    assert v_fail.status == "FAILED"
    assert any("Amount mismatch" in r for r in v_fail.failure_reasons)
