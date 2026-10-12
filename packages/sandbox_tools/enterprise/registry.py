from typing import Dict, Any, Callable, Awaitable
from packages.sandbox_tools.enterprise.models import ToolRiskLevel, ToolAccessType
from packages.sandbox_tools.enterprise.invoice_tools import (
    search_company_files,
    list_invoices,
    read_invoice,
    extract_invoice_fields,
    search_vendor
)
from packages.sandbox_tools.enterprise.finance_tools import (
    finance_find_invoice,
    finance_create_invoice,
    finance_get_invoice
)
from packages.sandbox_tools.enterprise.browser_tools import (
    browser_navigate,
    browser_type,
    browser_click,
    browser_read
)
from packages.sandbox_tools.enterprise.approval_tools import request_human_approval

ENTERPRISE_TOOL_REGISTRY: Dict[str, Callable[..., Awaitable[Any]]] = {
    "search_company_files": search_company_files,
    "list_invoices": list_invoices,
    "read_invoice": read_invoice,
    "extract_invoice_fields": extract_invoice_fields,
    "search_vendor": search_vendor,
    "finance_find_invoice": finance_find_invoice,
    "finance_create_invoice": finance_create_invoice,
    "finance_get_invoice": finance_get_invoice,
    "browser_navigate": browser_navigate,
    "browser_type": browser_type,
    "browser_click": browser_click,
    "browser_read": browser_read,
    "request_human_approval": request_human_approval
}

ENTERPRISE_TOOL_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "search_company_files": {
        "description": "Search internal company file repository by keyword, vendor name, or document reference.",
        "risk_level": ToolRiskLevel.LOW,
        "access_type": ToolAccessType.READ,
        "parameters": {
            "query": {"type": "string", "required": True, "description": "Search keyword or vendor name (e.g. 'Acme', 'invoice')"},
            "file_type": {"type": "string", "required": False, "description": "Optional file extension or type filter"}
        }
    },
    "list_invoices": {
        "description": "Query repository invoices with optional vendor or status filters (e.g. UNPAID, PAID).",
        "risk_level": ToolRiskLevel.LOW,
        "access_type": ToolAccessType.READ,
        "parameters": {
            "vendor": {"type": "string", "required": False, "description": "Vendor name filter (e.g. 'Acme', 'Contoso')"},
            "status": {"type": "string", "required": False, "description": "Invoice status filter (e.g. 'UNPAID', 'PAID')"},
            "limit": {"type": "integer", "required": False, "default": 10}
        }
    },
    "read_invoice": {
        "description": "Read the full document text, line items, and metadata for a specific invoice number or file path.",
        "risk_level": ToolRiskLevel.LOW,
        "access_type": ToolAccessType.READ,
        "parameters": {
            "invoice_number": {"type": "string", "required": False, "description": "Invoice reference number (e.g. 'INV-2026-1042')"},
            "file_path": {"type": "string", "required": False, "description": "Path to document in file repository"}
        }
    },
    "extract_invoice_fields": {
        "description": "Extract and validate structured fields (vendor, invoice_number, date, due_date, amount, currency) from raw text.",
        "risk_level": ToolRiskLevel.LOW,
        "access_type": ToolAccessType.READ,
        "parameters": {
            "raw_document": {"type": "string", "required": True, "description": "Raw text content of the invoice document"},
            "invoice_number_hint": {"type": "string", "required": False, "description": "Optional expected invoice number hint"}
        }
    },
    "search_vendor": {
        "description": "Look up vendor master record to verify tax compliance (GSTIN), approved status, and bank details.",
        "risk_level": ToolRiskLevel.LOW,
        "access_type": ToolAccessType.READ,
        "parameters": {
            "vendor_name": {"type": "string", "required": True, "description": "Vendor name to search"}
        }
    },
    "finance_find_invoice": {
        "description": "Search internal finance application to verify whether an invoice has already been entered.",
        "risk_level": ToolRiskLevel.LOW,
        "access_type": ToolAccessType.READ,
        "parameters": {
            "invoice_number": {"type": "string", "required": False, "description": "Invoice number to look up in finance records"},
            "record_number": {"type": "string", "required": False, "description": "Finance record number (e.g. 'FIN-82914')"}
        }
    },
    "finance_create_invoice": {
        "description": "Enter and submit a new invoice into the finance system with idempotency key protection.",
        "risk_level": ToolRiskLevel.HIGH,
        "access_type": ToolAccessType.WRITE,
        "parameters": {
            "invoice_number": {"type": "string", "required": True, "description": "Vendor invoice number"},
            "vendor": {"type": "string", "required": True, "description": "Vendor company name"},
            "amount": {"type": "number", "required": True, "description": "Total invoice payable amount"},
            "due_date": {"type": "string", "required": True, "description": "Payment due date (YYYY-MM-DD)"},
            "currency": {"type": "string", "required": False, "default": "INR"},
            "idempotency_key": {"type": "string", "required": False, "description": "Unique key to ensure exactly-once write execution"},
            "task_id": {"type": "string", "required": False, "description": "Task identifier for auditing and idempotency scoping"},
            "simulate_failure": {"type": "string", "required": False, "description": "Optional fault injection simulator flag"}
        }
    },
    "finance_get_invoice": {
        "description": "Independently read a finance record to verify persistence and compare stored values.",
        "risk_level": ToolRiskLevel.LOW,
        "access_type": ToolAccessType.READ,
        "parameters": {
            "record_number": {"type": "string", "required": False, "description": "Target finance record number"},
            "invoice_number": {"type": "string", "required": False, "description": "Target invoice number"}
        }
    },
    "browser_navigate": {
        "description": "Navigate Playwright browser to an internal finance or inbox portal URL.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "access_type": ToolAccessType.READ,
        "parameters": {
            "url": {"type": "string", "required": True, "description": "Target internal URL (e.g. '/sandbox/finance')"}
        }
    },
    "browser_type": {
        "description": "Type text into a designated input selector in the browser application.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "access_type": ToolAccessType.WRITE,
        "parameters": {
            "selector": {"type": "string", "required": True, "description": "CSS selector for input field"},
            "text": {"type": "string", "required": True, "description": "Value to type"}
        }
    },
    "browser_click": {
        "description": "Click a button or action element in the browser application.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "access_type": ToolAccessType.WRITE,
        "parameters": {
            "selector": {"type": "string", "required": True, "description": "CSS selector for element to click"}
        }
    },
    "browser_read": {
        "description": "Read text and DOM elements from the browser application.",
        "risk_level": ToolRiskLevel.LOW,
        "access_type": ToolAccessType.READ,
        "parameters": {
            "selector": {"type": "string", "required": False, "description": "Optional CSS selector to scope content read"}
        }
    },
    "request_human_approval": {
        "description": "Pause execution and request explicit human approval for high-value or restricted operations.",
        "risk_level": ToolRiskLevel.MEDIUM,
        "access_type": ToolAccessType.WRITE,
        "parameters": {
            "run_id": {"type": "string", "required": True, "description": "Task run identifier"},
            "action_type": {"type": "string", "required": True, "description": "Type of action requiring approval"},
            "reason": {"type": "string", "required": True, "description": "Explanation why human approval is required"},
            "proposed_payload": {"type": "object", "required": True, "description": "Details of the proposed action"}
        }
    }
}
