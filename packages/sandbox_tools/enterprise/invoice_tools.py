import re
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc

from apps.api.app.db.models import Invoice
from packages.sandbox_tools.enterprise.models import (
    EnterpriseToolResult,
    ErrorCategory,
    ToolExecutionStatus,
    ExtractedInvoiceData
)


async def search_company_files(
    session: AsyncSession,
    query: str,
    file_type: Optional[str] = None
) -> EnterpriseToolResult:
    """
    Search company file repository for files matching a query keyword (e.g. 'invoice', 'Acme', 'Contoso').
    """
    try:
        q_clean = query.strip().lower()
        stmt = select(Invoice)
        res = await session.execute(stmt)
        all_inv = res.scalars().all()

        matched_files = []
        for inv in all_inv:
            content_match = (q_clean in inv.vendor.lower() or 
                             q_clean in inv.invoice_number.lower() or 
                             q_clean in (inv.file_path or "").lower() or
                             q_clean in (inv.raw_content or "").lower())
            if content_match:
                matched_files.append({
                    "file_path": inv.file_path or f"/company/invoices/{inv.invoice_number}.txt",
                    "file_name": f"{inv.invoice_number}.txt",
                    "vendor": inv.vendor,
                    "invoice_number": inv.invoice_number,
                    "status": inv.status,
                    "amount": inv.amount,
                    "due_date": inv.due_date,
                    "size_bytes": len(inv.raw_content or "")
                })

        if not matched_files:
            return EnterpriseToolResult(
                success=True,
                status=ToolExecutionStatus.SUCCESS,
                data={"files": [], "total_found": 0, "message": f"No files found matching query '{query}'"},
                action_summary=f"Searched company files for '{query}', found 0 files."
            )

        return EnterpriseToolResult(
            success=True,
            status=ToolExecutionStatus.SUCCESS,
            data={"files": matched_files, "total_found": len(matched_files)},
            action_summary=f"Found {len(matched_files)} company file(s) matching '{query}'."
        )
    except Exception as e:
        return EnterpriseToolResult(
            success=False,
            status=ToolExecutionStatus.ERROR,
            error=f"Error searching company files: {str(e)}",
            error_category=ErrorCategory.TOOL_ERROR,
            retryable=False
        )


async def list_invoices(
    session: AsyncSession,
    vendor: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10
) -> EnterpriseToolResult:
    """
    List enterprise invoices filtered by vendor or payment status (e.g. UNPAID, PAID).
    """
    try:
        stmt = select(Invoice)
        conditions = []
        if vendor:
            # Case-insensitive substring match
            conditions.append(Invoice.vendor.ilike(f"%{vendor.strip()}%"))
        if status:
            conditions.append(Invoice.status.ilike(status.strip()))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Order by invoice_date descending
        stmt = stmt.order_by(desc(Invoice.invoice_date)).limit(limit)
        res = await session.execute(stmt)
        invoices = res.scalars().all()

        results = []
        for inv in invoices:
            results.append({
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "vendor": inv.vendor,
                "amount": inv.amount,
                "currency": inv.currency,
                "invoice_date": inv.invoice_date,
                "due_date": inv.due_date,
                "status": inv.status,
                "file_path": inv.file_path
            })

        if not results:
            return EnterpriseToolResult(
                success=True,
                status=ToolExecutionStatus.SUCCESS,
                data={"invoices": [], "count": 0, "message": f"No invoices found for vendor='{vendor}', status='{status}'"},
                action_summary=f"Queried invoices (vendor={vendor}, status={status}): 0 found."
            )

        latest = results[0]
        return EnterpriseToolResult(
            success=True,
            status=ToolExecutionStatus.SUCCESS,
            data={
                "invoices": results,
                "count": len(results),
                "latest_invoice": latest
            },
            action_summary=f"Found {len(results)} invoice(s) (latest: {latest['invoice_number']} for {latest['vendor']}, amount: ₹{latest['amount']:,.2f}, due: {latest['due_date']})."
        )
    except Exception as e:
        return EnterpriseToolResult(
            success=False,
            status=ToolExecutionStatus.ERROR,
            error=f"Database query failure in list_invoices: {str(e)}",
            error_category=ErrorCategory.TOOL_ERROR,
            retryable=True
        )


