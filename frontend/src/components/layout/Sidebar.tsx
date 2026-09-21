import React from "react";
import {
  LayoutDashboard,
  Server,
  Layers,
  ShieldAlert,
  History,
  CheckCircle2,
} from "lucide-react";
import { useReserveX } from "../../context/ReserveXContext";

interface SidebarProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onTabChange,
}) => {
  const { options, allocations, risk } = useReserveX();

  const pendingCount = options.filter((o) => o.status === "PENDING").length;
  const allocationCount = allocations.filter((a) => !a.released_at).length;
  const isHighRisk =
    risk?.highest_risk_level === "HIGH" ||
    risk?.highest_risk_level === "CRITICAL";

  const navItems = [
    {
      id: "overview",
      label: "Overview",
      icon: LayoutDashboard,
      badge: null,
    },
    {
      id: "resources",
      label: "Resources",
      icon: Server,
      badge: null,
    },
    {
      id: "reservations",
      label: "Reservations",
      icon: Layers,
      badge: pendingCount > 0 ? pendingCount : null,
      badgeColor: "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30",
    },
    {
      id: "risk",
      label: "Risk & Conflict",
      icon: ShieldAlert,
      badge: isHighRisk ? risk?.highest_risk_level : null,
      badgeColor:
        risk?.highest_risk_level === "CRITICAL"
          ? "bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse"
          : "bg-orange-500/20 text-orange-300 border border-orange-500/40",
    },
    {
      id: "activity",
      label: "Activity Log",
      icon: History,
      badge: null,
    },
  ];

  return (
    <aside className="w-64 shrink-0 border-r border-zinc-800/80 bg-zinc-950/40 flex flex-col justify-between py-6 px-3">
      <div className="space-y-1">
        <div className="px-3 pb-2 text-[11px] font-mono uppercase tracking-wider text-zinc-500 font-semibold">
          Operations Console
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all duration-150 ${
                isActive
                  ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 shadow-sm shadow-cyan-950/20"
                  : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900/60 border border-transparent"
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={`h-4 w-4 ${
                    isActive ? "text-cyan-400" : "text-zinc-400"
                  }`}
                />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span
                  className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded-md ${
                    item.badgeColor || "bg-zinc-800 text-zinc-300"
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Semantic Pipeline Card */}
      <div className="mx-2 p-3.5 rounded-xl border border-zinc-800/70 bg-zinc-900/40 text-xs">
        <div className="font-mono text-[11px] text-zinc-400 uppercase tracking-wider flex items-center gap-1.5 mb-2 font-semibold">
          <CheckCircle2 className="h-3.5 w-3.5 text-cyan-400" />
          <span>RESERVE-X Core</span>
        </div>
        <div className="space-y-1 text-[11px] font-mono text-zinc-400">
          <div className="flex justify-between">
            <span>Allocations:</span>
            <span className="text-zinc-200">{allocationCount} Active</span>
          </div>
          <div className="flex justify-between">
            <span>Pending Demand:</span>
            <span className="text-cyan-300">{pendingCount} Options</span>
          </div>
          <div className="flex justify-between">
            <span>System State:</span>
            <span className={isHighRisk ? "text-orange-400" : "text-emerald-400"}>
              {risk?.highest_risk_level || "NOMINAL"}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
};
