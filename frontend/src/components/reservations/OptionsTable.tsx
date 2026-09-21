import React, { useState } from "react";
import {
  Layers,
  CheckCircle2,
  XCircle,
  Edit2,
  Clock,
  Plus,
  Filter,
} from "lucide-react";
import { Badge, StatusBadge } from "../common/Badge";
import { getAgentDisplayName } from "../../data/agents";
import { useCountdown } from "../../hooks/useCountdown";
import { CreateOptionModal } from "./CreateOptionModal";
import { EditOptionModal } from "./EditOptionModal";
import type { ResourceOption } from "../../types/reservex";
import { useReserveX } from "../../context/ReserveXContext";

const CountdownCell: React.FC<{ option: ResourceOption }> = ({ option }) => {
  const { formatted, isExpired } = useCountdown(option.expires_at);

  if (option.status === "EXPIRED" || isExpired) {
    return (
      <span className="inline-flex items-center gap-1 font-mono text-xs text-zinc-500">
        <Clock className="h-3 w-3" />
        <span>EXPIRED</span>
      </span>
    );
  }

  if (option.status !== "PENDING") {
    return (
      <span className="font-mono text-xs text-zinc-500">
        {option.exercised_at
          ? `Done (${new Date(option.exercised_at).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })})`
          : "—"}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 font-mono text-xs text-cyan-300 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
      <Clock className="h-3 w-3 animate-spin" />
      <span>{formatted}</span>
    </span>
  );
};

export const OptionsTable: React.FC = () => {
  const {
    options,
    exerciseOption,
    cancelOption,
  } = useReserveX();

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingOption, setEditingOption] = useState<ResourceOption | null>(null);

  const [filterAgent, setFilterAgent] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [filterCapability, setFilterCapability] = useState<string>("all");

  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  // Extract unique capabilities and agents for filters
  const uniqueAgents = Array.from(new Set(options.map((o) => o.agent_id)));
  const uniqueCapabilities = Array.from(new Set(options.map((o) => o.capability)));

  // Filtered options
  const filteredOptions = options.filter((o) => {
    if (filterAgent !== "all" && o.agent_id !== filterAgent) return false;
    if (filterStatus !== "all" && o.status !== filterStatus) return false;
    if (filterCapability !== "all" && o.capability !== filterCapability)
      return false;
    return true;
  });

  const handleExercise = async (id: string) => {
    setActionLoadingId(id);
    await exerciseOption(id);
    setActionLoadingId(null);
  };

  const handleCancel = async (id: string) => {
    setActionLoadingId(id);
    await cancelOption(id);
    setActionLoadingId(null);
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
            <Layers className="h-5 w-5 text-cyan-400" />
            <span>Conditional Resource Options</span>
          </h2>
          <p className="text-xs text-zinc-400 mt-1">
            Pre-registered probabilistic claims held by autonomous agents prior to execution.
          </p>
        </div>

        <button
          onClick={() => setIsCreateOpen(true)}
          className="inline-flex items-center gap-2 rounded-xl border border-cyan-500/40 bg-cyan-500/10 px-4 py-2 text-xs font-mono font-semibold text-cyan-200 hover:bg-cyan-500/20 shadow-lg shadow-cyan-950/20 transition-all"
        >
          <Plus className="h-4 w-4" />
          <span>Create Option</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 p-3.5 rounded-xl border border-zinc-800/80 bg-zinc-900/50 text-xs font-mono">
        <div className="flex items-center gap-1.5 text-zinc-400">
          <Filter className="h-3.5 w-3.5 text-cyan-400" />
          <span>Filters:</span>
        </div>

        {/* Status Filter */}
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="rounded-lg border border-zinc-700/80 bg-zinc-950 px-2.5 py-1 text-zinc-200 focus:border-cyan-500 focus:outline-none"
        >
          <option value="all">All Statuses ({options.length})</option>
          <option value="PENDING">
            PENDING ({options.filter((o) => o.status === "PENDING").length})
          </option>
          <option value="EXERCISED">
            EXERCISED ({options.filter((o) => o.status === "EXERCISED").length})
          </option>
          <option value="EXPIRED">
            EXPIRED ({options.filter((o) => o.status === "EXPIRED").length})
          </option>
          <option value="CANCELLED">
            CANCELLED ({options.filter((o) => o.status === "CANCELLED").length})
          </option>
        </select>

        {/* Agent Filter */}
        <select
          value={filterAgent}
          onChange={(e) => setFilterAgent(e.target.value)}
          className="rounded-lg border border-zinc-700/80 bg-zinc-950 px-2.5 py-1 text-zinc-200 focus:border-cyan-500 focus:outline-none"
        >
          <option value="all">All Agents</option>
          {uniqueAgents.map((ag) => (
            <option key={ag} value={ag}>
              {getAgentDisplayName(ag)} ({ag})
            </option>
          ))}
        </select>

        {/* Capability Filter */}
        <select
          value={filterCapability}
          onChange={(e) => setFilterCapability(e.target.value)}
          className="rounded-lg border border-zinc-700/80 bg-zinc-950 px-2.5 py-1 text-zinc-200 focus:border-cyan-500 focus:outline-none"
        >
          <option value="all">All Capabilities</option>
          {uniqueCapabilities.map((cap) => (
            <option key={cap} value={cap}>
              {cap}
            </option>
          ))}
        </select>

        <span className="text-zinc-500 ml-auto hidden sm:inline">
          Showing {filteredOptions.length} of {options.length} options
        </span>
      </div>

      {/* Table Card */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-zinc-800 bg-zinc-950/80 font-mono text-[11px] uppercase tracking-wider text-zinc-400">
              <tr>
                <th className="px-4 py-3.5">Agent</th>
                <th className="px-4 py-3.5">Capability</th>
                <th className="px-4 py-3.5 text-center">Probability</th>
                <th className="px-4 py-3.5 text-center">Units</th>
                <th className="px-4 py-3.5 text-center">Priority</th>
                <th className="px-4 py-3.5">Status</th>
                <th className="px-4 py-3.5">Created</th>
                <th className="px-4 py-3.5">Expires</th>
                <th className="px-4 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 font-mono">
              {filteredOptions.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center text-zinc-500">
                    No conditional options match the current filters.
                  </td>
                </tr>
              ) : (
                filteredOptions.map((opt) => {
                  const agentName = getAgentDisplayName(opt.agent_id);
                  const isPending = opt.status === "PENDING";
                  const isActionLoading = actionLoadingId === opt.id;

                  const probPercent = Math.round(opt.probability * 100);

                  return (
                    <tr
                      key={opt.id}
                      className="hover:bg-zinc-800/30 transition-colors"
                    >
                      {/* Agent */}
                      <td className="px-4 py-3">
                        <div className="font-sans font-semibold text-zinc-200">
                          {agentName}
                        </div>
                        <div className="text-[10px] text-zinc-500 font-mono">
                          {opt.agent_id}
                        </div>
                      </td>

                      {/* Capability */}
                      <td className="px-4 py-3">
                        <Badge variant="cyan">{opt.capability}</Badge>
                      </td>

                      {/* Probability */}
                      <td className="px-4 py-3 text-center">
                        <div className="flex items-center justify-center gap-1.5">
                          <div className="w-12 bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-cyan-400 rounded-full"
                              style={{ width: `${probPercent}%` }}
                            />
                          </div>
                          <span className="font-bold text-zinc-200">
                            {probPercent}%
                          </span>
                        </div>
                      </td>

                      {/* Amount */}
                      <td className="px-4 py-3 text-center font-bold text-zinc-300">
                        {opt.amount}u
                      </td>

                      {/* Priority */}
                      <td className="px-4 py-3 text-center text-zinc-400">
                        P{opt.priority}
                      </td>

                      {/* Status */}
                      <td className="px-4 py-3">
                        <StatusBadge status={opt.status} />
                      </td>

                      {/* Created */}
                      <td className="px-4 py-3 text-zinc-400">
                        {new Date(opt.created_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                        })}
                      </td>

                      {/* Expires Countdown */}
                      <td className="px-4 py-3">
                        <CountdownCell option={opt} />
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3 text-right">
                        {isPending ? (
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => handleExercise(opt.id)}
                              disabled={isActionLoading}
                              title="Exercise Option (attempt real resource allocation)"
                              className="px-2.5 py-1 rounded-md border border-emerald-500/40 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/25 transition-all text-xs font-mono font-semibold flex items-center gap-1 disabled:opacity-50"
                            >
                              <CheckCircle2 className="h-3 w-3" />
                              <span>Exercise</span>
                            </button>

                            <button
                              onClick={() => handleCancel(opt.id)}
                              disabled={isActionLoading}
                              title="Cancel Option (no resource consumed)"
                              className="px-2 py-1 rounded-md border border-zinc-700 bg-zinc-800/80 text-zinc-300 hover:bg-zinc-700 hover:text-white transition-all text-xs font-mono flex items-center gap-1 disabled:opacity-50"
                            >
                              <XCircle className="h-3 w-3" />
                              <span>Cancel</span>
                            </button>

                            <button
                              onClick={() => setEditingOption(opt)}
                              disabled={isActionLoading}
                              title="Edit probability or expiry"
                              className="p-1 rounded-md border border-zinc-700/60 bg-zinc-800/60 text-zinc-400 hover:text-cyan-300 hover:border-cyan-500/40 transition-colors"
                            >
                              <Edit2 className="h-3 w-3" />
                            </button>
                          </div>
                        ) : (
                          <span className="text-[11px] text-zinc-600 font-mono italic">
                            Completed
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      <CreateOptionModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
      />

      <EditOptionModal
        option={editingOption}
        isOpen={!!editingOption}
        onClose={() => setEditingOption(null)}
      />
    </div>
  );
};
