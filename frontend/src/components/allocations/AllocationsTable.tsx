import React, { useState } from "react";
import { Cpu, Unlock, Package } from "lucide-react";
import { Badge } from "../common/Badge";
import { getAgentDisplayName } from "../../data/agents";
import { useReserveX } from "../../context/ReserveXContext";

export const AllocationsTable: React.FC = () => {
  const { allocations, releaseAllocation, resources } = useReserveX();

  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  const activeAllocations = allocations.filter((a) => !a.released_at);
  const releasedAllocations = allocations.filter((a) => a.released_at);

  const handleRelease = async (id: string) => {
    setActionLoadingId(id);
    await releaseAllocation(id);
    setActionLoadingId(null);
  };

  const getResourceName = (resourceId: string): string => {
    const res = resources.find((r) => r.id === resourceId);
    return res?.name || `Resource ${resourceId.substring(0, 8)}`;
  };

  return (
    <div className="space-y-6">
      {/* Active Allocations */}
      <div>
        <h3 className="text-sm font-semibold text-zinc-200 flex items-center gap-2 mb-3">
          <Cpu className="h-4 w-4 text-emerald-400" />
          <span>Active Allocations ({activeAllocations.length})</span>
        </h3>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-zinc-800 bg-zinc-950/80 font-mono text-[11px] uppercase tracking-wider text-zinc-400">
                <tr>
                  <th className="px-4 py-3">Allocation ID</th>
                  <th className="px-4 py-3">Agent</th>
                  <th className="px-4 py-3">Resource</th>
                  <th className="px-4 py-3">Capability</th>
                  <th className="px-4 py-3 text-center">Amount</th>
                  <th className="px-4 py-3">Allocated At</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/60 font-mono">
                {activeAllocations.length === 0 ? (
                  <tr>
                    <td
                      colSpan={7}
                      className="px-4 py-6 text-center text-zinc-500"
                    >
                      No active allocations. Exercise a pending option to create one.
                    </td>
                  </tr>
                ) : (
                  activeAllocations.map((alloc) => (
                    <tr
                      key={alloc.id}
                      className="hover:bg-zinc-800/30 transition-colors"
                    >
                      <td className="px-4 py-3 text-[11px] text-zinc-400">
                        {alloc.id.substring(0, 12)}...
                      </td>
                      <td className="px-4 py-3">
                        <span className="font-sans font-semibold text-zinc-200">
                          {getAgentDisplayName(alloc.agent_id)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-zinc-300">
                        {getResourceName(alloc.resource_id)}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="cyan">{alloc.capability}</Badge>
                      </td>
                      <td className="px-4 py-3 text-center font-bold text-emerald-400">
                        {alloc.amount}u
                      </td>
                      <td className="px-4 py-3 text-zinc-400">
                        {new Date(alloc.allocated_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                        })}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => handleRelease(alloc.id)}
                          disabled={actionLoadingId === alloc.id}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md border border-amber-500/40 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20 transition-all text-xs font-mono font-semibold disabled:opacity-50"
                        >
                          <Unlock className="h-3 w-3" />
                          <span>Release</span>
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Released Allocations (history) */}
      {releasedAllocations.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-zinc-400 flex items-center gap-2 mb-3">
            <Package className="h-4 w-4 text-zinc-500" />
            <span>Released Allocations ({releasedAllocations.length})</span>
          </h3>

          <div className="rounded-xl border border-zinc-800/60 bg-zinc-950/40 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-zinc-800/60 bg-zinc-950/60 font-mono text-[11px] uppercase tracking-wider text-zinc-500">
                  <tr>
                    <th className="px-4 py-3">Allocation ID</th>
                    <th className="px-4 py-3">Agent</th>
                    <th className="px-4 py-3">Capability</th>
                    <th className="px-4 py-3 text-center">Amount</th>
                    <th className="px-4 py-3">Allocated At</th>
                    <th className="px-4 py-3">Released At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/40 font-mono text-zinc-500">
                  {releasedAllocations.map((alloc) => (
                    <tr key={alloc.id}>
                      <td className="px-4 py-2.5 text-[11px]">
                        {alloc.id.substring(0, 12)}...
                      </td>
                      <td className="px-4 py-2.5">
                        {getAgentDisplayName(alloc.agent_id)}
                      </td>
                      <td className="px-4 py-2.5">{alloc.capability}</td>
                      <td className="px-4 py-2.5 text-center">{alloc.amount}u</td>
                      <td className="px-4 py-2.5">
                        {new Date(alloc.allocated_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                        })}
                      </td>
                      <td className="px-4 py-2.5">
                        {alloc.released_at &&
                          new Date(alloc.released_at).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                            second: "2-digit",
                          })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
