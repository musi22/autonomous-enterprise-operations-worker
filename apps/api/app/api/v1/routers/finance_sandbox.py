from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from apps.api.app.db.database import get_db
from apps.api.app.db.models import Invoice, FinanceRecord, generate_uuid
from packages.sandbox_tools.enterprise.finance_tools import generate_finance_record_number

router = APIRouter(tags=["Enterprise Sandbox"])


class CreateFinanceRecordRequest(BaseModel):
    invoice_number: str
    vendor: str
    amount: float
    due_date: str
    currency: str = "INR"
    idempotency_key: Optional[str] = None
    task_id: Optional[str] = None


# --- HTML Web App Endpoints for Playwright Browser Interaction ---

@router.get("/sandbox/finance", response_class=HTMLResponse)
async def get_finance_portal_html(
    db: AsyncSession = Depends(get_db),
    fail_500: bool = False
):
    """
    Simulated internal company Finance Web Application.
    Supports form submission, invoice lookup, and deterministic failure injection.
    """
    stmt = select(FinanceRecord).order_by(desc(FinanceRecord.created_at)).limit(10)
    res = await db.execute(stmt)
    records = res.scalars().all()

    rows_html = "".join([
        f"""<tr class="border-b border-slate-700/50 hover:bg-slate-800/40">
            <td class="p-3 font-mono text-cyan-400 font-semibold">{rec.record_number}</td>
            <td class="p-3 font-mono text-slate-300">{rec.invoice_number}</td>
            <td class="p-3 text-slate-200">{rec.vendor}</td>
            <td class="p-3 font-medium text-emerald-400">₹{rec.amount:,.2f}</td>
            <td class="p-3 text-slate-300">{rec.due_date}</td>
            <td class="p-3"><span class="px-2 py-1 text-xs rounded bg-emerald-950 text-emerald-300 border border-emerald-800">{rec.status}</span></td>
        </tr>""" for rec in records
    ])

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enterprise Finance Operations Portal</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen p-6 font-sans">
    <div class="max-w-6xl mx-auto space-y-6">
        <header class="border-b border-slate-800 pb-4 flex justify-between items-center">
            <div>
                <h1 class="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                    <span class="text-cyan-400">⚡</span> Internal Finance Operations Portal
                </h1>
                <p class="text-sm text-slate-400 mt-1">Simulated corporate ERP system for invoice ingestion and payments reconciliation.</p>
            </div>
            <div class="flex items-center gap-3">
                <span class="px-3 py-1 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">System Online</span>
                <span class="text-xs text-slate-500 font-mono">v3.4-prod-sandbox</span>
            </div>
        </header>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Left: Entry Form -->
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
                <h2 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <span>📝</span> Record New Invoice
                </h2>
                <form id="finance_form" onsubmit="handleFormSubmit(event)" class="space-y-4">
                    <div>
                        <label class="block text-xs font-medium text-slate-400 mb-1">Invoice Number *</label>
                        <input id="invoice_number" name="invoice_number" type="text" required placeholder="e.g. INV-2026-1042"
                            class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-400 mb-1">Vendor Name *</label>
                        <input id="vendor" name="vendor" type="text" required placeholder="e.g. Acme Corp"
                            class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-400 mb-1">Amount (INR ₹) *</label>
                        <input id="amount" name="amount" type="number" step="0.01" required placeholder="84500"
                            class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-400 mb-1">Payment Due Date *</label>
                        <input id="due_date" name="due_date" type="text" required placeholder="YYYY-MM-DD"
                            class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-400 mb-1">Idempotency Key (Auto-generated)</label>
                        <input id="idempotency_key" name="idempotency_key" type="text" placeholder="idemp_key_..."
                            class="w-full bg-slate-950/60 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-slate-400">
                    </div>

                    <div class="pt-2">
                        <button id="submit_btn" type="submit"
                            class="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-medium py-2.5 px-4 rounded-lg text-sm transition-colors shadow-lg shadow-cyan-950">
                            Submit to Finance System
                        </button>
                    </div>
                </form>

                <div id="status_message" class="hidden mt-4 p-3 rounded-lg text-sm"></div>
                <div id="created_record_banner" class="hidden mt-3 p-3 bg-emerald-950/60 border border-emerald-800 rounded-lg text-emerald-300 text-sm">
                    Record Created: <span id="created_record_id" class="font-mono font-bold text-emerald-400"></span>
                </div>
            </div>

            <!-- Right: Existing Records -->
            <div class="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-lg font-semibold text-white flex items-center gap-2">
                        <span>📊</span> Recent Finance Records
                    </h2>
                    <span class="text-xs text-slate-400">Auto-refreshing</span>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-slate-950 text-xs text-slate-400 uppercase font-mono border-b border-slate-800">
                            <tr>
                                <th class="p-3">Record ID</th>
                                <th class="p-3">Invoice #</th>
                                <th class="p-3">Vendor</th>
                                <th class="p-3">Amount</th>
                                <th class="p-3">Due Date</th>
                                <th class="p-3">Status</th>
                            </tr>
                        </thead>
                        <tbody id="records_table">
                            {rows_html if rows_html else '<tr><td colspan="6" class="p-4 text-center text-slate-500">No records found.</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function handleFormSubmit(e) {{
            e.preventDefault();
            const invNum = document.getElementById('invoice_number').value.trim();
            const vendor = document.getElementById('vendor').value.trim();
            const amount = parseFloat(document.getElementById('amount').value);
            const dueDate = document.getElementById('due_date').value.trim();
            let idempKey = document.getElementById('idempotency_key').value.trim();
            if (!idempKey) {{
                idempKey = 'browser_' + invNum + '_' + Date.now();
                document.getElementById('idempotency_key').value = idempKey;
            }}

            const statusEl = document.getElementById('status_message');
            const bannerEl = document.getElementById('created_record_banner');
            const recordIdEl = document.getElementById('created_record_id');
            const submitBtn = document.getElementById('submit_btn');

            submitBtn.disabled = true;
            submitBtn.innerText = 'Submitting...';

            try {{
                const res = await fetch('/api/v1/sandbox/finance/records', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        invoice_number: invNum,
                        vendor: vendor,
                        amount: amount,
                        due_date: dueDate,
                        idempotency_key: idempKey
                    }})
                }});

                const data = await res.json();
                if (res.ok) {{
                    statusEl.className = 'mt-4 p-3 rounded-lg text-sm bg-emerald-950/80 border border-emerald-800 text-emerald-300 block';
                    statusEl.innerText = '✓ Invoice successfully ingested into finance ledger.';
                    bannerEl.classList.remove('hidden');
                    recordIdEl.innerText = data.record_number;
                    setTimeout(() => window.location.reload(), 1500);
                }} else {{
                    statusEl.className = 'mt-4 p-3 rounded-lg text-sm bg-red-950/80 border border-red-800 text-red-300 block';
                    statusEl.innerText = '✗ Error: ' + (data.detail || 'Submission failed');
                }}
            }} catch (err) {{
                statusEl.className = 'mt-4 p-3 rounded-lg text-sm bg-red-950/80 border border-red-800 text-red-300 block';
                statusEl.innerText = '✗ Network / Server connection error.';
            }} finally {{
                submitBtn.disabled = false;
                submitBtn.innerText = 'Submit to Finance System';
            }}
        }}
    </script>
