import pytest
from httpx import AsyncClient, ASGITransport
from apps.api.app.main import app


@pytest.mark.asyncio
async def test_api_primary_invoice_task():
    """
    Integration test: Submits primary natural-language business objective
    to POST /api/v1/tasks/run and verifies autonomous execution, finance write, and verification.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/v1/tasks/run", json={
            "goal": "Find the latest unpaid invoice from Acme, extract the invoice number, amount and due date, enter it into our finance system, verify that it was saved correctly, and tell me when it is done.",
            "max_retries": 3
        })
        assert res.status_code == 200, f"Task run failed: {res.text}"
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert data["verification_results"] is not None
        assert data["verification_results"]["verified"] is True
        assert data["verification_results"]["status"] == "PASSED"
        assert data["memory"]["invoice_number"] == "INV-2026-1042"
        assert data["memory"]["amount"] == 84500.0
        assert "FIN-82914" in data["final_result"]


@pytest.mark.asyncio
async def test_api_approval_flow_pause_and_resume():
    """
    Integration test: High-value invoice triggers WAITING_APPROVAL status,
    then POST /api/v1/tasks/{task_id}/decision approves and completes execution.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Run task requiring approval
        run_res = await client.post("/api/v1/tasks/run", json={
            "goal": "Process the latest Contoso invoice, but do not enter invoices above ₹100,000 without my approval."
        })
        assert run_res.status_code == 200
        run_data = run_res.json()
        assert run_data["status"] == "WAITING_APPROVAL"
        task_id = run_data["task_id"]
        assert run_data["approval_id"] is not None

        # 2. Approve the paused task
        appr_res = await client.post(f"/api/v1/tasks/{task_id}/decision", json={
            "decision": "approve",
            "reason": "Approved by senior finance director"
        })
        assert appr_res.status_code == 200
        appr_data = appr_res.json()
        assert appr_data["status"] == "SUCCESS"
        assert appr_data["verification_results"]["verified"] is True


@pytest.mark.asyncio
async def test_api_transient_failure_and_recovery():
    """
    Integration test: Simulates transient HTTP 500 error on finance submission;
    worker classifies as TRANSIENT, retries with backoff, and succeeds.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/v1/tasks/run", json={
            "goal": "Find the latest unpaid invoice from Acme, enter into finance, and verify completion.",
            "simulate_fault": "HTTP_500"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert data["retry_count"] >= 1
        assert data["verification_results"]["verified"] is True


@pytest.mark.asyncio
async def test_api_sandbox_finance_idempotency_and_duplicate():
    """
    Integration test: Sandbox finance endpoint enforces idempotency key replay
    and duplicate invoice rejection.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        idemp_key = "idemp_api_test_99"
        # 1. First submission
        res1 = await client.post("/api/v1/sandbox/finance/records", json={
            "invoice_number": "INV-API-IDEMP-01",
            "vendor": "Acme Corp",
            "amount": 25000.0,
            "due_date": "2026-11-20",
            "idempotency_key": idemp_key
        })
        assert res1.status_code == 200
        rec_num = res1.json()["record_number"]

        # 2. Replay with identical idempotency key returns existing record (idempotent)
        res2 = await client.post("/api/v1/sandbox/finance/records", json={
            "invoice_number": "INV-API-IDEMP-01",
            "vendor": "Acme Corp",
            "amount": 25000.0,
            "due_date": "2026-11-20",
            "idempotency_key": idemp_key
        })
        assert res2.status_code == 200
        assert res2.json()["record_number"] == rec_num
        assert res2.json().get("is_idempotent_replay") is True

        # 3. Duplicate invoice number with DIFFERENT idempotency key is rejected (HTTP 409)
        res3 = await client.post("/api/v1/sandbox/finance/records", json={
            "invoice_number": "INV-API-IDEMP-01",
            "vendor": "Acme Corp",
            "amount": 25000.0,
            "due_date": "2026-11-20",
            "idempotency_key": "different_key_123"
        })
        assert res3.status_code == 409
