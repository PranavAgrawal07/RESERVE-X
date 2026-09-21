import React from "react";
import type { OptionStatus, RiskLevel } from "../../types/reservex";

interface BadgeProps {
  children: React.ReactNode;
  variant?:
    | "default"
    | "low"
    | "medium"
    | "high"
    | "critical"
    | "pending"
    | "exercised"
    | "expired"
    | "cancelled"
    | "cyan"
    | "purple"
    | "sky";
  size?: "sm" | "md";
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "default",
  size = "sm",
  className = "",
}) => {
  const sizeClasses =
    size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-xs font-semibold";

  let colorClasses = "bg-zinc-800/60 text-zinc-300 border-zinc-700/60";

  switch (variant) {
    case "low":
      colorClasses = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
      break;
    case "medium":
      colorClasses = "bg-amber-500/10 text-amber-400 border-amber-500/30";
      break;
    case "high":
      colorClasses = "bg-orange-500/10 text-orange-400 border-orange-500/30";
      break;
    case "critical":
      colorClasses = "bg-rose-500/10 text-rose-400 border-rose-500/30 animate-pulse";
      break;
    case "pending":
      colorClasses = "bg-cyan-500/10 text-cyan-400 border-cyan-500/30";
      break;
    case "exercised":
      colorClasses = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
      break;
    case "expired":
      colorClasses = "bg-zinc-800/80 text-zinc-400 border-zinc-700/60";
      break;
    case "cancelled":
      colorClasses = "bg-slate-800/60 text-slate-400 border-slate-700/50";
      break;
    case "cyan":
      colorClasses = "bg-cyan-500/10 text-cyan-300 border-cyan-500/30";
      break;
    case "purple":
      colorClasses = "bg-purple-500/10 text-purple-300 border-purple-500/30";
      break;
    case "sky":
      colorClasses = "bg-sky-500/10 text-sky-300 border-sky-500/30";
      break;
  }

  return (
    <span
      className={`inline-flex items-center gap-1 font-mono uppercase tracking-wider rounded-md border backdrop-blur-sm ${sizeClasses} ${colorClasses} ${className}`}
    >
      {children}
    </span>
  );
};

export const RiskBadge: React.FC<{ level?: RiskLevel | string }> = ({
  level,
}) => {
  const normalized = (level || "LOW").toUpperCase();
  let variant: "low" | "medium" | "high" | "critical" = "low";
  if (normalized === "MEDIUM") variant = "medium";
  else if (normalized === "HIGH") variant = "high";
  else if (normalized === "CRITICAL") variant = "critical";

  return <Badge variant={variant}>{normalized}</Badge>;
};

export const StatusBadge: React.FC<{ status: OptionStatus | string }> = ({
  status,
}) => {
  const normalized = (status || "PENDING").toUpperCase();
  let variant: "pending" | "exercised" | "expired" | "cancelled" = "pending";
  if (normalized === "EXERCISED") variant = "exercised";
  else if (normalized === "EXPIRED") variant = "expired";
  else if (normalized === "CANCELLED") variant = "cancelled";

  return <Badge variant={variant}>{normalized}</Badge>;
};