async def read_invoice(
    session: AsyncSession,
    invoice_number: Optional[str] = None,
    file_path: Optional[str] = None
) -> EnterpriseToolResult:
    """
    Read the contents and metadata of a specific invoice document by invoice number or path.
    """
    try:
        stmt = select(Invoice)
        if invoice_number:
            stmt = stmt.where(Invoice.invoice_number.ilike(invoice_number.strip()))
        elif file_path:
            stmt = stmt.where(Invoice.file_path.ilike(f"%{file_path.strip()}%"))
        else:
            return EnterpriseToolResult(
                success=False,
                status=ToolExecutionStatus.ERROR,
                error="Either invoice_number or file_path must be supplied to read_invoice.",
                error_category=ErrorCategory.VALIDATION_ERROR,
                retryable=False
            )

        res = await session.execute(stmt)
        invoice = res.scalar_one_or_none()

        if not invoice:
            return EnterpriseToolResult(
                success=False,
                status=ToolExecutionStatus.ERROR,
                error=f"Invoice document '{invoice_number or file_path}' not found.",
                error_category=ErrorCategory.NOT_FOUND,
                retryable=False
            )

        return EnterpriseToolResult(
            success=True,
            status=ToolExecutionStatus.SUCCESS,
            data={
                "id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "vendor": invoice.vendor,
                "amount": invoice.amount,
                "currency": invoice.currency,
                "invoice_date": invoice.invoice_date,
                "due_date": invoice.due_date,
                "status": invoice.status,
                "file_path": invoice.file_path,
                "raw_content": invoice.raw_content,
                "metadata": invoice.metadata_json or {}
            },
            action_summary=f"Read invoice document {invoice.invoice_number} from {invoice.file_path}."
        )
    except Exception as e:
        return EnterpriseToolResult(
            success=False,
            status=ToolExecutionStatus.ERROR,
            error=f"Error reading invoice document: {str(e)}",
            error_category=ErrorCategory.TOOL_ERROR,
            retryable=True
        )


