import React from "react";
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
import { BarChart3 } from "lucide-react";
import { useReserveX } from "../../context/ReserveXContext";

export const RiskDemandChart: React.FC = () => {
  const { risk } = useReserveX();

  const capRisks = risk?.capability_risks || [];

  if (capRisks.length === 0) {
    return null;
  }

  const chartData = capRisks.map((cr) => ({
    capability: cr.capability.replace(/_/g, " "),
    "Expected Demand": parseFloat(cr.expected_demand.toFixed(2)),
    "Available Capacity": cr.available_capacity,
    "Allocated Capacity": cr.allocated_capacity,
    "Total Pending Demand": cr.total_pending_demand,
  }));

  return (
    <Card
      title={
        <div className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-cyan-400" />
          <span>Expected Demand vs Available Capacity</span>
        </div>
      }
      subtitle="Recharts visualization comparing probabilistic demand against remaining pool headroom"
    >
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 10, right: 30, left: 10, bottom: 5 }}
          >
            <XAxis
              dataKey="capability"
              stroke="#a1a1aa"
              fontSize={10}
              tickLine={false}
              tick={{ fill: "#a1a1aa" }}
            />
            <YAxis
              stroke="#71717a"
              fontSize={11}
              tickLine={false}
              tick={{ fill: "#a1a1aa" }}
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
            <Legend
              wrapperStyle={{ fontSize: "11px", fontFamily: "monospace" }}
            />
            <Bar
              dataKey="Expected Demand"
              fill="#f59e0b"
              radius={[4, 4, 0, 0]}
              barSize={28}
            />
            <Bar
              dataKey="Available Capacity"
              fill="#10b981"
              radius={[4, 4, 0, 0]}
              barSize={28}
            />
            <Bar
              dataKey="Allocated Capacity"
              fill="#06b6d4"
              radius={[4, 4, 0, 0]}
              barSize={28}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};
