import React from "react";
import { AlertTriangle, Users } from "lucide-react";
import { Card } from "../common/Card";
import { Badge, RiskBadge } from "../common/Badge";
import { getAgentDisplayName } from "../../data/agents";
import { useReserveX } from "../../context/ReserveXContext";

export const ContentionPanel: React.FC = () => {
  const { risk, options } = useReserveX();

  const capRisks = risk?.capability_risks || [];
  const pendingOptions = options.filter((o) => o.status === "PENDING");

  // Derive contention groups: capabilities with multiple pending options
  const contentionGroups = capRisks
    .filter((cr) => cr.pending_options_count >= 2)
    .map((cr) => {
      const capOptions = pendingOptions.filter(
        (o) => o.capability === cr.capability
      );
      const uniqueAgents = Array.from(
        new Set(capOptions.map((o) => o.agent_id))
      );

      return {
        ...cr,
        options: capOptions,
        agents: uniqueAgents,
      };
    })
    .sort((a, b) => b.overcommit_probability - a.overcommit_probability);

  return (
    <Card
      title={
        <div className="flex items-center gap-2">
          <Users className="h-4 w-4 text-orange-400" />
          <span>Resource Contention Analysis</span>
        </div>
      }
      subtitle="Capabilities where multiple agents hold competing conditional options"
    >
      {contentionGroups.length === 0 ? (
        <div className="text-center py-6 border border-dashed border-zinc-800 rounded-xl">
          <AlertTriangle className="h-6 w-6 text-zinc-600 mx-auto mb-2" />
          <p className="text-sm text-zinc-400 font-medium">
            No multi-agent contention detected
          </p>
          <p className="text-xs text-zinc-500 mt-1">
            Contention occurs when two or more agents hold pending options for the same capability.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {contentionGroups.map((group) => (
            <div
              key={group.capability}
              className={`p-4 rounded-xl border transition-all ${
                group.overcommit_probability >= 0.6
                  ? "border-rose-500/40 bg-rose-950/10"
                  : group.overcommit_probability >= 0.3
                  ? "border-orange-500/30 bg-orange-950/10"
                  : "border-zinc-800/80 bg-zinc-950/40"
              }`}
            >
              {/* Header Row */}
              <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
                <div className="flex items-center gap-2">
                  <Badge variant="cyan">{group.capability}</Badge>
                  <RiskBadge level={group.risk_level} />
                  <span className="text-xs font-mono text-zinc-400">
                    {group.agents.length} competing agents
                  </span>
                </div>
                <div className="text-right text-xs font-mono">
                  <span className="text-zinc-400">P(Overcommit): </span>
                  <span
                    className={`font-bold ${
                      group.overcommit_probability >= 0.6
                        ? "text-rose-400"
                        : group.overcommit_probability >= 0.3
                        ? "text-orange-400"
                        : "text-amber-400"
                    }`}
                  >
                    {(group.overcommit_probability * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Capacity vs Demand Metrics */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3 font-mono">
                <div className="p-2 rounded-lg bg-zinc-950/50 border border-zinc-800/50">
                  <span className="text-[10px] text-zinc-500 block uppercase">
                    Available
                  </span>
                  <span className="text-sm font-bold text-emerald-400">
                    {group.available_capacity}
                  </span>
                </div>
                <div className="p-2 rounded-lg bg-zinc-950/50 border border-zinc-800/50">
                  <span className="text-[10px] text-zinc-500 block uppercase">
                    Total Demand
                  </span>
                  <span className="text-sm font-bold text-zinc-200">
                    {group.total_pending_demand}
                  </span>
                </div>
                <div className="p-2 rounded-lg bg-zinc-950/50 border border-zinc-800/50">
                  <span className="text-[10px] text-zinc-500 block uppercase">
                    E[Demand]
                  </span>
                  <span className="text-sm font-bold text-amber-400">
                    {group.expected_demand.toFixed(2)}
                  </span>
                </div>
                <div className="p-2 rounded-lg bg-zinc-950/50 border border-zinc-800/50">
                  <span className="text-[10px] text-zinc-500 block uppercase">
                    Pending Options
                  </span>
                  <span className="text-sm font-bold text-cyan-400">
                    {group.pending_options_count}
                  </span>
                </div>
              </div>

              {/* Competing Agents List */}
              <div className="flex flex-wrap gap-2">
                {group.options.map((opt) => (
                  <div
                    key={opt.id}
                    className="inline-flex items-center gap-2 rounded-lg bg-zinc-900/70 px-3 py-1.5 text-[11px] font-mono border border-zinc-800/60"
                  >
                    <span className="text-zinc-200 font-semibold">
                      {getAgentDisplayName(opt.agent_id)}
                    </span>
                    <span className="text-cyan-400">
                      {Math.round(opt.probability * 100)}%
                    </span>
                    <span className="text-zinc-500">{opt.amount}u</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};
