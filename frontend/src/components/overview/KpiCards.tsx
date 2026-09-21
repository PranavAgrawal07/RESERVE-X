import React from "react";
import {
  Layers,
  Cpu,
  ShieldAlert,
  Server,
} from "lucide-react";
import { RiskBadge } from "../common/Badge";
import { useReserveX } from "../../context/ReserveXContext";

export const KpiCards: React.FC = () => {
  const { options, allocations, resources, risk } = useReserveX();

  const pendingOptions = options.filter((o) => o.status === "PENDING");
  const pendingCount = pendingOptions.length;
  const activeAllocations = allocations.filter((a) => !a.released_at);
  const activeAllocationsCount = activeAllocations.length;

  const totalCapacity = resources.reduce((acc, r) => acc + r.total_capacity, 0);
  const totalAllocated = resources.reduce(
    (acc, r) => acc + r.allocated_capacity,
    0
  );
  const totalAvailable = Math.max(0, totalCapacity - totalAllocated);
  const availablePercentage =
    totalCapacity > 0 ? Math.round((totalAvailable / totalCapacity) * 100) : 100;

  const highestRisk = risk?.highest_risk_level || "LOW";

  // Calculate total pending demand
  const totalPendingDemand = pendingOptions.reduce(
    (acc, o) => acc + o.amount,
    0
  );

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* 1. Pending Options */}
      <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-5 backdrop-blur-md relative overflow-hidden group hover:border-cyan-500/40 transition-all">
        <div className="absolute top-0 left-0 w-1 h-full bg-cyan-500" />
        <div className="flex items-center justify-between text-zinc-400 mb-2">
          <span className="text-xs font-mono tracking-wider uppercase">
            Pending Options
          </span>
          <Layers className="h-4 w-4 text-cyan-400" />
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold font-mono text-zinc-100">
            {pendingCount}
          </span>
          <span className="text-xs text-zinc-400 font-mono">
            {totalPendingDemand} units requested
          </span>
        </div>
        <div className="mt-3 flex items-center justify-between text-[11px] text-zinc-400 border-t border-zinc-800/60 pt-2.5">
          <span>Contingent Demand</span>
          <span className="text-cyan-400 font-mono">Pre-committed rights</span>
        </div>
      </div>

      {/* 2. Active Allocations */}
      <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-5 backdrop-blur-md relative overflow-hidden group hover:border-emerald-500/40 transition-all">
        <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500" />
        <div className="flex items-center justify-between text-zinc-400 mb-2">
          <span className="text-xs font-mono tracking-wider uppercase">
            Active Allocations
          </span>
          <Cpu className="h-4 w-4 text-emerald-400" />
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold font-mono text-zinc-100">
            {activeAllocationsCount}
          </span>
          <span className="text-xs text-zinc-400 font-mono">
            {totalAllocated} units locked
          </span>
        </div>
        <div className="mt-3 flex items-center justify-between text-[11px] text-zinc-400 border-t border-zinc-800/60 pt-2.5">
          <span>Exercised Options</span>
          <span className="text-emerald-400 font-mono">Real execution</span>
        </div>
      </div>

      {/* 3. Available Capacity */}
      <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-5 backdrop-blur-md relative overflow-hidden group hover:border-blue-500/40 transition-all">
        <div className="absolute top-0 left-0 w-1 h-full bg-blue-500" />
        <div className="flex items-center justify-between text-zinc-400 mb-2">
          <span className="text-xs font-mono tracking-wider uppercase">
            Available Capacity
          </span>
          <Server className="h-4 w-4 text-blue-400" />
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold font-mono text-zinc-100">
            {totalAvailable}
          </span>
          <span className="text-xs text-zinc-400 font-mono">
            / {totalCapacity} units ({availablePercentage}%)
          </span>
        </div>
        <div className="mt-3 flex items-center justify-between text-[11px] text-zinc-400 border-t border-zinc-800/60 pt-2.5">
          <span>Pool Headroom</span>
          <span className="text-blue-400 font-mono">{totalAllocated} Allocated</span>
        </div>
      </div>

      {/* 4. Highest Risk Level */}
      <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/60 p-5 backdrop-blur-md relative overflow-hidden group hover:border-amber-500/40 transition-all">
        <div
          className={`absolute top-0 left-0 w-1 h-full ${
            highestRisk === "CRITICAL"
              ? "bg-rose-500"
              : highestRisk === "HIGH"
              ? "bg-orange-500"
              : highestRisk === "MEDIUM"
              ? "bg-amber-500"
              : "bg-emerald-500"
          }`}
        />
        <div className="flex items-center justify-between text-zinc-400 mb-2">
          <span className="text-xs font-mono tracking-wider uppercase">
            Highest Risk Level
          </span>
          <ShieldAlert
            className={`h-4 w-4 ${
              highestRisk === "CRITICAL"
                ? "text-rose-400"
                : highestRisk === "HIGH"
                ? "text-orange-400"
                : highestRisk === "MEDIUM"
                ? "text-amber-400"
                : "text-emerald-400"
            }`}
          />
        </div>
        <div className="flex items-center gap-3">
          <RiskBadge level={highestRisk} />
          {risk?.capability_risks && risk.capability_risks.length > 0 && (
            <span className="text-xs font-mono text-zinc-400">
              max P(over):{" "}
              {Math.round(
                Math.max(...risk.capability_risks.map((c) => c.overcommit_probability)) * 100
              )}
              %
            </span>
          )}
        </div>
        <div className="mt-3 flex items-center justify-between text-[11px] text-zinc-400 border-t border-zinc-800/60 pt-2.5">
          <span>Overcommit Engine</span>
          <span className="text-zinc-300 font-mono">2^n Exact Subset</span>
        </div>
      </div>
    </div>
  );
};
