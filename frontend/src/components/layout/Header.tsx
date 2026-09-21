import React from "react";
import {
  RefreshCw,
  Zap,
  Radio,
} from "lucide-react";
import { useReserveX } from "../../context/ReserveXContext";

export const Header: React.FC = () => {
  const {
    isOnline,
    lastUpdated,
    loading,
    refresh,
    isPolling,
    togglePolling,
  } = useReserveX();

  const formattedTime = lastUpdated
    ? lastUpdated.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    : "Never";

  return (
    <header className="sticky top-0 z-40 w-full border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-xl">
      <div className="flex h-16 items-center justify-between px-6">
        {/* Brand & Tagline */}
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-cyan-500/40 bg-cyan-500/10 text-cyan-400 shadow-md shadow-cyan-950/30">
            <Zap className="h-5 w-5 fill-cyan-400/20" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-base font-bold tracking-wider text-zinc-100">
                RESERVE-X
              </span>
              <span className="rounded bg-zinc-800/80 px-1.5 py-0.5 text-[10px] font-mono text-cyan-400 border border-zinc-700/50">
                v0.1.0
              </span>
            </div>
            <p className="text-[11px] font-medium tracking-wide text-zinc-400 hidden sm:block">
              Conditional Resource Reservation for Autonomous AI Workflows
            </p>
          </div>
        </div>

        {/* System Controls & Connection Status */}
        <div className="flex items-center gap-4">
          {/* Connection Status Indicator */}
          <div
            className={`flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-mono transition-all ${
              isOnline
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                : "border-rose-500/30 bg-rose-500/10 text-rose-400 animate-pulse"
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                isOnline
                  ? "bg-emerald-400 shadow-sm shadow-emerald-400"
                  : "bg-rose-400 shadow-sm shadow-rose-400"
              }`}
            />
            <span className="font-medium">
              {isOnline ? "Backend Online" : "Backend Offline"}
            </span>
          </div>

          {/* Polling Mode Indicator */}
          <button
            onClick={togglePolling}
            title={isPolling ? "Live polling active (every 2s). Click to pause." : "Polling paused. Click to resume."}
            className={`hidden md:flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-mono transition-colors ${
              isPolling
                ? "border-cyan-500/30 bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20"
                : "border-zinc-800 bg-zinc-900 text-zinc-500 hover:text-zinc-300"
            }`}
          >
            <Radio className={`h-3 w-3 ${isPolling ? "animate-pulse" : ""}`} />
            <span>{isPolling ? "2s Live Sync" : "Sync Paused"}</span>
          </button>

          {/* Timestamp */}
          <div className="hidden lg:flex items-center gap-1.5 text-xs font-mono text-zinc-400">
            <span>Sync:</span>
            <span className="text-zinc-200">{formattedTime}</span>
          </div>

          {/* Manual Refresh Button */}
          <button
            onClick={() => refresh()}
            disabled={loading}
            title="Force refresh backend status"
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-900/80 text-zinc-300 hover:border-zinc-700 hover:bg-zinc-800 hover:text-white transition-all disabled:opacity-50"
          >
            <RefreshCw
              className={`h-3.5 w-3.5 ${loading ? "animate-spin text-cyan-400" : ""}`}
            />
          </button>
        </div>
      </div>
    </header>
  );
};
