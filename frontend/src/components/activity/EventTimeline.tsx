import React, { useState } from "react";
import {
  History,
  Filter,
  Layers,
  CheckCircle2,
  Clock,
  XCircle,
  AlertTriangle,
  Cpu,
  Server,
  ArrowUpDown,
  RefreshCw,
} from "lucide-react";
import { Badge } from "../common/Badge";
import { getAgentDisplayName } from "../../data/agents";
import { useReserveX } from "../../context/ReserveXContext";

const EVENT_ICONS: Record<string, React.ReactNode> = {
  OPTION_CREATED: <Layers className="h-4 w-4 text-cyan-400" />,
  OPTION_UPDATED: <ArrowUpDown className="h-4 w-4 text-purple-400" />,
  OPTION_EXERCISED: <CheckCircle2 className="h-4 w-4 text-emerald-400" />,
  OPTION_EXPIRED: <Clock className="h-4 w-4 text-zinc-400" />,
  OPTION_CANCELLED: <XCircle className="h-4 w-4 text-slate-400" />,
  EXERCISE_FAILED: <AlertTriangle className="h-4 w-4 text-rose-400" />,
  ALLOCATION_CREATED: <Cpu className="h-4 w-4 text-emerald-400" />,
  ALLOCATION_RELEASED: <RefreshCw className="h-4 w-4 text-amber-400" />,
  RESOURCE_REGISTERED: <Server className="h-4 w-4 text-blue-400" />,
};

const EVENT_COLORS: Record<string, string> = {
  OPTION_CREATED: "border-l-cyan-500",
  OPTION_UPDATED: "border-l-purple-500",
  OPTION_EXERCISED: "border-l-emerald-500",
  OPTION_EXPIRED: "border-l-zinc-600",
  OPTION_CANCELLED: "border-l-slate-500",
  EXERCISE_FAILED: "border-l-rose-500",
  ALLOCATION_CREATED: "border-l-emerald-500",
  ALLOCATION_RELEASED: "border-l-amber-500",
  RESOURCE_REGISTERED: "border-l-blue-500",
};

const EVENT_BADGE_VARIANTS: Record<string, "cyan" | "exercised" | "expired" | "cancelled" | "critical" | "purple" | "sky" | "default"> = {
  OPTION_CREATED: "cyan",
  OPTION_UPDATED: "purple",
  OPTION_EXERCISED: "exercised",
  OPTION_EXPIRED: "expired",
  OPTION_CANCELLED: "cancelled",
  EXERCISE_FAILED: "critical",
  ALLOCATION_CREATED: "exercised",
  ALLOCATION_RELEASED: "default",
  RESOURCE_REGISTERED: "sky",
};

