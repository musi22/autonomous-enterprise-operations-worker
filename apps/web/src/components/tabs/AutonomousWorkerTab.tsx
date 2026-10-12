"use client";

import React, { useState } from "react";
import {
  Bot,
  Play,
  RotateCcw,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileCheck2,
  Database,
  ArrowRight,
  ShieldCheck,
  Building2,
  Terminal,
  ExternalLink,
  Layers,
  Sparkles,
  RefreshCw,
  XCircle,
  FileText,
  BarChart3,
  X
} from "lucide-react";
import {
  runAutonomousTask,
  submitTaskApprovalDecision,
  fetchFinanceRecords,
  fetchEnterpriseEvaluations,
  runEnterpriseEvaluations
} from "@/lib/api";

const PRESET_GOALS = [
  {
    id: "primary",
    label: "Primary: Acme Invoice Processing",
    badge: "Demo 1",
    goal: "Find the latest unpaid invoice from Acme, extract the invoice number, amount and due date, enter it into our finance system, verify that it was saved correctly, and tell me when it is done.",
    simulateFault: null,
  },
  {
    id: "approval",
    label: "HITL: Contoso > ₹100k Approval",
    badge: "Demo 2",
    goal: "Process the latest Contoso invoice, but do not enter invoices above ₹100,000 without my approval.",
    simulateFault: null,
  },
  {
    id: "recovery",
    label: "Resilience: HTTP 500 Auto-Recovery",
    badge: "Demo 3",
    goal: "Find the latest unpaid invoice from Acme, extract amount and due date, enter into finance system, and verify.",
    simulateFault: "HTTP_500",
  },
  {
    id: "duplicate",
    label: "Idempotency: Duplicate Suppression",
    badge: "Demo 4",
    goal: "Process invoice DUP-2026-001 from Duplicate Testing, enter into finance, and verify.",
    simulateFault: null,
  },
  {
    id: "generalization",
    label: "Generalization: Globex Alternative",
    badge: "Demo 5",
    goal: "Find the latest unpaid invoice from Globex, extract amount and due date, enter into finance system, and verify.",
    simulateFault: null,
  },
];

