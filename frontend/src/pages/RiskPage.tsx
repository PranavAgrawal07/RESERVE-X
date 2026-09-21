import React from "react";
import { ShieldAlert, AlertTriangle } from "lucide-react";
import { RiskBadge } from "../components/common/Badge";
import { RiskTable } from "../components/risk/RiskTable";
import { RiskDemandChart } from "../components/risk/RiskDemandChart";
import { ContentionPanel } from "../components/risk/ContentionPanel";
import { useReserveX } from "../context/ReserveXContext";

export const RiskPage: React.FC = () => {
  const { risk } = useReserveX();

  const highestRisk = risk?.highest_risk_level || "LOW";
  const isHighRisk = highestRisk === "HIGH" || highestRisk === "CRITICAL";

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-orange-400" />
            <span>Risk & Conflict Analysis</span>
          </h2>
          <p className="text-xs text-zinc-400 mt-1">
            Exact 2^n subset enumeration across all capabilities to quantify overcommit risk.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-zinc-400">System Risk:</span>
          <RiskBadge level={highestRisk} />
        </div>
      </div>

      {/* Risk Warning Banner */}
      {isHighRisk && (
        <div className="rounded-xl border border-orange-500/40 bg-orange-950/15 p-4 flex items-start gap-3 shadow-lg shadow-orange-950/10">
          <AlertTriangle className="h-5 w-5 text-orange-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-semibold text-orange-200">
              Elevated Contention Risk Detected
            </h4>
            <p className="text-xs text-orange-300/80 mt-1 leading-relaxed">
              Current pending options present a significant probability of capacity exhaustion
              if agents exercise simultaneously. Agents attempting to exercise during contention
              will receive HTTP 409 responses and their options will remain PENDING.
            </p>
          </div>
        </div>
      )}

      {/* Per-Capability Risk Table */}
      <RiskTable />

      {/* Demand vs Capacity Chart */}
      <RiskDemandChart />

      {/* Contention Analysis */}
      <ContentionPanel />
    </div>
  );
};