export const EventTimeline: React.FC = () => {
  const { events } = useReserveX();

  const [filterType, setFilterType] = useState<string>("all");
  const [filterAgent, setFilterAgent] = useState<string>("all");

  const uniqueAgents = Array.from(
    new Set(events.filter((e) => e.agent_id).map((e) => e.agent_id!))
  );

  const filteredEvents = events.filter((e) => {
    if (filterType !== "all" && e.event_type !== filterType) return false;
    if (filterAgent !== "all" && e.agent_id !== filterAgent) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
          <History className="h-5 w-5 text-cyan-400" />
          <span>System Activity & Audit Timeline</span>
        </h2>
        <p className="text-xs text-zinc-400 mt-1">
          Immutable reverse-chronological event log. All lifecycle transitions are recorded by the backend store.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 p-3.5 rounded-xl border border-zinc-800/80 bg-zinc-900/50 text-xs font-mono">
        <div className="flex items-center gap-1.5 text-zinc-400">
          <Filter className="h-3.5 w-3.5 text-cyan-400" />
          <span>Filters:</span>
        </div>

        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="rounded-lg border border-zinc-700/80 bg-zinc-950 px-2.5 py-1 text-zinc-200 focus:border-cyan-500 focus:outline-none"
        >
          <option value="all">All Event Types ({events.length})</option>
          <option value="OPTION_CREATED">OPTION_CREATED</option>
          <option value="OPTION_UPDATED">OPTION_UPDATED</option>
          <option value="OPTION_EXERCISED">OPTION_EXERCISED</option>
          <option value="OPTION_EXPIRED">OPTION_EXPIRED</option>
          <option value="OPTION_CANCELLED">OPTION_CANCELLED</option>
          <option value="EXERCISE_FAILED">EXERCISE_FAILED</option>
          <option value="ALLOCATION_CREATED">ALLOCATION_CREATED</option>
          <option value="ALLOCATION_RELEASED">ALLOCATION_RELEASED</option>
          <option value="RESOURCE_REGISTERED">RESOURCE_REGISTERED</option>
        </select>

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

        <span className="text-zinc-500 ml-auto hidden sm:inline">
          {filteredEvents.length} events
        </span>
      </div>

      {/* Timeline */}
      {filteredEvents.length === 0 ? (
        <div className="text-center py-12 border border-dashed border-zinc-800 rounded-xl">
          <History className="h-8 w-8 text-zinc-600 mx-auto mb-2" />
          <p className="text-sm text-zinc-400 font-medium">No events recorded</p>
          <p className="text-xs text-zinc-500 mt-1">
            Events are logged automatically as agents interact with the system.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredEvents.map((evt) => {
            const icon = EVENT_ICONS[evt.event_type] || (
              <Layers className="h-4 w-4 text-zinc-400" />
            );
            const borderColor =
              EVENT_COLORS[evt.event_type] || "border-l-zinc-700";
            const badgeVariant =
              EVENT_BADGE_VARIANTS[evt.event_type] || "default";

            const agentName = getAgentDisplayName(evt.agent_id);

            const time = new Date(evt.timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            });
            const date = new Date(evt.timestamp).toLocaleDateString([], {
              month: "short",
              day: "numeric",
            });

            // Build details string
            const detailParts: string[] = [];
            if (evt.details?.capability)
              detailParts.push(`Cap: ${evt.details.capability}`);
            if (evt.details?.probability !== undefined)
              detailParts.push(
                `Prob: ${Math.round(evt.details.probability * 100)}%`
              );
            if (evt.details?.amount !== undefined)
              detailParts.push(`Amount: ${evt.details.amount}u`);
            if (evt.details?.reason)
              detailParts.push(`Reason: ${evt.details.reason}`);
            if (evt.details?.old_probability !== undefined)
              detailParts.push(
                `${Math.round(evt.details.old_probability * 100)}% → ${Math.round(
                  evt.details.new_probability * 100
                )}%`
              );
            if (evt.details?.allocation_id)
              detailParts.push(
                `Alloc: ${evt.details.allocation_id.substring(0, 8)}`
              );

            return (
              <div
                key={evt.id}
                className={`flex items-start gap-4 p-4 rounded-xl border border-zinc-800/60 bg-zinc-900/40 hover:bg-zinc-900/60 transition-colors border-l-[3px] ${borderColor}`}
              >
                {/* Icon */}
                <div className="mt-0.5 shrink-0">{icon}</div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <Badge variant={badgeVariant} size="sm">
                      {evt.event_type.replace(/_/g, " ")}
                    </Badge>
                    <span className="font-sans font-semibold text-sm text-zinc-200">
                      {agentName}
                    </span>
                  </div>

                  {/* Detail line */}
                  {detailParts.length > 0 && (
                    <p className="text-[11px] font-mono text-zinc-400 mt-1">
                      {detailParts.join(" · ")}
                    </p>
                  )}

                  {/* IDs */}
                  <div className="flex flex-wrap gap-3 mt-1.5 text-[10px] font-mono text-zinc-600">
                    {evt.option_id && (
                      <span>Option: {evt.option_id.substring(0, 12)}</span>
                    )}
                    {evt.resource_id && (
                      <span>Resource: {evt.resource_id.substring(0, 12)}</span>
                    )}
                    <span>Event: {evt.id.substring(0, 12)}</span>
                  </div>
                </div>

                {/* Timestamp */}
                <div className="text-right shrink-0 font-mono">
                  <div className="text-xs text-zinc-300">{time}</div>
                  <div className="text-[10px] text-zinc-500">{date}</div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
