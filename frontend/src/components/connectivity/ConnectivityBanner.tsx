import React, { useEffect, useState } from "react";
import {
  Wifi,
  WifiOff,
  Clock,
  Layers,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Power,
} from "lucide-react";
import { useReserveX } from "../../context/ReserveXContext";

interface ConnectivityBannerProps {
  onNavigateToOfflinePage?: () => void;
}

export const ConnectivityBanner: React.FC<ConnectivityBannerProps> = ({
  onNavigateToOfflinePage,
}) => {
  const { connectivity, simulateDisconnect, reconnectAndSync, loading } =
    useReserveX();

  const isOfflineMode = connectivity?.mode === "OFFLINE";
  const outageStartedAt = connectivity?.outage_started_at;
  const stats = connectivity?.queue_stats || {
    total: 0,
    pending: 0,
    failed: 0,
    synced: 0,
  };

  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const [actionLoading, setActionLoading] = useState<boolean>(false);

  // Live timer for outage duration
  useEffect(() => {
    if (!isOfflineMode || !outageStartedAt) {
      setElapsedSeconds(0);
      return;
    }

    const updateTimer = () => {
      const startMs = new Date(outageStartedAt).getTime();
      const nowMs = Date.now();
      const diffSec = Math.max(0, Math.floor((nowMs - startMs) / 1000));
      setElapsedSeconds(diffSec);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [isOfflineMode, outageStartedAt]);

  const formatTimer = (totalSec: number): string => {
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const handleDisconnect = async () => {
    setActionLoading(true);
    await simulateDisconnect();
    setActionLoading(false);
  };

  const handleReconnect = async () => {
    setActionLoading(true);
    await reconnectAndSync();
    setActionLoading(false);
  };

  return (
    <div
      className={`border-b transition-colors px-6 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs font-mono ${
        isOfflineMode
          ? "bg-rose-950/40 border-rose-500/40 text-rose-200"
          : "bg-zinc-900/60 border-zinc-800/80 text-zinc-300"
      }`}
    >
      {/* Left: Mode & Outage Timer */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          {isOfflineMode ? (
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-rose-500/20 border border-rose-500/40 text-rose-300 font-bold tracking-wider animate-pulse">
              <WifiOff className="h-3.5 w-3.5" />
              <div className="flex items-center gap-1.5">
                <span>🔴 OFFLINE MODE</span>
                <span className="text-rose-400/50">|</span>
                <span className="font-semibold text-rose-200">
                  {connectivity?.offline_reason === "NETWORK_DISCONNECTED"
                    ? "Network disconnected"
                    : "Manual simulation"}
                </span>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-bold tracking-wider">
              <Wifi className="h-3.5 w-3.5" />
              <div className="flex items-center gap-1.5">
                <span>🟢 ONLINE</span>
                <span className="text-emerald-400/50">|</span>
                <span className="font-semibold text-emerald-200">Network connected</span>
              </div>
            </div>
          )}
        </div>

        {isOfflineMode && (
          <div className="flex items-center gap-1.5 text-rose-300 bg-rose-900/30 border border-rose-500/30 px-2.5 py-1 rounded-md">
            <Clock className="h-3.5 w-3.5 text-rose-400" />
            <span>Outage Duration:</span>
            <span className="font-bold text-rose-200 text-sm">
              {formatTimer(elapsedSeconds)}
            </span>
          </div>
        )}

        {/* Counter Pills */}
        <div className="flex items-center gap-3 text-zinc-400">
          <div
            className={`flex items-center gap-1.5 px-2 py-0.5 rounded border ${
              stats.pending > 0
                ? "bg-amber-500/20 border-amber-500/40 text-amber-300 font-semibold"
                : "bg-zinc-800/50 border-zinc-700/40 text-zinc-400"
            }`}
            title="Operations buffered in SQLite durable queue waiting for reconnect"
          >
            <Layers className="h-3 w-3" />
            <span>Queued:</span>
            <span className="font-bold">{stats.pending}</span>
          </div>

          <div
            className={`flex items-center gap-1.5 px-2 py-0.5 rounded border ${
              stats.failed > 0
                ? "bg-rose-500/20 border-rose-500/40 text-rose-300"
                : "bg-zinc-800/50 border-zinc-700/40 text-zinc-400"
            }`}
          >
            <AlertCircle className="h-3 w-3" />
            <span>Failed:</span>
            <span className="font-bold">{stats.failed}</span>
          </div>

          <div
            className={`flex items-center gap-1.5 px-2 py-0.5 rounded border ${
              stats.synced > 0
                ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300"
                : "bg-zinc-800/50 border-zinc-700/40 text-zinc-400"
            }`}
          >
            <CheckCircle2 className="h-3 w-3" />
            <span>Synced:</span>
            <span className="font-bold">{stats.synced}</span>
          </div>
        </div>
      </div>

      {/* Right: Quick Controls & Navigation */}
      <div className="flex items-center gap-3">
        {onNavigateToOfflinePage && (
          <button
            onClick={onNavigateToOfflinePage}
            className="text-cyan-400 hover:text-cyan-300 underline underline-offset-4 mr-2"
          >
            Resilience Console →
          </button>
        )}

        {isOfflineMode ? (
          <button
            onClick={handleReconnect}
            disabled={actionLoading || loading}
            className="flex items-center gap-1.5 rounded-lg border border-emerald-500/40 bg-emerald-500/20 px-3 py-1 font-semibold text-emerald-200 hover:bg-emerald-500/30 transition-colors disabled:opacity-50"
            title="Reconnect and trigger automatic synchronization of SQLite queue"
          >
            <RefreshCw
              className={`h-3.5 w-3.5 ${actionLoading ? "animate-spin" : ""}`}
            />
            <span>Reconnect & Sync</span>
          </button>
        ) : (
          <button
            onClick={handleDisconnect}
            disabled={actionLoading || loading}
            className="flex items-center gap-1.5 rounded-lg border border-rose-500/40 bg-rose-500/15 px-3 py-1 font-semibold text-rose-200 hover:bg-rose-500/25 transition-colors disabled:opacity-50"
            title="Simulate network outage without disconnecting computer"
          >
            <Power className="h-3.5 w-3.5" />
            <span>Simulate Disconnect</span>
          </button>
        )}
      </div>
    </div>
  );
};
