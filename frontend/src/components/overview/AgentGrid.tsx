import React from "react";
import { Bot, Layers, Cpu, Activity } from "lucide-react";
import { Card } from "../common/Card";
import { KNOWN_AGENTS } from "../../data/agents";
import { useReserveX } from "../../context/ReserveXContext";

export const AgentGrid: React.FC = () => {
  const { options, allocations, events } = useReserveX();

  // Inspect activity per known agent
  const agentList = Object.values(KNOWN_AGENTS);

  return (
    <Card
      title={
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-purple-400" />
          <span>Simulated Agent Fleet & Active States</span>
        </div>
      }
      subtitle="Inferred runtime telemetry for simulated autonomous agents"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {agentList.map((agent) => {
          const agentOptions = options.filter((o) => o.agent_id === agent.id);
          const pendingOptions = agentOptions.filter((o) => o.status === "PENDING");
          const agentAllocations = allocations.filter(
            (a) => a.agent_id === agent.id && !a.released_at
          );
          const latestEvent = events.find((e) => e.agent_id === agent.id);

          // Highest predicted probability among pending options
          const highestProb =
            pendingOptions.length > 0
              ? Math.max(...pendingOptions.map((o) => o.probability))
              : null;

          const isActive =
            pendingOptions.length > 0 || agentAllocations.length > 0;

          return (
            <div
              key={agent.id}
              className={`rounded-xl border p-4 flex flex-col justify-between transition-all duration-200 ${
                isActive
                  ? "border-zinc-700 bg-zinc-950/60 shadow-md shadow-purple-950/10"
                  : "border-zinc-800/60 bg-zinc-950/30 opacity-80"
              }`}
            >
              <div>
                {/* Agent Header */}
                <div className="flex items-start justify-between gap-2 mb-3">
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
                    className={`h-2 w-2 rounded-full shrink-0 ${
                      isActive
                        ? "bg-emerald-400 shadow-sm shadow-emerald-400 animate-pulse"
                        : "bg-zinc-600"
                    }`}
                    title={isActive ? "Active in RESERVE-X" : "Idle"}
                  />
                </div>

                <p className="text-[11px] text-zinc-400 leading-snug line-clamp-2 mb-3">
                  {agent.role}
                </p>

                {/* Metrics */}
                <div className="space-y-2 border-t border-zinc-800/60 pt-2.5 text-xs font-mono">
                  <div className="flex items-center justify-between text-zinc-400">
                    <span className="flex items-center gap-1 text-[11px]">
                      <Layers className="h-3 w-3 text-cyan-400" />
                      Pending:
                    </span>
                    <strong className="text-cyan-300">
                      {pendingOptions.length}
                    </strong>
                  </div>

                  <div className="flex items-center justify-between text-zinc-400">
                    <span className="flex items-center gap-1 text-[11px]">
                      <Cpu className="h-3 w-3 text-emerald-400" />
                      Allocated:
                    </span>
                    <strong className="text-emerald-300">
                      {agentAllocations.length}
                    </strong>
                  </div>

                  {highestProb !== null && (
                    <div className="flex items-center justify-between text-zinc-400">
                      <span className="text-[11px]">Peak Prob:</span>
                      <strong className="text-purple-300">
                        {Math.round(highestProb * 100)}%
                      </strong>
                    </div>
                  )}
                </div>
              </div>

              {/* Latest Event Footer */}
              <div className="mt-3 pt-2 border-t border-zinc-800/60 text-[10px] font-mono text-zinc-500">
                <div className="flex items-center gap-1 text-zinc-400 truncate">
                  <Activity className="h-3 w-3 shrink-0 text-zinc-500" />
                  <span className="truncate">
                    {latestEvent
                      ? latestEvent.event_type.replace(/_/g, " ")
                      : "No events yet"}
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