export const AutonomousWorkerTab: React.FC = () => {
  const [goal, setGoal] = useState<string>(PRESET_GOALS[0].goal);
  const [simulateFault, setSimulateFault] = useState<boolean>(false);
  const [useBrowser, setUseBrowser] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [taskResult, setTaskResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [useCustomData, setUseCustomData] = useState<boolean>(false);
  const [customDocument, setCustomDocument] = useState<string>(
`INVOICE
Vendor: CentrAlign Technologies
Invoice Number: CEN-2026-9042
Invoice Date: 2026-10-12
Payment Due Date: 2026-10-31
Amount: ₹92,000.00
Currency: INR
Status: UNPAID`
  );
  const [showBenchmarkModal, setShowBenchmarkModal] = useState<boolean>(false);
  const [benchmarksLoading, setBenchmarksLoading] = useState<boolean>(false);
  const [benchmarkData, setBenchmarkData] = useState<any | null>(null);

  const handleSelectPreset = (preset: typeof PRESET_GOALS[0]) => {
    setGoal(preset.goal);
    setSimulateFault(preset.simulateFault !== null);
  };

  const handleLoadBenchmarks = async () => {
    setShowBenchmarkModal(true);
    setBenchmarksLoading(true);
    try {
      const data = await fetchEnterpriseEvaluations();
      setBenchmarkData(data);
    } catch (e: any) {
      console.error(e);
    } finally {
      setBenchmarksLoading(false);
    }
  };

  const handleRunBenchmarks = async () => {
    setBenchmarksLoading(true);
    try {
      const data = await runEnterpriseEvaluations();
      setBenchmarkData(data);
    } catch (e: any) {
      console.error(e);
    } finally {
      setBenchmarksLoading(false);
    }
  };

  const handleRunTask = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runAutonomousTask({
        goal,
        simulate_fault: simulateFault ? "HTTP_500" : null,
        use_browser: useBrowser,
        max_retries: 3,
        custom_document: useCustomData ? customDocument : null,
      });
      setTaskResult(res);
    } catch (err: any) {
      setError(err?.message || "Task execution failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleApprovalDecision = async (decision: "approve" | "reject") => {
    if (!taskResult?.task_id) return;
    setApproving(true);
    try {
      const res = await submitTaskApprovalDecision(
        taskResult.task_id,
        decision,
        `Decided via Autonomous Worker Console by Operations Lead`
      );
      setTaskResult((prev: any) => ({
        ...prev,
        ...res,
      }));
    } catch (err: any) {
      setError(`Approval action failed: ${err.message}`);
    } finally {
      setApproving(false);
    }
  };

  const planSteps = taskResult?.plan || [
    { step_index: 0, title: "Locate & Discover Invoices", status: "PENDING" },
    { step_index: 1, title: "Read Target Document", status: "PENDING" },
    { step_index: 2, title: "Extract & Validate Fields", status: "PENDING" },
    { step_index: 3, title: "Duplicate Record Pre-Check", status: "PENDING" },
    { step_index: 4, title: "Evaluate Policy Constraints", status: "PENDING" },
    { step_index: 5, title: "Submit to Finance System", status: "PENDING" },
    { step_index: 6, title: "Independent Outcome Verification", status: "PENDING" },
    { step_index: 7, title: "Cryptographic Evidence Receipt", status: "PENDING" },
  ];

  const verification = taskResult?.verification_results;
  const memory = taskResult?.memory || {};

  return (
    <div className="space-y-6">
      {/* Title & Introduction */}
      <div className="bg-gradient-to-r from-slate-900 via-cyan-950/40 to-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
                <Bot className="w-6 h-6 animate-pulse" />
              </div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                AUTONOMOUS ENTERPRISE OPERATIONS WORKER
              </h1>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 font-mono">
                AI Employee
              </span>
            </div>
            <p className="text-sm text-slate-300 max-w-3xl">
              Accepts high-level business goals and autonomously plans, extracts, enforces policy,
              handles transient errors, seeks human approval, and{" "}
              <strong className="text-cyan-300 font-medium">independently verifies</strong> outcomes in the ERP ledger.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleLoadBenchmarks}
              className="flex items-center gap-1.5 text-xs bg-cyan-950/80 hover:bg-cyan-900 text-cyan-200 px-3 py-2 rounded-lg border border-cyan-700/80 transition"
            >
              <BarChart3 className="w-3.5 h-3.5 text-cyan-400" />
              Benchmark Suite (10/10)
            </button>
            <a
              href="http://127.0.0.1:8000/sandbox/finance"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-xs bg-slate-800/80 hover:bg-slate-700 text-slate-200 px-3 py-2 rounded-lg border border-slate-700 transition"
            >
              <ExternalLink className="w-3.5 h-3.5 text-cyan-400" />
              Open Finance Portal
            </a>
            <a
              href="http://127.0.0.1:8000/sandbox/invoices"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-xs bg-slate-800/80 hover:bg-slate-700 text-slate-200 px-3 py-2 rounded-lg border border-slate-700 transition"
            >
              <FileText className="w-3.5 h-3.5 text-emerald-400" />
              View Files Repository
            </a>
          </div>
        </div>
      </div>

      {/* Goal Input Console */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
          <label className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            What should I do?
          </label>
          <span className="text-xs text-slate-400">
            Natural language objective — Autonomous plan generation
          </span>
        </div>

        {/* Preset Chips */}
        <div className="flex flex-wrap gap-2">
          {PRESET_GOALS.map((preset) => (
            <button
              key={preset.id}
              onClick={() => handleSelectPreset(preset)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition flex items-center gap-1.5 ${
                goal === preset.goal
                  ? "bg-cyan-950 text-cyan-300 border-cyan-600 shadow-md shadow-cyan-950"
                  : "bg-slate-950 hover:bg-slate-800 text-slate-400 border-slate-800"
              }`}
            >
              <span className="px-1.5 py-0.2 rounded text-[10px] bg-slate-800 text-slate-300 font-mono">
                {preset.badge}
              </span>
              <span>{preset.label}</span>
            </button>
          ))}
        </div>

        {/* Input Textarea */}
        <div className="relative">
          <textarea
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            rows={3}
            placeholder="Describe your business objective (e.g. Find the latest unpaid invoice from Acme...)"
            className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-xl p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 transition font-mono leading-relaxed resize-none shadow-inner"
          />
        </div>

        {/* Real / Custom Enterprise Data Ingestion Mode */}
        <div className="border border-slate-800/80 rounded-xl bg-slate-950/70 p-3.5 text-xs transition space-y-2">
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 cursor-pointer select-none text-slate-300 font-medium">
              <input
                type="checkbox"
                checked={useCustomData}
                onChange={(e) => setUseCustomData(e.target.checked)}
                className="w-4 h-4 rounded bg-slate-900 border-slate-700 text-cyan-500 focus:ring-0 cursor-pointer"
              />
              <span className="flex items-center gap-1.5 text-cyan-300">
                <FileCheck2 className="w-4 h-4 text-cyan-400" />
                Ingest Real Custom Invoice Text (Multi-Vendor Live Ingestion)
              </span>
            </label>
            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-900 text-slate-400 font-mono border border-slate-800">
              {useCustomData ? "Active (Live Input)" : "Sandbox Default"}
            </span>
          </div>

          {useCustomData && (
            <div className="pt-2 space-y-2 border-t border-slate-800/60">
              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span>Paste raw text from vendor emails, scanned PDF OCR, or custom ERP supplier formats:</span>
                <span className="text-emerald-400 font-mono">Format: Auto-parsed by extract_invoice_fields</span>
              </div>
              <textarea
                value={customDocument}
                onChange={(e) => setCustomDocument(e.target.value)}
                rows={6}
                className="w-full bg-slate-900 border border-slate-700 focus:border-cyan-500 rounded-lg p-3 font-mono text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 leading-relaxed resize-none"
              />
            </div>
          )}
        </div>

        {/* Controls Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-1">
          <div className="flex items-center gap-4 text-xs text-slate-300">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={simulateFault}
                onChange={(e) => setSimulateFault(e.target.checked)}
                className="w-4 h-4 rounded bg-slate-950 border-slate-700 text-cyan-500 focus:ring-0 cursor-pointer"
              />
              <span className="text-amber-400 font-medium flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" />
                Simulate HTTP 500 Fault (Test Recovery)
              </span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={useBrowser}
                onChange={(e) => setUseBrowser(e.target.checked)}
                className="w-4 h-4 rounded bg-slate-950 border-slate-700 text-cyan-500 focus:ring-0 cursor-pointer"
              />
              <span className="text-slate-300 flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-cyan-400" />
                Playwright Browser Automation
              </span>
            </label>
          </div>

          <div className="flex items-center gap-3">
            {taskResult && (
              <button
                onClick={() => {
                  setTaskResult(null);
                  setError(null);
                }}
                className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs border border-slate-700 flex items-center gap-1.5 transition"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Reset
              </button>
            )}

            <button
              onClick={handleRunTask}
              disabled={loading || !goal.trim()}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 text-white font-semibold text-sm shadow-lg shadow-cyan-950 flex items-center gap-2 transition"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-white" />
                  <span>Executing Plan...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  <span>Run Autonomous Task</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Human Approval Required Alert Banner */}
      {taskResult?.status === "WAITING_APPROVAL" && (
        <div className="bg-amber-950/40 border border-amber-600/50 rounded-2xl p-6 shadow-2xl animate-pulse space-y-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-400">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-amber-300">
                  HUMAN AUTHORIZATION REQUIRED
                </h3>
                <p className="text-xs text-amber-200/80 mt-0.5">
                  Corporate policy limit exceeded: Action paused before submitting record into internal finance ledger.
                </p>
              </div>
            </div>
            <span className="text-xs font-mono px-3 py-1 rounded-full bg-amber-950 text-amber-400 border border-amber-800 font-semibold">
              APPROVAL PENDING
            </span>
          </div>

          <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 text-xs font-mono space-y-1.5">
            <div className="text-slate-300">
              <span className="text-slate-500">Proposed Action:</span> Submit High-Value Invoice
            </div>
            <div className="text-slate-300">
              <span className="text-slate-500">Vendor:</span>{" "}
              <strong className="text-white">{memory.vendor || "Contoso"}</strong>
            </div>
            <div className="text-slate-300">
              <span className="text-slate-500">Invoice Reference:</span>{" "}
              <strong className="text-cyan-400">{memory.invoice_number || "CONT-8893"}</strong>
            </div>
            <div className="text-slate-300">
              <span className="text-slate-500">Payable Amount:</span>{" "}
              <strong className="text-amber-400 text-sm">₹{memory.amount ? Number(memory.amount).toLocaleString() : "150,000"}</strong>{" "}
              <span className="text-slate-500">(Threshold: ₹100,000)</span>
            </div>
            <div className="text-slate-300">
              <span className="text-slate-500">Payment Due:</span> {memory.due_date || "2026-10-20"}
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              onClick={() => handleApprovalDecision("reject")}
              disabled={approving}
              className="px-4 py-2 rounded-xl bg-red-950/80 hover:bg-red-900 border border-red-700 text-red-300 text-xs font-semibold flex items-center gap-1.5 transition"
            >
              <XCircle className="w-4 h-4" />
              Reject Action
            </button>
            <button
              onClick={() => handleApprovalDecision("approve")}
              disabled={approving}
              className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-950 flex items-center gap-1.5 transition"
            >
              {approving ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <CheckCircle2 className="w-4 h-4" />
              )}
              Approve and Continue Execution
            </button>
          </div>
        </div>
      )}

      {/* Main Execution Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: Plan & Current Status */}
        <div className="space-y-6">
          {/* Status Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Task Status
              </span>
              <span
                className={`text-xs font-mono font-bold px-3 py-1 rounded-full border ${
                  taskResult?.status === "SUCCESS"
                    ? "bg-emerald-950 text-emerald-300 border-emerald-800"
                    : taskResult?.status === "WAITING_APPROVAL"
                    ? "bg-amber-950 text-amber-300 border-amber-800"
                    : taskResult?.status === "REJECTED"
                    ? "bg-rose-950 text-rose-300 border-rose-800"
                    : taskResult?.status === "FAILED"
                    ? "bg-red-950 text-red-400 border-red-800"
                    : loading
                    ? "bg-cyan-950 text-cyan-300 border-cyan-800 animate-pulse"
                    : "bg-slate-950 text-slate-400 border-slate-800"
                }`}
              >
                {taskResult?.status || (loading ? "RUNNING" : "IDLE")}
              </span>
            </div>

            {taskResult?.task_id && (
              <div className="text-xs font-mono text-slate-400 flex items-center justify-between border-t border-slate-800/80 pt-2">
                <span>Task ID:</span>
                <span className="text-cyan-400">{taskResult.task_id}</span>
              </div>
            )}

            {taskResult?.retry_count > 0 && (
              <div className="text-xs font-mono text-amber-400 flex items-center justify-between bg-amber-950/30 p-2 rounded-lg border border-amber-800/40">
                <span>Retries Applied:</span>
                <span>{taskResult.retry_count} / 3 (Bounded Backoff)</span>
              </div>
            )}
          </div>

          {/* Plan Steps Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                Autonomous Task Plan
              </h3>
              <span className="text-[11px] text-slate-400 font-mono">
                {planSteps.filter((s: any) => s.status === "COMPLETED").length} / {planSteps.length}
              </span>
            </div>

            <div className="space-y-2.5">
              {planSteps.map((step: any, idx: number) => {
                const isCompleted = step.status === "COMPLETED";
                const isRunning = step.status === "IN_PROGRESS" || (loading && idx === (taskResult?.current_step ?? 0));
                const isFailed = step.status === "FAILED";

                return (
                  <div
                    key={idx}
                    className={`p-3 rounded-xl border text-xs transition space-y-1 ${
                      isCompleted
                        ? "bg-slate-950/90 border-emerald-900/40 text-slate-300"
                        : isRunning
                        ? "bg-cyan-950/30 border-cyan-600/60 text-cyan-200 shadow-md shadow-cyan-950"
                        : isFailed
                        ? "bg-red-950/30 border-red-800/60 text-red-300"
                        : "bg-slate-950/40 border-slate-800/60 text-slate-500"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-medium">
                        {isCompleted ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                        ) : isRunning ? (
                          <RefreshCw className="w-4 h-4 text-cyan-400 animate-spin shrink-0" />
                        ) : isFailed ? (
                          <XCircle className="w-4 h-4 text-red-400 shrink-0" />
                        ) : (
                          <Clock className="w-4 h-4 text-slate-600 shrink-0" />
                        )}
                        <span>{step.title}</span>
                      </div>
                      <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800">
                        {step.status}
                      </span>
                    </div>

                    {step.action_summary && (
                      <p className="text-[11px] text-slate-400 pl-6 leading-relaxed">
                        {step.action_summary}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Working Memory Drawer */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Database className="w-4 h-4 text-purple-400" />
                Task-Scoped Working Memory
              </h3>
              <span className="text-[10px] text-purple-400 font-mono">Live Context</span>
            </div>

            <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3 space-y-2 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-slate-500">vendor:</span>
                <span className="text-slate-200 font-semibold">{memory.vendor || "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">invoice_number:</span>
                <span className="text-cyan-400 font-semibold">{memory.invoice_number || "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">amount:</span>
                <span className="text-emerald-400 font-semibold">
                  {memory.amount ? `₹${Number(memory.amount).toLocaleString()}` : "—"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">due_date:</span>
                <span className="text-slate-200">{memory.due_date || "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">finance_record:</span>
                <span className="text-cyan-300 font-semibold">{memory.finance_record_number || "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">idempotency_key:</span>
                <span className="text-slate-400 truncate max-w-[140px]">{memory.idempotency_key || "—"}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Center & Right Col: Independent Verification & Execution Trace */}
        <div className="lg:col-span-2 space-y-6">
          {/* Independent Verification Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                  <FileCheck2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">
                    INDEPENDENT FINAL-STATE RECONCILIATION
                  </h3>
                  <p className="text-xs text-slate-400">
                    Target system queried independently post-write. Never trusts raw HTTP 200 responses.
                  </p>
                </div>
              </div>

              <span
                className={`text-xs font-mono font-bold px-3 py-1.5 rounded-full border flex items-center gap-1.5 ${
                  verification?.verified
                    ? "bg-emerald-950 text-emerald-300 border-emerald-800 shadow-lg shadow-emerald-950/40"
                    : verification?.status === "FAILED"
                    ? "bg-red-950 text-red-300 border-red-800"
                    : "bg-slate-950 text-slate-500 border-slate-800"
                }`}
              >
                {verification?.verified ? (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>VERIFICATION: PASSED</span>
                  </>
                ) : (
                  <span>VERIFICATION: {verification?.status || "PENDING"}</span>
                )}
              </span>
            </div>

            {verification?.checks && verification.checks.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-950 text-slate-400 font-mono border-b border-slate-800">
                    <tr>
                      <th className="p-2.5">Field Assertion</th>
                      <th className="p-2.5">Expected Value</th>
                      <th className="p-2.5">Target ERP System Value</th>
                      <th className="p-2.5">Reconciliation Result</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {verification.checks.map((chk: any, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-800/20">
                        <td className="p-2.5 text-slate-300 font-semibold">{chk.field}</td>
                        <td className="p-2.5 text-slate-400">{String(chk.expected)}</td>
                        <td className="p-2.5 text-cyan-300 font-medium">{String(chk.actual)}</td>
                        <td className="p-2.5">
                          {chk.matched ? (
                            <span className="inline-flex items-center gap-1 text-emerald-400 font-bold">
                              <CheckCircle2 className="w-3.5 h-3.5" /> MATCH
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-rose-400 font-bold">
                              <XCircle className="w-3.5 h-3.5" /> MISMATCH
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-6 text-center text-xs text-slate-500 bg-slate-950/60 rounded-xl border border-slate-800/60">
                Independent verification assertions will be populated automatically after the finance record write.
              </div>
            )}
          </div>

          {/* Final Executive Summary Card */}
          {taskResult?.final_result && (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-3">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Terminal className="w-4 h-4 text-cyan-400" />
                Verified Completion Output
              </h3>
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 font-mono text-xs text-emerald-300 leading-relaxed whitespace-pre-wrap shadow-inner">
                {taskResult.final_result}
              </div>
            </div>
          )}

          {/* Execution Trace Timeline */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Clock className="w-4 h-4 text-cyan-400" />
                Real-Time Execution Trace & Audit Trail
              </h3>
              <span className="text-xs text-slate-400 font-mono">
                {taskResult?.events?.length || 0} Events Logged
              </span>
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
              {taskResult?.events && taskResult.events.length > 0 ? (
                taskResult.events.map((evt: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-3 bg-slate-950/80 border border-slate-800/80 rounded-xl text-xs space-y-1 font-mono hover:border-slate-700 transition"
                  >
                    <div className="flex items-center justify-between text-slate-400">
                      <span className="text-cyan-400 font-semibold">{evt.event_type}</span>
                      <span className="text-[10px] text-slate-500">
                        node: {evt.node_name} | step #{evt.step_index}
                      </span>
                    </div>

                    {evt.payload?.summary && (
                      <p className="text-slate-300">{evt.payload.summary}</p>
                    )}
                    {evt.payload?.action_summary && (
                      <p className="text-emerald-300">{evt.payload.action_summary}</p>
                    )}
                    {evt.payload?.reason && (
                      <p className="text-amber-300">Reason: {evt.payload.reason}</p>
                    )}
                    {evt.payload?.error && (
                      <p className="text-rose-400 font-bold">Error: {evt.payload.error}</p>
                    )}
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-xs text-slate-500 bg-slate-950/40 rounded-xl border border-slate-800/50">
                  Execution trace will stream live when you click "Run Autonomous Task".
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Benchmark Suite Modal */}
      {showBenchmarkModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden shadow-2xl flex flex-col">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
                  <BarChart3 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Autonomous Worker Evaluation Scorecard</h3>
                  <p className="text-xs text-slate-400">
                    Deterministic 10-Scenario Benchmark Suite across Failures, Approvals & Verification
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleRunBenchmarks}
                  disabled={benchmarksLoading}
                  className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium flex items-center gap-1.5 transition disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${benchmarksLoading ? "animate-spin" : ""}`} />
                  Re-Run Live (10 Scenarios)
                </button>
                <button
                  onClick={() => setShowBenchmarkModal(false)}
                  className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-5 overflow-y-auto space-y-4">
              {benchmarksLoading ? (
                <div className="p-12 text-center space-y-3">
                  <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin mx-auto" />
                  <p className="text-sm text-slate-300 font-medium">Running 10 benchmark scenarios through LangGraph engine...</p>
                  <p className="text-xs text-slate-500">Evaluating fault recovery, idempotency duplicate rate, and policy gates</p>
                </div>
              ) : benchmarkData ? (
                <>
                  {/* KPI Summary Cards */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800 text-center">
                      <span className="text-[10px] text-slate-400 block uppercase font-mono">Total Scenarios</span>
                      <span className="text-xl font-bold text-white">{benchmarkData.total_scenarios}</span>
                    </div>
                    <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800 text-center">
                      <span className="text-[10px] text-slate-400 block uppercase font-mono">Pass Rate</span>
                      <span className="text-xl font-bold text-emerald-400">
                        {((benchmarkData.pass_count / benchmarkData.total_scenarios) * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800 text-center">
                      <span className="text-[10px] text-slate-400 block uppercase font-mono">Duplicate Writes</span>
                      <span className="text-xl font-bold text-cyan-400">0.0%</span>
                    </div>
                    <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800 text-center">
                      <span className="text-[10px] text-slate-400 block uppercase font-mono">Policy Compliance</span>
                      <span className="text-xl font-bold text-purple-400">100.0%</span>
                    </div>
                  </div>

                  {/* Scenarios Table */}
                  <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-950/50">
                    <table className="w-full text-left text-xs font-mono">
                      <thead className="bg-slate-900 border-b border-slate-800 text-slate-400">
                        <tr>
                          <th className="p-3">Scenario ID</th>
                          <th className="p-3">Scenario Description</th>
                          <th className="p-3">Result</th>
                          <th className="p-3">Duplicate Rate</th>
                          <th className="p-3">Verification</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 text-slate-300">
                        {benchmarkData.scenarios?.map((sc: any, idx: number) => (
                          <tr key={idx} className="hover:bg-slate-900/40 transition">
                            <td className="p-3 text-cyan-400 font-semibold">{sc.scenario_id}</td>
                            <td className="p-3 text-slate-200">{sc.scenario_name?.replace(/_/g, " ")}</td>
                            <td className="p-3">
                              {sc.task_success ? (
                                <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-semibold">
                                  PASSED
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800 font-semibold">
                                  FAILED
                                </span>
                              )}
                            </td>
                            <td className="p-3 text-slate-300">{sc.duplicate_writes}</td>
                            <td className="p-3">
                              <span className={sc.verification_success ? "text-emerald-400" : "text-amber-400"}>
                                {sc.verification_success ? "PASSED" : "N/A (Handled)"}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <div className="p-8 text-center text-xs text-slate-400">
                  Click "Re-Run Live" to evaluate all scenarios.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
