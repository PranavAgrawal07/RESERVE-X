import React from "react";
import { Badge, RiskBadge } from "../common/Badge";
import { useReserveX } from "../../context/ReserveXContext";

export const RiskTable: React.FC = () => {
  const { risk } = useReserveX();

  const capRisks = risk?.capability_risks || [];

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 overflow-hidden shadow-xl">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-zinc-800 bg-zinc-950/80 font-mono text-[11px] uppercase tracking-wider text-zinc-400">
            <tr>
              <th className="px-4 py-3.5">Capability</th>
              <th className="px-4 py-3.5 text-center">Total Cap.</th>
              <th className="px-4 py-3.5 text-center">Allocated</th>
              <th className="px-4 py-3.5 text-center">Available</th>
              <th className="px-4 py-3.5 text-center">Pending Opts</th>
              <th className="px-4 py-3.5 text-center">Pending Demand</th>
              <th className="px-4 py-3.5 text-center">E[Demand]</th>
              <th className="px-4 py-3.5 text-center">P(Overcommit)</th>
              <th className="px-4 py-3.5 text-center">Risk Level</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60 font-mono">
            {capRisks.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-zinc-500">
                  No capabilities with registered resources. Register resources to enable risk analysis.
                </td>
              </tr>
            ) : (
              capRisks.map((cr) => {
                const overcommitPercent = (cr.overcommit_probability * 100).toFixed(1);

                return (
                  <tr
                    key={cr.capability}
                    className="hover:bg-zinc-800/30 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <Badge variant="cyan">{cr.capability}</Badge>
                    </td>
                    <td className="px-4 py-3 text-center text-zinc-300">
                      {cr.total_capacity}
                    </td>
                    <td className="px-4 py-3 text-center text-cyan-400 font-semibold">
                      {cr.allocated_capacity}
                    </td>
                    <td className="px-4 py-3 text-center text-emerald-400 font-semibold">
                      {cr.available_capacity}
                    </td>
                    <td className="px-4 py-3 text-center text-zinc-300">
                      {cr.pending_options_count}
                    </td>
                    <td className="px-4 py-3 text-center text-zinc-300">
                      {cr.total_pending_demand}
                    </td>
                    <td className="px-4 py-3 text-center text-amber-400 font-semibold">
                      {cr.expected_demand.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span
                        className={`font-bold ${
                          cr.overcommit_probability >= 0.6
                            ? "text-rose-400"
                            : cr.overcommit_probability >= 0.3
                            ? "text-orange-400"
                            : cr.overcommit_probability >= 0.1
                            ? "text-amber-400"
                            : "text-emerald-400"
                        }`}
                      >
                        {overcommitPercent}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <RiskBadge level={cr.risk_level} />
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
