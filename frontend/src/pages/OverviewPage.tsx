import React from "react";
import { LiveSimulationControls } from "../components/simulation/LiveSimulationControls";
import { KpiCards } from "../components/overview/KpiCards";
import { ResourceOverview } from "../components/overview/ResourceOverview";
import { RiskOverview } from "../components/overview/RiskOverview";
import { AgentGrid } from "../components/overview/AgentGrid";
import { RecentActivity } from "../components/overview/RecentActivity";
import { AllocationsTable } from "../components/allocations/AllocationsTable";
import { Card } from "../components/common/Card";
import { Cpu } from "lucide-react";

interface OverviewPageProps {
  onNavigate: (tab: string) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({ onNavigate }) => {
  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
          Operations Command Center
        </h1>
        <p className="text-xs text-zinc-400 mt-1">
          Executive view — conditional resource reservation system for autonomous AI agent workflows
        </p>
      </div>

      {/* Live Autonomous Simulation Runner Bar */}
      <LiveSimulationControls />

      {/* KPI Row */}
      <KpiCards />

      {/* Two-column: Resources + Risk */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ResourceOverview onNavigateToResources={() => onNavigate("resources")} />
        <RiskOverview onNavigateToRisk={() => onNavigate("risk")} />
      </div>

      {/* Agent Grid */}
      <AgentGrid />

      {/* Allocations + Recent Activity side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card
          title={
            <div className="flex items-center gap-2">
              <Cpu className="h-4 w-4 text-emerald-400" />
              <span>Active Allocations</span>
            </div>
          }
          subtitle="Exercised options consuming real resource capacity"
        >
          <AllocationsTable />
        </Card>

        <RecentActivity onNavigateToActivity={() => onNavigate("activity")} />
      </div>
    </div>
  );
};
