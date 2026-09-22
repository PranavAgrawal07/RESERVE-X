import React, { useState } from "react";
import { FlaskConical, ArrowRight, AlertTriangle, Play } from "lucide-react";
import { api } from "../services/api";
import type { WhatIfResponse, RiskLevel } from "../types/reservex";

const riskColors: Record<RiskLevel, string> = {
  LOW: "text-emerald-400",
  MEDIUM: "text-yellow-400",
  HIGH: "text-orange-400",
  CRITICAL: "text-rose-400",
};

const riskBgColors: Record<RiskLevel, string> = {
  LOW: "bg-emerald-500/10 border-emerald-500/30",
  MEDIUM: "bg-yellow-500/10 border-yellow-500/30",
  HIGH: "bg-orange-500/10 border-orange-500/30",
  CRITICAL: "bg-rose-500/10 border-rose-500/30",
};

export const WhatIfPage: React.FC = () => {
  const [agentCount, setAgentCount] = useState(5);
  const [resourceCapacity, setResourceCapacity] = useState(2);
  const [averageProbability, setAverageProbability] = useState(0.8);
  const [result, setResult] = useState<WhatIfResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.runWhatIf({
        agent_count: agentCount,
        resource_capacity: resourceCapacity,
        average_probability: averageProbability,
      });
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to run What-If simulation");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
          <FlaskConical className="h-5 w-5 text-violet-400" />
          <span>What-If Simulator</span>
        </h2>
        <p className="text-xs text-zinc-400 mt-1">
          Run hypothetical scenarios to explore risk without affecting real
          system state.
        </p>
      </div>

      {/* Hypothetical Banner */}
      <div className="rounded-xl border border-violet-500/30 bg-violet-950/15 p-4 flex items-start gap-3">
        <AlertTriangle className="h-5 w-5 text-violet-400 shrink-0 mt-0.5" />
        <div>
          <h4 className="text-sm font-semibold text-violet-200">
            Hypothetical Analysis Only
          </h4>
          <p className="text-xs text-violet-300/80 mt-1 leading-relaxed">
            This simulator does not create options, modify resources, or affect
            the live system in any way. All results are purely hypothetical.
          </p>
        </div>
      </div>

      {/* Input Controls */}
      <div className="rounded-xl border border-zinc-800/70 bg-zinc-900/40 p-6">
        <h3 className="text-sm font-semibold text-zinc-200 mb-4 font-mono uppercase tracking-wider">
          Scenario Parameters
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Agent Count */}
          <div className="space-y-2">
            <label className="text-xs font-mono text-zinc-400 block">
              Number of Agents
            </label>
            <input
              type="range"
              min={0}
              max={20}
              value={agentCount}
              onChange={(e) => setAgentCount(Number(e.target.value))}
              className="w-full accent-violet-500"
            />
            <div className="flex justify-between text-xs font-mono">
              <span className="text-zinc-500">0</span>
              <span className="text-violet-300 text-lg font-bold">
                {agentCount}
              </span>
              <span className="text-zinc-500">20</span>
            </div>
          </div>

          {/* Resource Capacity */}
          <div className="space-y-2">
            <label className="text-xs font-mono text-zinc-400 block">
              Resource Capacity
            </label>
            <input
              type="range"
              min={0}
              max={20}
              value={resourceCapacity}
              onChange={(e) => setResourceCapacity(Number(e.target.value))}
              className="w-full accent-cyan-500"
            />
            <div className="flex justify-between text-xs font-mono">
              <span className="text-zinc-500">0</span>
              <span className="text-cyan-300 text-lg font-bold">
                {resourceCapacity}
              </span>
              <span className="text-zinc-500">20</span>
            </div>
          </div>

          {/* Average Probability */}
          <div className="space-y-2">
            <label className="text-xs font-mono text-zinc-400 block">
              Average Probability
            </label>
            <input
              type="range"
              min={0}
              max={100}
              value={Math.round(averageProbability * 100)}
              onChange={(e) =>
                setAverageProbability(Number(e.target.value) / 100)
              }
              className="w-full accent-amber-500"
            />
            <div className="flex justify-between text-xs font-mono">
              <span className="text-zinc-500">0%</span>
              <span className="text-amber-300 text-lg font-bold">
                {(averageProbability * 100).toFixed(0)}%
              </span>
              <span className="text-zinc-500">100%</span>
            </div>
          </div>
        </div>

        {/* Run Button */}
        <div className="mt-6 flex justify-center">
          <button
            onClick={runSimulation}
            disabled={loading}
            className="flex items-center gap-2 rounded-xl border border-violet-500/40 bg-violet-600/20 px-8 py-3 text-sm font-mono font-bold text-violet-200 hover:bg-violet-600/30 hover:border-violet-400/60 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-violet-950/30"
          >
            <Play
              className={`h-4 w-4 ${loading ? "animate-spin" : ""}`}
            />
            <span>{loading ? "COMPUTING..." : "RUN WHAT-IF"}</span>
          </button>
        </div>

        {error && (
          <div className="mt-4 text-center text-xs text-rose-400 font-mono">
            Error: {error}
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Side-by-Side Comparison */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Current System */}
            <div className="rounded-xl border border-zinc-800/70 bg-zinc-900/40 p-6">
              <h3 className="text-sm font-semibold text-zinc-200 mb-4 font-mono uppercase tracking-wider flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-cyan-400" />
                Current System
              </h3>
              <div className="space-y-3">
                <MetricRow
                  label="Capacity"
                  value={String(result.current.capacity)}
                  color="text-zinc-200"
                />
                <MetricRow
                  label="Pending Options"
                  value={String(result.current.pending_options ?? 0)}
                  color="text-zinc-200"
                />
                <MetricRow
                  label="Expected Demand"
                  value={result.current.expected_demand.toFixed(4)}
                  color="text-cyan-300"
                />
                <MetricRow
                  label="Overcommit Prob."
                  value={`${(result.current.overcommit_probability * 100).toFixed(2)}%`}
                  color="text-cyan-300"
                />
                <div className="flex justify-between items-center pt-2 border-t border-zinc-800/50">
                  <span className="text-xs font-mono text-zinc-400">
                    Risk Level
                  </span>
                  <span
                    className={`text-sm font-mono font-bold ${riskColors[result.current.risk_level]}`}
                  >
                    {result.current.risk_level}
                  </span>
                </div>
              </div>
            </div>

            {/* Scenario */}
            <div
              className={`rounded-xl border p-6 ${riskBgColors[result.scenario.risk_level]}`}
            >
              <h3 className="text-sm font-semibold text-zinc-200 mb-4 font-mono uppercase tracking-wider flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-violet-400" />
                What-If Scenario
                <span className="text-[10px] px-2 py-0.5 rounded-md bg-violet-500/20 text-violet-300 border border-violet-500/30 ml-auto">
                  HYPOTHETICAL
                </span>
              </h3>
              <div className="space-y-3">
                <MetricRow
                  label="Capacity"
                  value={String(result.scenario.capacity)}
                  color="text-zinc-200"
                />
                <MetricRow
                  label="Agent Count"
                  value={String(result.scenario.agent_count ?? 0)}
                  color="text-zinc-200"
                />
                <MetricRow
                  label="Expected Demand"
                  value={result.scenario.expected_demand.toFixed(4)}
                  color="text-violet-300"
                />
                <MetricRow
                  label="Overcommit Prob."
                  value={`${(result.scenario.overcommit_probability * 100).toFixed(2)}%`}
                  color="text-violet-300"
                />
                <div className="flex justify-between items-center pt-2 border-t border-zinc-800/50">
                  <span className="text-xs font-mono text-zinc-400">
                    Risk Level
                  </span>
                  <span
                    className={`text-sm font-mono font-bold ${riskColors[result.scenario.risk_level]}`}
                  >
                    {result.scenario.risk_level}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Risk Comparison Arrow */}
          <div className="rounded-xl border border-zinc-800/70 bg-zinc-900/40 p-5">
            <h3 className="text-sm font-semibold text-zinc-200 mb-4 font-mono uppercase tracking-wider">
              Risk Comparison
            </h3>
            <div className="flex items-center justify-center gap-6 py-2">
              <div className="text-center">
                <div className="text-[10px] font-mono text-zinc-500 uppercase mb-1">
                  Current
                </div>
                <div
                  className={`text-2xl font-mono font-bold ${riskColors[result.current.risk_level]}`}
                >
                  {result.current.risk_level}
                </div>
              </div>

              <ArrowRight className="h-6 w-6 text-zinc-500" />

              <div className="text-center">
                <div className="text-[10px] font-mono text-zinc-500 uppercase mb-1">
                  What-If
                </div>
                <div
                  className={`text-2xl font-mono font-bold ${riskColors[result.scenario.risk_level]}`}
                >
                  {result.scenario.risk_level}
                </div>
              </div>
            </div>

            {/* Demand comparison bar */}
            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-xs font-mono text-zinc-400">
                <span>Expected Demand</span>
                <span>
                  {result.current.expected_demand.toFixed(2)} → {result.scenario.expected_demand.toFixed(2)}
                </span>
              </div>
              <div className="flex gap-2 h-3">
                <div
                  className="bg-cyan-500/40 rounded-full transition-all duration-500"
                  style={{
                    width: `${Math.max(4, Math.min(100, (result.current.expected_demand / Math.max(result.current.expected_demand, result.scenario.expected_demand, 1)) * 100))}%`,
                  }}
                />
                <div
                  className="bg-violet-500/40 rounded-full transition-all duration-500"
                  style={{
                    width: `${Math.max(4, Math.min(100, (result.scenario.expected_demand / Math.max(result.current.expected_demand, result.scenario.expected_demand, 1)) * 100))}%`,
                  }}
                />
              </div>
              <div className="flex justify-between text-[10px] font-mono text-zinc-500">
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-cyan-500/40" />
                  Current
                </span>
                <span className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-violet-500/40" />
                  Scenario
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

/* ── Metric Row helper ───────────────────────────────────────────── */

const MetricRow: React.FC<{
  label: string;
  value: string;
  color: string;
}> = ({ label, value, color }) => (
  <div className="flex justify-between items-center">
    <span className="text-xs font-mono text-zinc-400">{label}</span>
    <span className={`text-sm font-mono font-semibold ${color}`}>{value}</span>
  </div>
);
