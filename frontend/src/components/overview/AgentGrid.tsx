import React from "react";
import {
  Bot,
  Layers,
  Cpu,
  Activity,
  AlertTriangle,
  Clock,
  Sparkles,
  CheckCircle2,
} from "lucide-react";
import { Card } from "../common/Card";
import { KNOWN_AGENTS } from "../../data/agents";
import { useReserveX } from "../../context/ReserveXContext";

export const AgentGrid: React.FC = () => {
  const { options, allocations, events, liveSimulation } = useReserveX();

  // Inspect activity per known agent
  const agentList = Object.values(KNOWN_AGENTS);

  return (
    <Card
      title={
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-purple-400" />
          <span>Simulated Agent Fleet & Live Progression</span>
        </div>
      }
      subtitle="Autonomous agents navigating continuous workflows with ML capability prediction and conditional reservation"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {agentList.map((agent) => {
          const agentOptions = options.filter((o) => o.agent_id === agent.id);
          const pendingOptions = agentOptions.filter((o) => o.status === "PENDING");
          const agentAllocations = allocations.filter(
            (a) => a.agent_id === agent.id && !a.released_at
          );
          const latestEvent = events.find((e) => e.agent_id === agent.id);

          // Find live simulation state for this agent
          const liveAgent = liveSimulation?.agents?.find((a) => a.id === agent.id);

          const isWaiting = liveAgent?.waiting_for_capacity;
          const isAllocated =
            (liveAgent?.allocation_id && liveAgent.allocation_id.length > 0) ||
            agentAllocations.length > 0;
          const hasPendingOption =
            liveAgent?.option_status === "PENDING" || pendingOptions.length > 0;

          const isActive =
            liveSimulation?.running ||
            hasPendingOption ||
            isAllocated ||
            isWaiting;

          // Highest predicted probability
          const probDisplay =
            liveAgent?.prediction_probability !== undefined &&
            liveAgent?.prediction_probability !== null &&
            liveAgent.prediction_probability > 0
              ? Math.round(liveAgent.prediction_probability * 100)
              : pendingOptions.length > 0
              ? Math.round(Math.max(...pendingOptions.map((o) => o.probability)) * 100)
              : null;

          return (
            <div
              key={agent.id}
              className={`rounded-xl border p-4 flex flex-col justify-between transition-all duration-300 ${
                isWaiting
                  ? "border-amber-500/60 bg-amber-950/20 shadow-lg shadow-amber-950/30 ring-1 ring-amber-500/40"
                  : isAllocated
                  ? "border-emerald-500/50 bg-emerald-950/15 shadow-md shadow-emerald-950/20"
                  : isActive
                  ? "border-zinc-700 bg-zinc-950/70 shadow-md shadow-purple-950/10"
                  : "border-zinc-800/60 bg-zinc-950/30 opacity-80"
              }`}
            >
              <div>
                {/* Agent Header */}
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="font-semibold text-sm text-zinc-100">
                        {agent.name}
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-zinc-500">
                      {agent.id}
                    </span>
                  </div>
                  <span
                    className={`h-2.5 w-2.5 rounded-full shrink-0 ${
                      isWaiting
                        ? "bg-amber-400 shadow-sm shadow-amber-400 animate-ping"
                        : isAllocated
                        ? "bg-emerald-400 shadow-sm shadow-emerald-400 animate-pulse"
                        : isActive
                        ? "bg-cyan-400 shadow-sm shadow-cyan-400 animate-pulse"
                        : "bg-zinc-600"
                    }`}
                    title={
                      isWaiting
                        ? "Waiting for capacity (409)"
                        : isAllocated
                        ? "Resource Allocated"
                        : isActive
                        ? "Active in workflow"
                        : "Idle"
                    }
                  />
                </div>

                <p className="text-[11px] text-zinc-400 leading-snug line-clamp-1 mb-2.5">
                  {agent.role}
                </p>

                {/* Live Contention Alert */}
                {isWaiting && (
                  <div className="mb-2.5 rounded-lg border border-amber-500/40 bg-amber-500/10 p-2 text-center animate-pulse">
                    <div className="flex items-center justify-center gap-1.5 text-xs font-mono font-bold text-amber-300">
                      <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
                      <span>WAITING FOR CAPACITY</span>
                    </div>
                    <div className="text-[10px] font-mono text-amber-400/80 mt-0.5">
                      409 Contention • Retrying on release
                    </div>
                  </div>
                )}

                {/* Workflow Step Indicator */}
                <div className="mb-2.5 rounded-lg border border-zinc-800/80 bg-zinc-900/60 p-2 text-xs font-mono">
                  <div className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1 flex items-center justify-between">
                    <span>Workflow Step</span>
                    {liveAgent?.duration_remaining !== undefined &&
                      liveAgent.duration_remaining > 0 && (
                        <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                          <Clock className="h-2.5 w-2.5" />
                          {liveAgent.duration_remaining}t left
                        </span>
                      )}
                  </div>
                  <div className="text-zinc-200 font-semibold truncate">
                    {liveAgent?.current_step || "Awaiting Start"}
                  </div>
                </div>

                {/* Prediction & Option Status */}
                <div className="space-y-1.5 border-t border-zinc-800/60 pt-2.5 text-xs font-mono">
                  {liveAgent?.predicted_capability && (
                    <div className="flex items-center justify-between text-zinc-400">
                      <span className="flex items-center gap-1 text-[11px] text-zinc-400">
                        <Sparkles className="h-3 w-3 text-purple-400" />
                        Predicted:
                      </span>
                      <strong className="text-purple-300 text-[11px] font-semibold truncate max-w-[120px]">
                        {liveAgent.predicted_capability}
                      </strong>
                    </div>
                  )}

                  {probDisplay !== null && (
                    <div className="flex items-center justify-between text-zinc-400">
                      <span className="text-[11px]">ML Confidence:</span>
                      <strong className="text-cyan-300 font-bold">
                        {probDisplay}%
                      </strong>
                    </div>
                  )}

                  <div className="flex items-center justify-between text-zinc-400">
                    <span className="flex items-center gap-1 text-[11px]">
                      <Layers className="h-3 w-3 text-cyan-400" />
                      Option:
                    </span>
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                        liveAgent?.option_status === "EXERCISED"
                          ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                          : liveAgent?.option_status === "PENDING" || pendingOptions.length > 0
                          ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                          : "text-zinc-500"
                      }`}
                    >
                      {liveAgent?.option_status || (pendingOptions.length > 0 ? "PENDING" : "NONE")}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-zinc-400">
                    <span className="flex items-center gap-1 text-[11px]">
                      <Cpu className="h-3 w-3 text-emerald-400" />
                      Allocation:
                    </span>
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                        isAllocated
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 animate-pulse"
                          : "text-zinc-500"
                      }`}
                    >
                      {isAllocated ? "ACTIVE" : "NONE"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Status Footer */}
              <div className="mt-3 pt-2 border-t border-zinc-800/60 text-[10px] font-mono text-zinc-500">
                <div className="flex items-center gap-1 text-zinc-400 truncate">
                  {isAllocated ? (
                    <CheckCircle2 className="h-3 w-3 shrink-0 text-emerald-400" />
                  ) : (
                    <Activity className="h-3 w-3 shrink-0 text-zinc-500" />
                  )}
                  <span className="truncate">
                    {isWaiting
                      ? "409 Contention Wait"
                      : isAllocated
                      ? "Executing on Allocated Resource"
                      : liveAgent?.option_status === "PENDING"
                      ? "Conditional Option Pending"
                      : latestEvent
                      ? latestEvent.event_type.replace(/_/g, " ")
                      : "Ready"}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
