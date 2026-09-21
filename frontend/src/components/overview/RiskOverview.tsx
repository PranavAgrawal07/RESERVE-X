import React from "react";
import { ShieldAlert, ArrowRight, AlertTriangle } from "lucide-react";
import { Card } from "../common/Card";
import { Badge, RiskBadge } from "../common/Badge";
import { useReserveX } from "../../context/ReserveXContext";

interface RiskOverviewProps {
  onNavigateToRisk: () => void;
}

export const RiskOverview: React.FC<RiskOverviewProps> = ({
  onNavigateToRisk,
}) => {
  const { risk, options, allocations } = useReserveX();

  const highestRisk = risk?.highest_risk_level || "LOW";
  const pendingOptions = options.filter((o) => o.status === "PENDING").length;
  const activeAllocations = allocations.filter((a) => !a.released_at).length;

  // Aggregate expected demand across capabilities
  const totalExpectedDemand = (risk?.capability_risks || []).reduce(
    (acc, c) => acc + c.expected_demand,
    0
  );
  const totalAvailableCapacity = (risk?.capability_risks || []).reduce(
    (acc, c) => acc + c.available_capacity,
    0
  );
  const maxOvercommitProbability =
    (risk?.capability_risks || []).length > 0
      ? Math.max(...(risk?.capability_risks || []).map((c) => c.overcommit_probability))
      : 0;

  return (
    <Card
      title={
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-orange-400" />
          <span>Probabilistic Risk & Contention Status</span>
        </div>
      }
      subtitle="Evaluates 2^n simultaneous exercise subsets to quantify over-commitment risk"
      action={
        <button
          onClick={onNavigateToRisk}
          className="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors"
        >
          <span>Deep Analysis</span>
          <ArrowRight className="h-3 w-3" />
        </button>
      }
    >
      {/* High Risk Warning Banner if system is in HIGH or CRITICAL */}
      {(highestRisk === "HIGH" || highestRisk === "CRITICAL") && (
        <div className="mb-4 rounded-xl border border-orange-500/40 bg-orange-950/20 p-3.5 flex items-start gap-3">
          <AlertTriangle className="h-4 w-4 text-orange-400 shrink-0 mt-0.5" />
          <div className="text-xs text-orange-200">
            <span className="font-semibold text-orange-100">
              Contention Alert:
            </span>{" "}
            Simultaneous exercise of pending options has a{" "}
            <strong>{Math.round(maxOvercommitProbability * 100)}%</strong> chance
            of exceeding available resource capacity. Some options may receive HTTP 409 upon exercise.
          </div>
        </div>
      )}

      {/* Grid of Key Risk Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-4">
        <div className="p-3 rounded-lg border border-zinc-800/80 bg-zinc-950/50">
          <span className="text-[10px] font-mono uppercase text-zinc-500 block">
            System Risk
          </span>
          <div className="mt-1">
            <RiskBadge level={highestRisk} />
          </div>
        </div>

        <div className="p-3 rounded-lg border border-zinc-800/80 bg-zinc-950/50">
          <span className="text-[10px] font-mono uppercase text-zinc-500 block">
            Pending Options
          </span>
          <span className="text-lg font-bold font-mono text-cyan-400">
            {pendingOptions}
          </span>
        </div>

        <div className="p-3 rounded-lg border border-zinc-800/80 bg-zinc-950/50">
          <span className="text-[10px] font-mono uppercase text-zinc-500 block">
            Active Allocations
          </span>
          <span className="text-lg font-bold font-mono text-emerald-400">
            {activeAllocations}
          </span>
        </div>

        <div className="p-3 rounded-lg border border-zinc-800/80 bg-zinc-950/50">
          <span className="text-[10px] font-mono uppercase text-zinc-500 block">
            E[Demand]
          </span>
          <span className="text-lg font-bold font-mono text-zinc-100">
            {totalExpectedDemand.toFixed(2)}
          </span>
        </div>

        <div className="p-3 rounded-lg border border-zinc-800/80 bg-zinc-950/50">
          <span className="text-[10px] font-mono uppercase text-zinc-500 block">
            Available Headroom
          </span>
          <span className="text-lg font-bold font-mono text-blue-400">
            {totalAvailableCapacity}
          </span>
        </div>

        <div className="p-3 rounded-lg border border-zinc-800/80 bg-zinc-950/50">
          <span className="text-[10px] font-mono uppercase text-zinc-500 block">
            Max Overcommit P
          </span>
          <span
            className={`text-lg font-bold font-mono ${
              maxOvercommitProbability >= 0.6
                ? "text-rose-400"
                : maxOvercommitProbability >= 0.3
                ? "text-orange-400"
                : maxOvercommitProbability >= 0.1
                ? "text-amber-400"
                : "text-emerald-400"
            }`}
          >
            {(maxOvercommitProbability * 100).toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Capability summary cards */}
      {risk?.capability_risks && risk.capability_risks.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {risk.capability_risks.map((capRisk) => (
            <div
              key={capRisk.capability}
              className="p-3 rounded-lg border border-zinc-800/60 bg-zinc-900/30 flex items-center justify-between"
            >
              <div>
                <div className="flex items-center gap-2">
                  <Badge variant="cyan">{capRisk.capability}</Badge>
                  <RiskBadge level={capRisk.risk_level} />
                </div>
                <div className="mt-1 text-xs text-zinc-400 font-mono">
                  E[Demand]: {capRisk.expected_demand.toFixed(2)} | Avail:{" "}
                  {capRisk.available_capacity} | Pending:{" "}
                  {capRisk.pending_options_count}
                </div>
              </div>
              <div className="text-right">
                <span className="text-[11px] font-mono text-zinc-500 block">
                  P(Overcommit)
                </span>
                <span className="text-sm font-bold font-mono text-zinc-100">
                  {(capRisk.overcommit_probability * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-zinc-500 italic">
          No capabilities with registered resources yet.
        </p>
      )}
    </Card>
  );
};
