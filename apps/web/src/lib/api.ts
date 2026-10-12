const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// Determine if we're running in demo/offline mode (no backend configured)
export const IS_DEMO_MODE = false;

async function safeFetch(url: string, options?: RequestInit) {
  try {
    const res = await fetch(url, { ...options, cache: "no-store" });
    return res;
  } catch {
    throw new Error("BACKEND_OFFLINE");
  }
}

export async function fetchHealth() {
  if (IS_DEMO_MODE) return { status: "demo", version: "1.0.0", provider_mode: "DEMO (Mock)" };
  try {
    const res = await fetch(`${API_BASE}/health/ready`, { cache: "no-store" });
    return res.json();
  } catch {
    return { status: "offline", provider_mode: "DEMO (Mock)" };
  }
}


export async function fetchScenarios() {
  const res = await safeFetch(`${API_BASE}/api/v1/scenarios`);
  if (!res.ok) throw new Error("Failed to load scenarios");
  return res.json();
}

export async function fetchLatestBenchmark() {
  const res = await safeFetch(`${API_BASE}/api/v1/benchmarks/latest`);
  if (!res.ok) throw new Error("Failed to load benchmark metrics");
  return res.json();
}

export async function fetchReleaseGate() {
  const res = await safeFetch(`${API_BASE}/api/v1/release-gate`);
  if (!res.ok) throw new Error("Failed to load release gate");
  return res.json();
}

export async function executeAgentRun(payload: {
  scenario_id?: string;
  query?: string;
  agent_mode: string;
  provider_name?: string;
  seed: number;
  persona?: any;
}) {
  const res = await safeFetch(`${API_BASE}/api/v1/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Execution failed" }));
    throw new Error(err.detail || "Agent execution failed");
  }
  return res.json();
}

export async function fetchRunTrace(runId: string) {
  const res = await safeFetch(`${API_BASE}/api/v1/runs/${runId}/trace`);
  if (!res.ok) throw new Error(`Failed to load trace for run ${runId}`);
  return res.json();
}

export async function fetchApprovals() {
  const res = await safeFetch(`${API_BASE}/api/v1/approvals`);
  if (!res.ok) throw new Error("Failed to load approvals");
  return res.json();
}

export async function decideApproval(approvalId: string, decision: "approved" | "rejected") {
  const res = await safeFetch(`${API_BASE}/api/v1/approvals/${approvalId}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision }),
  });
  if (!res.ok) throw new Error("Approval decision failed");
  return res.json();
}

export async function fetchEvidenceReceipts() {
  const res = await safeFetch(`${API_BASE}/api/v1/evidence`);
  if (!res.ok) throw new Error("Failed to load evidence receipts");
  return res.json();
}

export async function verifyLedger() {
  const res = await safeFetch(`${API_BASE}/api/v1/evidence/verify`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Ledger verification call failed");
  return res.json();
}

export async function simulateTampering() {
  const res = await safeFetch(`${API_BASE}/api/v1/evidence/tamper-test`, {
    method: "POST",
  });
  return res.json();
}

export async function runAutonomousTask(payload: {
  goal: string;
  simulate_fault?: string | null;
  use_browser?: boolean;
  max_retries?: number;
  custom_document?: string | null;
}) {
  const res = await safeFetch(`${API_BASE}/api/v1/tasks/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Task execution failed");
  }
  return res.json();
}

export async function fetchTaskDetails(taskId: string) {
  const res = await safeFetch(`${API_BASE}/api/v1/tasks/${taskId}`);
  if (!res.ok) throw new Error("Failed to load task details");
  return res.json();
}

export async function submitTaskApprovalDecision(taskId: string, decision: "approve" | "reject", reason?: string) {
  const res = await safeFetch(`${API_BASE}/api/v1/tasks/${taskId}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, reason }),
  });
  if (!res.ok) throw new Error("Task approval decision failed");
  return res.json();
}

export async function fetchEnterpriseTasks() {
  const res = await safeFetch(`${API_BASE}/api/v1/tasks`);
  if (!res.ok) throw new Error("Failed to load tasks");
  return res.json();
}

export async function fetchFinanceRecords() {
  const res = await safeFetch(`${API_BASE}/api/v1/sandbox/finance/records`);
  if (!res.ok) throw new Error("Failed to load finance records");
  return res.json();
}

export async function fetchEnterpriseEvaluations() {
  const res = await safeFetch(`${API_BASE}/api/v1/evaluations/enterprise`);
  if (!res.ok) throw new Error("Failed to load enterprise evaluations");
  return res.json();
}

export async function runEnterpriseEvaluations() {
  const res = await safeFetch(`${API_BASE}/api/v1/evaluations/enterprise/run`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to run enterprise evaluations");
  return res.json();
}

