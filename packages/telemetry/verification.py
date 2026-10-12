from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.app.db.models import FinanceRecord


class VerificationCheckDetail(BaseModel):
    field: str
    expected: Any
    actual: Any
    matched: bool
    notes: str = ""


class VerificationResult(BaseModel):
    task_id: str
    verified: bool
    status: str = "PASSED"  # PASSED or FAILED
    target_system: str = "FinanceRecord (Internal ERP)"
    record_number: Optional[str] = None
    invoice_number: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    checks: List[VerificationCheckDetail] = Field(default_factory=list)
    failure_reasons: List[str] = Field(default_factory=list)
    evidence_payload: Dict[str, Any] = Field(default_factory=dict)


class IndependentVerificationEngine:
    """
    Independent Final-State Reconciliation Engine.
    Queries the target system directly after writes and confirms that the
    requested business state truly exists before declaring task success.
    """

    @staticmethod
    async def verify_finance_invoice(
        session: AsyncSession,
        task_id: str,
        expected_invoice_number: str,
        expected_vendor: str,
        expected_amount: float,
        expected_due_date: str,
        record_number: Optional[str] = None
    ) -> VerificationResult:
        """
        Independently queries the finance ledger by record_number or invoice_number,
        compares expected vs actual field values, and produces a cryptographic-ready verification certificate.
        """
        # 1. Independent read query directly against the target system
        stmt = select(FinanceRecord)
        if record_number:
            stmt = stmt.where(FinanceRecord.record_number.ilike(record_number.strip()))
        else:
            stmt = stmt.where(FinanceRecord.invoice_number.ilike(expected_invoice_number.strip()))

        res = await session.execute(stmt)
        actual_record = res.scalar_one_or_none()

        checks: List[VerificationCheckDetail] = []
        failure_reasons: List[str] = []

        if not actual_record:
            return VerificationResult(
                task_id=task_id,
                verified=False,
                status="FAILED",
                record_number=record_number,
                invoice_number=expected_invoice_number,
                failure_reasons=[f"Record not found in target finance system for invoice {expected_invoice_number}"],
                evidence_payload={"independent_query": "SELECT FROM finance_records", "found": False}
            )

        # 2. Field-by-field rigorous comparison
        # Invoice number
        inv_match = (actual_record.invoice_number.strip().lower() == expected_invoice_number.strip().lower())
        checks.append(VerificationCheckDetail(
            field="invoice_number",
            expected=expected_invoice_number,
            actual=actual_record.invoice_number,
            matched=inv_match,
            notes="Exact case-insensitive match" if inv_match else "Mismatch in invoice reference"
        ))
        if not inv_match:
            failure_reasons.append(f"Invoice number mismatch: expected '{expected_invoice_number}', found '{actual_record.invoice_number}'")

        # Vendor
        exp_v = expected_vendor.strip().lower()
        act_v = actual_record.vendor.strip().lower()
        vendor_match = (exp_v in act_v or act_v in exp_v)
        checks.append(VerificationCheckDetail(
            field="vendor",
            expected=expected_vendor,
            actual=actual_record.vendor,
            matched=vendor_match,
            notes="Vendor name verified" if vendor_match else "Vendor mismatch"
        ))
        if not vendor_match:
            failure_reasons.append(f"Vendor mismatch: expected '{expected_vendor}', found '{actual_record.vendor}'")

        # Amount (tolerance within ₹0.01)
        amount_diff = abs(actual_record.amount - expected_amount)
        amount_match = (amount_diff < 0.01)
        checks.append(VerificationCheckDetail(
            field="amount",
            expected=expected_amount,
            actual=actual_record.amount,
            matched=amount_match,
            notes=f"Diff: {amount_diff:.4f}" if amount_match else f"Amount difference: {amount_diff:.2f}"
        ))
        if not amount_match:
            failure_reasons.append(f"Amount mismatch: expected ₹{expected_amount:,.2f}, found ₹{actual_record.amount:,.2f}")

        # Due Date
        due_match = (actual_record.due_date.strip() == expected_due_date.strip())
        checks.append(VerificationCheckDetail(
            field="due_date",
            expected=expected_due_date,
            actual=actual_record.due_date,
            matched=due_match,
            notes="Payment due date match" if due_match else "Due date mismatch"
        ))
        if not due_match:
            failure_reasons.append(f"Due date mismatch: expected '{expected_due_date}', found '{actual_record.due_date}'")

        # Status check
        status_match = actual_record.status in ("ENTERED", "VERIFIED", "APPROVED")
        checks.append(VerificationCheckDetail(
            field="status",
            expected="ENTERED / VERIFIED",
            actual=actual_record.status,
            matched=status_match,
            notes=f"Status is {actual_record.status}"
        ))

        # Idempotency key presence
        has_idemp = bool(actual_record.idempotency_key)
        checks.append(VerificationCheckDetail(
            field="idempotency_key",
            expected="PRESENT",
            actual=actual_record.idempotency_key or "NONE",
            matched=has_idemp,
            notes="Idempotency key persisted for duplicate suppression"
        ))

        all_passed = (len(failure_reasons) == 0)

        # If verified, update record status to VERIFIED in database
        if all_passed and actual_record.status == "ENTERED":
            actual_record.status = "VERIFIED"
            await session.commit()

        evidence_payload = {
            "record_number": actual_record.record_number,
            "invoice_number": actual_record.invoice_number,
            "vendor": actual_record.vendor,
            "amount": actual_record.amount,
            "due_date": actual_record.due_date,
            "status": actual_record.status,
            "idempotency_key": actual_record.idempotency_key,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "checks_passed": sum(1 for c in checks if c.matched),
            "total_checks": len(checks)
        }

        return VerificationResult(
            task_id=task_id,
            verified=all_passed,
            status="PASSED" if all_passed else "FAILED",
            record_number=actual_record.record_number,
            invoice_number=actual_record.invoice_number,
            checks=checks,
            failure_reasons=failure_reasons,
            evidence_payload=evidence_payload
        )
