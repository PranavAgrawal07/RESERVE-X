import React, { useState } from "react";
import {
  Server,
  Plus,
  BarChart3,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card } from "../common/Card";
import { Badge } from "../common/Badge";
import { AddResourceModal } from "./AddResourceModal";
import { useReserveX } from "../../context/ReserveXContext";

export const ResourceList: React.FC = () => {
  const { resources, allocations } = useReserveX();
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Prepare chart data
  const chartData = resources.map((r) => ({
    name: r.name,
    Allocated: r.allocated_capacity,
    Available: r.available_capacity,
    Total: r.total_capacity,
    capability: r.capability,
    utilization:
      r.total_capacity > 0
        ? Math.round((r.allocated_capacity / r.total_capacity) * 100)
        : 0,
  }));

  const totalCapacity = resources.reduce((acc, r) => acc + r.total_capacity, 0);
  const totalAllocated = resources.reduce(
    (acc, r) => acc + r.allocated_capacity,
    0
  );
  const totalAvailable = Math.max(0, totalCapacity - totalAllocated);

  return (
    <div className="space-y-6">
      {/* Top Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
            <Server className="h-5 w-5 text-cyan-400" />
            <span>Resource Pools & Infrastructure</span>
          </h2>
          <p className="text-xs text-zinc-400 mt-1">
            Registered execution environments providing scarce capabilities to AI agents.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 rounded-xl border border-cyan-500/40 bg-cyan-500/10 px-4 py-2 text-xs font-mono font-semibold text-cyan-200 hover:bg-cyan-500/20 shadow-lg shadow-cyan-950/20 transition-all"
        >
          <Plus className="h-4 w-4" />
          <span>Add Resource</span>
        </button>
      </div>

      {/* Aggregate KPI Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
          <span className="text-[11px] font-mono text-zinc-400 uppercase block">
            Total Hardware Capacity
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-zinc-100">
              {totalCapacity}
            </span>
            <span className="text-xs text-zinc-500 font-mono">
              across {resources.length} pools
            </span>
          </div>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
          <span className="text-[11px] font-mono text-zinc-400 uppercase block">
            Currently Allocated
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-cyan-400">
              {totalAllocated}
            </span>
            <span className="text-xs text-zinc-500 font-mono">
              (
              {totalCapacity > 0
                ? Math.round((totalAllocated / totalCapacity) * 100)
                : 0}
              % locked)
            </span>
          </div>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
          <span className="text-[11px] font-mono text-zinc-400 uppercase block">
            Free Available Capacity
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-bold font-mono text-emerald-400">
              {totalAvailable}
            </span>
            <span className="text-xs text-zinc-500 font-mono">
              (
              {totalCapacity > 0
                ? Math.round((totalAvailable / totalCapacity) * 100)
                : 100}
              % headroom)
            </span>
          </div>
        </div>
      </div>

      {/* Recharts Capacity Distribution Visualization */}
      {resources.length > 0 && (
        <Card
          title={
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-cyan-400" />
              <span>Pool Capacity Utilization (Allocated vs Available)</span>
            </div>
          }
          subtitle="Real-time capacity allocation per resource pool"
        >
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 10, right: 30, left: 40, bottom: 5 }}
              >
                <XAxis type="number" stroke="#71717a" fontSize={11} />
                <YAxis
                  dataKey="name"
                  type="category"
                  stroke="#a1a1aa"
                  fontSize={11}
                  tickLine={false}
                  width={140}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#18181b",
                    borderColor: "#3f3f46",
                    borderRadius: "8px",
                    color: "#f4f4f5",
                    fontSize: "12px",
                    fontFamily: "monospace",
                  }}
                />
                <Legend wrapperStyle={{ fontSize: "11px", fontFamily: "monospace" }} />
                <Bar
                  dataKey="Allocated"
                  stackId="a"
                  fill="#06b6d4"
                  radius={[0, 0, 0, 0]}
                />
                <Bar
                  dataKey="Available"
                  stackId="a"
                  fill="#10b981"
                  radius={[0, 4, 4, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}

      {/* Resource Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {resources.map((res) => {
          const total = res.total_capacity;
          const allocated = res.allocated_capacity;
          const available = res.available_capacity;
          const utilization =
            total > 0 ? Math.round((allocated / total) * 100) : 0;

          // Find active allocations using this resource
          const activeOnResource = allocations.filter(
            (a) => a.resource_id === res.id && !a.released_at
          );

          let barColor = "bg-cyan-500";
          if (utilization >= 90) barColor = "bg-rose-500";
          else if (utilization >= 70) barColor = "bg-amber-500";
          else if (utilization > 0) barColor = "bg-emerald-500";

          return (
            <div
              key={res.id}
              className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 flex flex-col justify-between hover:border-cyan-500/30 transition-all shadow-md"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div>
                    <h3 className="font-semibold text-base text-zinc-100">
                      {res.name}
                    </h3>
                    <span className="font-mono text-[10px] text-zinc-500">
                      ID: {res.id.substring(0, 13)}...
                    </span>
                  </div>
                  <Badge variant="cyan">{res.capability}</Badge>
                </div>

                {/* Capacity Meter */}
                <div className="my-4 space-y-2">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-zinc-400">Capacity Meter</span>
                    <span
                      className={`font-semibold ${
                        utilization >= 90
                          ? "text-rose-400"
                          : utilization >= 70
                          ? "text-amber-400"
                          : "text-cyan-400"
                      }`}
                    >
                      {utilization}% Utilized
                    </span>
                  </div>
                  <div className="h-2 w-full bg-zinc-800 rounded-full overflow-hidden p-0.5 border border-zinc-700/40">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${barColor}`}
                      style={{ width: `${utilization}%` }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 py-3 border-y border-zinc-800/60 text-center font-mono">
                  <div className="p-2 rounded-lg bg-zinc-950/60 border border-zinc-800/50">
                    <span className="text-[10px] text-zinc-500 uppercase block">
                      Total
                    </span>
                    <strong className="text-sm text-zinc-200">{total}</strong>
                  </div>
                  <div className="p-2 rounded-lg bg-zinc-950/60 border border-zinc-800/50">
                    <span className="text-[10px] text-zinc-500 uppercase block">
                      Allocated
                    </span>
                    <strong className="text-sm text-cyan-400">
                      {allocated}
                    </strong>
                  </div>
                  <div className="p-2 rounded-lg bg-zinc-950/60 border border-zinc-800/50">
                    <span className="text-[10px] text-zinc-500 uppercase block">
                      Available
                    </span>
                    <strong className="text-sm text-emerald-400">
                      {available}
                    </strong>
                  </div>
                </div>

                {/* Active Consumers */}
                <div className="mt-3 text-xs">
                  <span className="text-[11px] font-mono text-zinc-500 block mb-1">
                    Active Consumers ({activeOnResource.length}):
                  </span>
                  {activeOnResource.length === 0 ? (
                    <span className="text-zinc-500 text-xs italic font-mono">
                      No active allocations
                    </span>
                  ) : (
                    <div className="flex flex-wrap gap-1.5">
                      {activeOnResource.map((a) => (
                        <span
                          key={a.id}
                          className="px-2 py-0.5 rounded bg-zinc-800 text-[11px] font-mono text-zinc-300 border border-zinc-700/60"
                        >
                          {a.agent_id} ({a.amount}u)
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-zinc-800/50 text-[10px] font-mono text-zinc-500 flex justify-between">
                <span>Registered:</span>
                <span>{new Date(res.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          );
        })}
      </div>

      <AddResourceModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
};
