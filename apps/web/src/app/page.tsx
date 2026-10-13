"use client";

import React, { useState, useEffect } from "react";
import { ConsoleHeader } from "@/components/ConsoleHeader";
import { AutonomousWorkerTab } from "@/components/tabs/AutonomousWorkerTab";
import { OverviewTab } from "@/components/tabs/OverviewTab";
import { ScenarioLabTab } from "@/components/tabs/ScenarioLabTab";
import { TraceExplorerTab } from "@/components/tabs/TraceExplorerTab";
import { ApprovalInboxTab } from "@/components/tabs/ApprovalInboxTab";
import { BenchmarkTab } from "@/components/tabs/BenchmarkTab";
import { EvidenceTab } from "@/components/tabs/EvidenceTab";
import { fetchLatestBenchmark, fetchReleaseGate, fetchScenarios, fetchHealth, IS_DEMO_MODE } from "@/lib/api";

export default function ConsoleDashboard() {
  const [activeTab, setActiveTab] = useState<string>("worker");

  const [selectedRunIdForTrace, setSelectedRunIdForTrace] = useState<string | null>(null);
  const [benchmark, setBenchmark] = useState<any | null>(null);
  const [releaseGate, setReleaseGate] = useState<any | null>(null);
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [providerMode, setProviderMode] = useState<string>(IS_DEMO_MODE ? "DEMO (Mock)" : "");
  const [loading, setLoading] = useState<boolean>(true);

  const loadData = async () => {
    try {
      const [benchData, gateData, scData, healthData] = await Promise.all([
        fetchLatestBenchmark().catch(() => null),
        fetchReleaseGate().catch(() => null),
        fetchScenarios().catch(() => []),
        fetchHealth().catch(() => ({ provider_mode: "DEMO (Mock)" })),
      ]);
      setBenchmark(benchData);
      setReleaseGate(gateData);
      setScenarios(scData);
      if (healthData?.provider_mode) setProviderMode(healthData.provider_mode);
    } catch (err) {
      console.error("Dashboard data load error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleViewTrace = (runId: string) => {
    setSelectedRunIdForTrace(runId);
    setActiveTab("traces");
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#090d16] text-slate-100">
      <ConsoleHeader
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        gatePassed={releaseGate?.release_gate_passed ?? false}
        providerMode={providerMode}
      />

      {/* Demo Mode Banner — shown on Vercel when no backend is connected */}
      {IS_DEMO_MODE && (
        <div className="bg-amber-500/10 border-b border-amber-500/30 px-4 py-2 text-center text-sm text-amber-400">
          <span className="font-semibold">Live Sandbox Environment</span>
          {" — "}
          Connect a FastAPI backend to run live agent scenarios against real target ledgers.
        </div>
      )}

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "worker" && (
          <AutonomousWorkerTab />
        )}

        {activeTab === "overview" && (
          <OverviewTab
            benchmark={benchmark}
            releaseGate={releaseGate}
            onNavigateToScenarios={() => setActiveTab("scenarios")}
          />
        )}


        {activeTab === "scenarios" && (
          <ScenarioLabTab
            scenarios={scenarios}
            onViewTrace={handleViewTrace}
          />
        )}

        {activeTab === "traces" && (
          <TraceExplorerTab
            initialRunId={selectedRunIdForTrace}
          />
        )}

        {activeTab === "approvals" && (
          <ApprovalInboxTab />
        )}

        {activeTab === "benchmark" && (
          <BenchmarkTab
            benchmark={benchmark}
            releaseGate={releaseGate}
            onRefresh={loadData}
          />
        )}

        {activeTab === "evidence" && (
          <EvidenceTab />
        )}
      </main>
    </div>
  );
}