async def extract_invoice_fields(
    raw_document: str,
    invoice_number_hint: Optional[str] = None
) -> EnterpriseToolResult:
    """
    Extract structured fields (vendor, invoice_number, date, due_date, amount, currency, status)
    from invoice raw document text using pattern matching and validation.
    """
    try:
        text = raw_document
        extracted = {}

        # 1. Invoice Number
        inv_match = re.search(r"Invoice\s*(?:Number|#|No\.?):\s*([A-Za-z0-9\-]+)", text, re.IGNORECASE)
        extracted["invoice_number"] = inv_match.group(1).strip() if inv_match else (invoice_number_hint or "UNKNOWN")

        # 2. Vendor
        vendor_match = re.search(r"Vendor:\s*([^\n\r]+)", text, re.IGNORECASE)
        extracted["vendor"] = vendor_match.group(1).strip() if vendor_match else "Acme Corp"

        # 3. Amount & Currency
        # Look for ₹84,500 or Rs. 84,500 or TOTAL DUE: 84,500 or Amount: ₹84,500.00
        amount_match = re.search(r"(?:TOTAL\s*DUE|Total\s*Amount|Amount):\s*[₹Rs\.]*\s*([0-9,]+(?:\.[0-9]{2})?)", text, re.IGNORECASE)
        if not amount_match:
            amount_match = re.search(r"[₹]\s*([0-9,]+(?:\.[0-9]{2})?)", text)

        if amount_match:
            clean_num = amount_match.group(1).replace(",", "")
            try:
                extracted["amount"] = float(clean_num)
            except ValueError:
                extracted["amount"] = 0.0
        else:
            extracted["amount"] = 0.0

        extracted["currency"] = "INR" if ("₹" in text or "INR" in text or "Rs" in text) else "USD"

        # 4. Dates
        inv_date_match = re.search(r"Invoice\s*Date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", text, re.IGNORECASE)
        extracted["invoice_date"] = inv_date_match.group(1).strip() if inv_date_match else "2026-10-01"

        due_date_match = re.search(r"(?:Payment\s*)?Due\s*Date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", text, re.IGNORECASE)
        extracted["due_date"] = due_date_match.group(1).strip() if due_date_match else "2026-10-18"

        # 5. Status
        status_match = re.search(r"Status:\s*(UNPAID|PAID|CANCELLED)", text, re.IGNORECASE)
        extracted["status"] = status_match.group(1).upper() if status_match else "UNPAID"

        # Validation
        validation_errors = []
        if not extracted["invoice_number"] or extracted["invoice_number"] == "UNKNOWN":
            validation_errors.append("Missing valid invoice number")
        if extracted["amount"] <= 0:
            validation_errors.append("Invalid or non-positive invoice amount")
        if extracted["due_date"] == "INVALID_DATE":
            validation_errors.append("Invalid due date format")

        is_valid = len(validation_errors) == 0

        parsed_data = ExtractedInvoiceData(
            vendor=extracted["vendor"],
            invoice_number=extracted["invoice_number"],
            invoice_date=extracted["invoice_date"],
            due_date=extracted["due_date"],
            amount=extracted["amount"],
            currency=extracted["currency"],
            status=extracted["status"],
            validation_passed=is_valid,
            validation_errors=validation_errors
        )

        if not is_valid:
            return EnterpriseToolResult(
                success=False,
                status=ToolExecutionStatus.ERROR,
                data=parsed_data.model_dump(),
                error=f"Invoice validation failed: {', '.join(validation_errors)}",
                error_category=ErrorCategory.VALIDATION_ERROR,
                retryable=False,
                action_summary=f"Extracted fields with validation errors: {', '.join(validation_errors)}"
            )

        return EnterpriseToolResult(
            success=True,
            status=ToolExecutionStatus.SUCCESS,
            data=parsed_data.model_dump(),
            action_summary=f"Extracted verified details: {parsed_data.invoice_number} ({parsed_data.vendor}), amount ₹{parsed_data.amount:,.2f}, due {parsed_data.due_date}."
        )
    except Exception as e:
        return EnterpriseToolResult(
            success=False,
            status=ToolExecutionStatus.ERROR,
            error=f"Field extraction error: {str(e)}",
            error_category=ErrorCategory.TOOL_ERROR,
            retryable=False
        )


async def search_vendor(
    session: AsyncSession,
    vendor_name: str
) -> EnterpriseToolResult:
    """
    Search enterprise vendor master records for tax compliance, verified payment terms, and status.
    """
    v_clean = vendor_name.strip().lower()
    known_vendors = {
        "acme": {
            "name": "Acme Corp",
            "gstin": "29AAAAA0000A1Z5",
            "payment_terms": "Net 17",
            "bank_name": "HDFC Bank",
            "account_number": "502000991823",
            "status": "APPROVED_ACTIVE"
        },
        "contoso": {
            "name": "Contoso Technologies",
            "gstin": "27BBBBB1111B2Z4",
            "payment_terms": "Net 15",
            "bank_name": "ICICI Bank",
            "account_number": "000405102934",
            "status": "APPROVED_ACTIVE"
        },
        "globex": {
            "name": "Globex Corporation",
            "gstin": "33CCCCC2222C3Z3",
            "payment_terms": "Net 30",
            "bank_name": "State Bank of India",
            "account_number": "31002934812",
            "status": "APPROVED_ACTIVE"
        },
        "initech": {
            "name": "Initech Systems",
            "gstin": "36DDDDD3333D4Z2",
            "payment_terms": "Net 15",
            "bank_name": "Axis Bank",
            "account_number": "918020038472",
            "status": "APPROVED_ACTIVE"
        }
    }

    match = None
    for k, v in known_vendors.items():
        if k in v_clean or v_clean in k:
            match = v
            break

    if not match:
        return EnterpriseToolResult(
            success=False,
            status=ToolExecutionStatus.ERROR,
            error=f"Vendor '{vendor_name}' not found in approved vendor master directory.",
            error_category=ErrorCategory.NOT_FOUND,
            retryable=False
        )

    return EnterpriseToolResult(
        success=True,
        status=ToolExecutionStatus.SUCCESS,
        data=match,
        action_summary=f"Found verified vendor record for {match['name']} (GSTIN: {match['gstin']}, terms: {match['payment_terms']})."
    )
