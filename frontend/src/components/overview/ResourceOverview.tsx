import React from "react";
import { Server, ArrowRight } from "lucide-react";
import { Card } from "../common/Card";
import { Badge } from "../common/Badge";
import { useReserveX } from "../../context/ReserveXContext";

interface ResourceOverviewProps {
  onNavigateToResources: () => void;
}

export const ResourceOverview: React.FC<ResourceOverviewProps> = ({
  onNavigateToResources,
}) => {
  const { resources } = useReserveX();

  return (
    <Card
      title={
        <div className="flex items-center gap-2">
          <Server className="h-4 w-4 text-cyan-400" />
          <span>Scarce Resource Pools & Utilization</span>
        </div>
      }
      subtitle="Real-time capacity tracking across all registered hardware and service pools"
      action={
        <button
          onClick={onNavigateToResources}
          className="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors"
        >
          <span>Manage Resources</span>
          <ArrowRight className="h-3 w-3" />
        </button>
      }
    >
      {resources.length === 0 ? (
        <div className="text-center py-8 border border-dashed border-zinc-800 rounded-xl">
          <Server className="h-8 w-8 text-zinc-600 mx-auto mb-2" />
          <p className="text-sm font-medium text-zinc-400">
            No resources registered yet
          </p>
          <p className="text-xs text-zinc-500 mt-1">
            Register scarce hardware pools or APIs in the Resources tab.
          </p>
          <button
            onClick={onNavigateToResources}
            className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-cyan-500/40 bg-cyan-500/10 text-cyan-300 text-xs font-mono hover:bg-cyan-500/20 transition-all"
          >
            <span>+ Add Resource</span>
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {resources.map((res) => {
            const total = res.total_capacity;
            const allocated = res.allocated_capacity;
            const available = res.available_capacity;
            const utilization =
              total > 0 ? Math.round((allocated / total) * 100) : 0;

            let barColor = "bg-cyan-500";
            if (utilization >= 90) barColor = "bg-rose-500";
            else if (utilization >= 70) barColor = "bg-amber-500";
            else if (utilization > 0) barColor = "bg-emerald-500";

            return (
              <div
                key={res.id}
                className="p-3.5 rounded-xl border border-zinc-800/70 bg-zinc-950/40 hover:border-zinc-700/80 transition-all"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm text-zinc-100">
                      {res.name}
                    </span>
                    <Badge variant="cyan">{res.capability}</Badge>
                  </div>
                  <div className="flex items-center gap-3 text-xs font-mono">
                    <span className="text-zinc-400">
                      Allocated:{" "}
                      <strong className="text-zinc-100">{allocated}</strong> / {total}
                    </span>
                    <span className="text-emerald-400 font-semibold">
                      {available} Available
                    </span>
                    <span className="text-zinc-400">
                      Utilization:{" "}
                      <strong
                        className={
                          utilization >= 90
                            ? "text-rose-400"
                            : utilization >= 70
                            ? "text-amber-400"
                            : "text-cyan-400"
                        }
                      >
                        {utilization}%
                      </strong>
                    </span>
                  </div>
                </div>

                {/* Capacity Progress Bar */}
                <div className="w-full bg-zinc-800/80 h-2.5 rounded-full overflow-hidden p-0.5 border border-zinc-700/40">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${barColor}`}
                    style={{ width: `${Math.min(100, Math.max(0, utilization))}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
};