</body>
</html>"""
    return HTMLContent(html_content)


def HTMLContent(content: str) -> HTMLResponse:
    return HTMLResponse(content=content)


@router.get("/sandbox/invoices", response_class=HTMLResponse)
async def get_invoices_repository_html(db: AsyncSession = Depends(get_db)):
    """
    HTML view of simulated company invoices repository.
    """
    stmt = select(Invoice).order_by(desc(Invoice.invoice_date))
    res = await db.execute(stmt)
    invoices = res.scalars().all()

    cards = "".join([
        f"""<div class="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-2">
            <div class="flex justify-between items-start">
                <span class="font-mono text-cyan-400 font-bold text-base">{inv.invoice_number}</span>
                <span class="text-xs px-2 py-0.5 rounded {'bg-amber-950 text-amber-300 border border-amber-800' if inv.status == 'UNPAID' else 'bg-slate-800 text-slate-400'}">{inv.status}</span>
            </div>
            <div class="text-sm font-medium text-slate-200">{inv.vendor}</div>
            <div class="text-xs text-slate-400">Amount: <span class="text-emerald-400 font-semibold">₹{inv.amount:,.2f}</span></div>
            <div class="text-xs text-slate-500">Date: {inv.invoice_date} | Due: {inv.due_date}</div>
            <div class="text-xs font-mono text-slate-500 truncate">{inv.file_path}</div>
        </div>""" for inv in invoices
    ])

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Company Invoices Repository</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 p-6 min-h-screen">
    <div class="max-w-5xl mx-auto space-y-6">
        <header class="border-b border-slate-800 pb-3">
            <h1 class="text-xl font-bold text-white">📁 Corporate Invoices & Files Repository</h1>
            <p class="text-xs text-slate-400">Simulated vendor invoice document repository</p>
        </header>
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {cards}
        </div>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html)


# --- REST API Endpoints ---

@router.get("/api/v1/sandbox/invoices")
async def list_sandbox_invoices(
    vendor: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Invoice)
    if vendor:
        stmt = stmt.where(Invoice.vendor.ilike(f"%{vendor.strip()}%"))
    if status:
        stmt = stmt.where(Invoice.status.ilike(status.strip()))
    stmt = stmt.order_by(desc(Invoice.invoice_date))
    res = await db.execute(stmt)
    invoices = res.scalars().all()
    return [{
        "invoice_number": inv.invoice_number,
        "vendor": inv.vendor,
        "amount": inv.amount,
        "currency": inv.currency,
        "invoice_date": inv.invoice_date,
        "due_date": inv.due_date,
        "status": inv.status,
        "file_path": inv.file_path
    } for inv in invoices]


@router.get("/api/v1/sandbox/finance/records")
async def list_finance_records(db: AsyncSession = Depends(get_db)):
    stmt = select(FinanceRecord).order_by(desc(FinanceRecord.created_at))
    res = await db.execute(stmt)
    records = res.scalars().all()
    return [{
        "record_number": r.record_number,
        "invoice_number": r.invoice_number,
        "vendor": r.vendor,
        "amount": r.amount,
        "currency": r.currency,
        "due_date": r.due_date,
        "status": r.status,
        "idempotency_key": r.idempotency_key,
        "created_at": r.created_at.isoformat() if r.created_at else None
    } for r in records]


@router.post("/api/v1/sandbox/finance/records")
async def create_finance_record_api(
    req: CreateFinanceRecordRequest,
    x_simulate_fault: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    # Fault injection check
    if x_simulate_fault == "HTTP_500":
        raise HTTPException(status_code=500, detail="Database lock timeout on record ingestion (HTTP 500)")

    eff_key = req.idempotency_key or f"api_{req.invoice_number}_{req.amount}"

    # 1. Check idempotency key
    stmt_key = select(FinanceRecord).where(FinanceRecord.idempotency_key == eff_key)
    res_key = await db.execute(stmt_key)
    existing_key = res_key.scalar_one_or_none()
    if existing_key:
        return {
            "record_number": existing_key.record_number,
            "invoice_number": existing_key.invoice_number,
            "vendor": existing_key.vendor,
            "amount": existing_key.amount,
            "currency": existing_key.currency,
            "due_date": existing_key.due_date,
            "status": existing_key.status,
            "is_idempotent_replay": True
        }

    # 2. Check duplicate invoice number
    stmt_inv = select(FinanceRecord).where(FinanceRecord.invoice_number.ilike(req.invoice_number.strip()))
    res_inv = await db.execute(stmt_inv)
    existing_inv = res_inv.scalar_one_or_none()
    if existing_inv:
        raise HTTPException(
            status_code=409,
            detail=f"Duplicate invoice: {req.invoice_number} already recorded as {existing_inv.record_number}"
        )

    # 3. Create record
    rec_num = generate_finance_record_number(req.invoice_number)
    record = FinanceRecord(
        id=generate_uuid(),
        record_number=rec_num,
        invoice_number=req.invoice_number,
        vendor=req.vendor,
        amount=req.amount,
        currency=req.currency,
        due_date=req.due_date,
        status="ENTERED",
        idempotency_key=eff_key,
        source="api",
        task_id=req.task_id
    )
    db.add(record)
    await db.commit()

    return {
        "record_number": record.record_number,
        "invoice_number": record.invoice_number,
        "vendor": record.vendor,
        "amount": record.amount,
        "currency": record.currency,
        "due_date": record.due_date,
        "status": record.status,
        "idempotency_key": eff_key
    }


@router.get("/api/v1/sandbox/finance/records/{record_number}")
async def get_finance_record_api(
    record_number: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(FinanceRecord).where(FinanceRecord.record_number.ilike(record_number.strip()))
    res = await db.execute(stmt)
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Finance record '{record_number}' not found.")
    return {
        "record_number": rec.record_number,
        "invoice_number": rec.invoice_number,
        "vendor": rec.vendor,
        "amount": rec.amount,
        "currency": rec.currency,
        "due_date": rec.due_date,
        "status": rec.status,
        "idempotency_key": rec.idempotency_key,
        "created_at": rec.created_at.isoformat() if rec.created_at else None
    }
