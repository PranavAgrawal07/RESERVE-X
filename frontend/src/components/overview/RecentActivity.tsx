import React from "react";
import { History, ArrowRight } from "lucide-react";
import { Card } from "../common/Card";
import { Badge } from "../common/Badge";
import { getAgentDisplayName } from "../../data/agents";
import { useReserveX } from "../../context/ReserveXContext";

interface RecentActivityProps {
  onNavigateToActivity: () => void;
}

export const RecentActivity: React.FC<RecentActivityProps> = ({
  onNavigateToActivity,
}) => {
  const { events } = useReserveX();

  const recentEvents = events.slice(0, 10);

  return (
    <Card
      title={
        <div className="flex items-center gap-2">
          <History className="h-4 w-4 text-cyan-400" />
          <span>Real-Time Event Stream</span>
        </div>
      }
      subtitle="Immutable operational event audit feed from backend store"
      action={
        <button
          onClick={onNavigateToActivity}
          className="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors"
        >
          <span>Full Audit Log</span>
          <ArrowRight className="h-3 w-3" />
        </button>
      }
    >
      {recentEvents.length === 0 ? (
        <div className="text-center py-6 text-zinc-500 font-mono text-xs">
          No system events logged yet. Trigger an action or wait for simulation.
        </div>
      ) : (
        <div className="space-y-2">
          {recentEvents.map((evt) => {
            const time = new Date(evt.timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            });

            let badgeVariant: "cyan" | "exercised" | "expired" | "cancelled" | "critical" | "default" = "default";
            if (evt.event_type.includes("CREATED")) badgeVariant = "cyan";
            else if (evt.event_type.includes("EXERCISED")) badgeVariant = "exercised";
            else if (evt.event_type.includes("EXPIRED")) badgeVariant = "expired";
            else if (evt.event_type.includes("CANCELLED")) badgeVariant = "cancelled";
            else if (evt.event_type.includes("FAILED")) badgeVariant = "critical";

            const agentName = getAgentDisplayName(evt.agent_id);

            return (
              <div
                key={evt.id}
                className="flex items-center justify-between gap-4 p-2.5 rounded-lg border border-zinc-800/60 bg-zinc-950/40 hover:bg-zinc-900/50 transition-colors text-xs"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="font-mono text-[11px] text-zinc-500 shrink-0">
                    {time}
                  </span>
                  <Badge variant={badgeVariant} size="sm">
                    {evt.event_type}
                  </Badge>
                  <span className="font-medium text-zinc-200 truncate">
                    {agentName}
                  </span>
                  {evt.details?.capability && (
                    <span className="text-[11px] font-mono text-zinc-400 hidden md:inline">
                      {evt.details.capability}
                    </span>
                  )}
                  {evt.details?.reason && (
                    <span className="text-[11px] text-rose-400 font-mono">
                      ({evt.details.reason})
                    </span>
                  )}
                </div>

                <div className="font-mono text-[11px] text-zinc-500 shrink-0">
                  {evt.option_id ? `opt:${evt.option_id.substring(0, 8)}` : ""}
                  {evt.resource_id ? `res:${evt.resource_id.substring(0, 8)}` : ""}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
};
