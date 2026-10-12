from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ErrorCategory(str, Enum):
    TRANSIENT = "TRANSIENT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    TOOL_ERROR = "TOOL_ERROR"
    BROWSER_ERROR = "BROWSER_ERROR"
    CONFLICT = "CONFLICT"
    DUPLICATE = "DUPLICATE"
    POLICY_DENIED = "POLICY_DENIED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    UNKNOWN = "UNKNOWN"


class ToolRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ToolAccessType(str, Enum):
    READ = "READ"
    WRITE = "WRITE"


class ToolExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    RETRYABLE_ERROR = "RETRYABLE_ERROR"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"


class EnterpriseToolResult(BaseModel):
    success: bool
    status: ToolExecutionStatus = ToolExecutionStatus.SUCCESS
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_category: Optional[ErrorCategory] = None
    retryable: bool = False
    action_summary: str = ""
    idempotency_key: Optional[str] = None
    verification_hint: Optional[Dict[str, Any]] = None


class ExtractedInvoiceData(BaseModel):
    vendor: str
    invoice_number: str
    invoice_date: str
    due_date: str
    amount: float
    currency: str = "INR"
    status: str = "UNPAID"
    line_items: List[Dict[str, Any]] = Field(default_factory=list)
    raw_reference: Optional[str] = None
    validation_passed: bool = True
    validation_errors: List[str] = Field(default_factory=list)
