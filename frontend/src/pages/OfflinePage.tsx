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
  Play,
  Database,
  ArrowDown,
  Server,
  Zap,
  ShieldCheck,
} from "lucide-react";
import { api } from "../services/api";
import { useReserveX } from "../context/ReserveXContext";
import type {
  QueuedOperation,
  OfflineEventLog,
  ResourceOption,
  ReconnectResponse,
} from "../types/reservex";

export const OfflinePage: React.FC = () => {
  const {
    connectivity,
    lastSyncResult: contextLastSyncResult,
    simulateDisconnect,
    reconnectAndSync,
    refresh,
    addToast,
  } = useReserveX();

  const isOfflineMode = connectivity?.mode === "OFFLINE";
  const outageStartedAt = connectivity?.outage_started_at;
  const stats = connectivity?.queue_stats || {
    total: 0,
    pending: 0,
    failed: 0,
    synced: 0,
  };

  const [queue, setQueue] = useState<QueuedOperation[]>([]);
  const [offlineEvents, setOfflineEvents] = useState<OfflineEventLog[]>([]);
  const [loadingAction, setLoadingAction] = useState<boolean>(false);
  const [lastCreatedOption, setLastCreatedOption] =
    useState<ResourceOption | null>(null);
  const [lastSyncResult, setLastSyncResult] =
    useState<ReconnectResponse | null>(null);
  const activeSyncResult = contextLastSyncResult || lastSyncResult;
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);

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

  // Fetch local queue and events
  const loadQueueAndEvents = async () => {
    try {
      const [queueData, eventsData] = await Promise.all([
        api.getConnectivityQueue(),
        api.getOfflineEvents(),
      ]);
      setQueue(queueData);
      setOfflineEvents(eventsData);
    } catch {
      // Ignore network errors when polling
    }
  };

  useEffect(() => {
    loadQueueAndEvents();
    const interval = setInterval(loadQueueAndEvents, 2000);
    return () => clearInterval(interval);
  }, [connectivity?.mode]);

  // Handler: Simulate Disconnect
  const handleSimulateDisconnect = async () => {
    setLoadingAction(true);
    setLastSyncResult(null);
    await simulateDisconnect();
    await loadQueueAndEvents();
    setLoadingAction(false);
  };

  // Handler: Reconnect & Sync
  const handleReconnectAndSync = async () => {
    setLoadingAction(true);
    const res = await reconnectAndSync();
    if (res) {
      setLastSyncResult(res);
    }
    await loadQueueAndEvents();
    setLoadingAction(false);
  };

  // Handler: Test Offline Operation (Calls real POST /api/v1/options)
  const handleCreateOfflineOption = async () => {
    setLoadingAction(true);
    try {
      const futureExpiry = new Date(Date.now() + 60 * 60 * 1000).toISOString();
      const opt = await api.createOption({
        agent_id: "Offline-Demo-Agent",
        capability: "GPU_COMPUTE",
        probability: 0.85,
        amount: 1,
        priority: 5,
        expires_at: futureExpiry,
      });

      setLastCreatedOption(opt);
      addToast({
        type: "success",
        title: isOfflineMode
          ? "Option Recorded Locally in SQLite"
          : "Option Created Online",
        message: isOfflineMode
          ? `Captured in durable queue (ID: ${opt.id.slice(0, 8)}...). Ready for reconciliation.`
          : `Created directly in RESERVE-X live engine.`,
      });

      await refresh();
      await loadQueueAndEvents();
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Operation Failed",
        message: err?.message || "Failed to create resource option.",
      });
    } finally {
      setLoadingAction(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-violet-500/10 border border-violet-500/30 text-violet-400">
            <WifiOff className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold tracking-tight text-zinc-100 flex items-center gap-3">
              <span>Intermittent Connectivity & Offline Resilience</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-violet-500/20 text-violet-300 border border-violet-500/40 font-bold uppercase">
                Donut Challenge
              </span>
            </h2>
            <p className="text-xs text-zinc-400 mt-0.5">
              Demonstrates uninterrupted agent execution, SQLite persistence,
              and automatic reconciliation across temporary network outages.
            </p>
          </div>
        </div>
      </div>

      {/* Official Challenge Explanation Banner */}
      <div className="rounded-xl border border-cyan-500/30 bg-cyan-950/20 p-5 shadow-lg shadow-cyan-950/20">
        <div className="flex items-start gap-3.5">
          <ShieldCheck className="h-6 w-6 text-cyan-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-sm font-semibold text-cyan-200">
              Core Resilience Guarantee
            </h4>
            <p className="text-xs text-cyan-100/90 leading-relaxed font-sans">
              “RESERVE-X continues critical resource-option workflows during
              temporary connectivity loss using local processing and durable
              SQLite persistence, then automatically synchronizes when
              connectivity is restored.”
            </p>
          </div>
        </div>
      </div>

      {/* Main Interactive Control Panel */}
      <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/50 p-6 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-zinc-800/70">
          {/* Status Badge & Outage Duration */}
          <div className="flex items-center gap-4 flex-wrap">
            <div className="space-y-1">
              <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-500 font-semibold">
                Connectivity State
              </div>
              {isOfflineMode ? (
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-rose-500/20 border border-rose-500/50 text-rose-200 font-mono font-bold tracking-wider text-sm animate-pulse shadow-sm shadow-rose-950/50">
                  <WifiOff className="h-4 w-4 text-rose-400" />
                  <div className="flex items-center gap-2">
                    <span>🔴 OFFLINE MODE</span>
                    <span className="text-rose-400/50">|</span>
                    <span className="font-semibold text-rose-200 text-xs">
                      {connectivity?.offline_reason === "NETWORK_DISCONNECTED"
                        ? "Network disconnected"
                        : "Manual simulation"}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-200 font-mono font-bold tracking-wider text-sm shadow-sm shadow-emerald-950/50">
                  <Wifi className="h-4 w-4 text-emerald-400" />
                  <div className="flex items-center gap-2">
                    <span>🟢 ONLINE</span>
                    <span className="text-emerald-400/50">|</span>
                    <span className="font-semibold text-emerald-200 text-xs">Network connected</span>
                  </div>
                </div>
              )}
              <div className="text-[10px] text-zinc-500 font-mono">
                {isOfflineMode
                  ? connectivity?.offline_reason === "NETWORK_DISCONNECTED"
                    ? "Detected via hardware / browser network events"
                    : "Simulated via interactive test controls"
                  : "Live connection to core RESERVE-X engine"}
              </div>
            </div>

            {isOfflineMode && (
              <div className="space-y-1">
                <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-500 font-semibold">
                  Outage Duration
                </div>
                <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-rose-900/40 border border-rose-500/40 text-rose-200 font-mono font-bold text-base">
                  <Clock className="h-4 w-4 text-rose-400 animate-spin" />
                  <span>{formatTimer(elapsedSeconds)}</span>
                  <span className="text-[10px] text-rose-400/80 font-normal">
                    {elapsedSeconds >= 60 ? "(≥ 1 min passed)" : "(testing)"}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Action Trigger Buttons */}
          <div className="flex items-center gap-3 flex-wrap">
            {isOfflineMode ? (
              <>
                <button
                  onClick={handleCreateOfflineOption}
                  disabled={loadingAction}
                  className="flex items-center gap-2 rounded-xl border border-amber-500/50 bg-amber-500/20 px-5 py-2.5 text-xs font-mono font-bold text-amber-200 hover:bg-amber-500/30 hover:border-amber-400 transition-all shadow-md shadow-amber-950/30 disabled:opacity-50"
                  title="Issue real option request through backend while offline"
                >
                  <Play
                    className={`h-4 w-4 text-amber-400 ${
                      loadingAction ? "animate-spin" : ""
                    }`}
                  />
                  <span>Create Offline Option</span>
                </button>

                <button
                  onClick={handleReconnectAndSync}
                  disabled={loadingAction}
                  className="flex items-center gap-2 rounded-xl border border-emerald-500/50 bg-emerald-600/25 px-5 py-2.5 text-xs font-mono font-bold text-emerald-200 hover:bg-emerald-600/35 hover:border-emerald-400 transition-all shadow-md shadow-emerald-950/40 disabled:opacity-50"
                  title="Restore connection and trigger automatic reconciliation"
                >
                  <RefreshCw
                    className={`h-4 w-4 text-emerald-400 ${
                      loadingAction ? "animate-spin" : ""
                    }`}
                  />
                  <span>Reconnect & Sync</span>
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={handleCreateOfflineOption}
                  disabled={loadingAction}
                  className="flex items-center gap-2 rounded-xl border border-cyan-500/40 bg-cyan-500/15 px-4 py-2 text-xs font-mono font-semibold text-cyan-200 hover:bg-cyan-500/25 transition-all disabled:opacity-50"
                  title="Test standard online option creation"
                >
                  <Play className="h-3.5 w-3.5 text-cyan-400" />
                  <span>Test Option (Online)</span>
                </button>

                <button
                  onClick={handleSimulateDisconnect}
                  disabled={loadingAction}
                  className="flex items-center gap-2 rounded-xl border border-rose-500/50 bg-rose-500/20 px-5 py-2.5 text-xs font-mono font-bold text-rose-200 hover:bg-rose-500/30 hover:border-rose-400 transition-all shadow-md shadow-rose-950/30 disabled:opacity-50"
                  title="Simulate connection loss in backend"
                >
                  <Power className="h-4 w-4 text-rose-400" />
                  <span>Simulate Disconnect</span>
                </button>
              </>
            )}
          </div>
        </div>

        {/* Live Counters */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-5">
          <div className="p-3.5 rounded-xl border border-zinc-800 bg-zinc-950/50">
            <div className="flex items-center justify-between text-xs text-zinc-400 font-mono">
              <span>SQLite Queued</span>
              <Layers className="h-4 w-4 text-amber-400" />
            </div>
            <div className="mt-2 text-2xl font-mono font-bold text-amber-300">
              {stats.pending}
            </div>
            <p className="text-[10px] text-zinc-500 mt-0.5">
              Buffered offline operations
            </p>
          </div>

          <div className="p-3.5 rounded-xl border border-zinc-800 bg-zinc-950/50">
            <div className="flex items-center justify-between text-xs text-zinc-400 font-mono">
              <span>Synced Operations</span>
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="mt-2 text-2xl font-mono font-bold text-emerald-300">
              {stats.synced}
            </div>
            <p className="text-[10px] text-zinc-500 mt-0.5">
              Reconciled with core engine
            </p>
          </div>

          <div className="p-3.5 rounded-xl border border-zinc-800 bg-zinc-950/50">
            <div className="flex items-center justify-between text-xs text-zinc-400 font-mono">
              <span>Failed Retries</span>
              <AlertCircle className="h-4 w-4 text-rose-400" />
            </div>
            <div className="mt-2 text-2xl font-mono font-bold text-rose-300">
              {stats.failed}
            </div>
            <p className="text-[10px] text-zinc-500 mt-0.5">
              Preserved for next retry
            </p>
          </div>

          <div className="p-3.5 rounded-xl border border-zinc-800 bg-zinc-950/50">
            <div className="flex items-center justify-between text-xs text-zinc-400 font-mono">
              <span>Total Captured</span>
              <Database className="h-4 w-4 text-cyan-400" />
            </div>
            <div className="mt-2 text-2xl font-mono font-bold text-cyan-300">
              {stats.total}
            </div>
            <p className="text-[10px] text-zinc-500 mt-0.5">
              Lifetime SQLite records
            </p>
          </div>
        </div>

        {/* Sync Result Banner (Shown after Reconnect & Sync or real Wi-Fi return) */}
        {activeSyncResult && (
          <div className="mt-5 p-4 rounded-xl border border-emerald-500/40 bg-emerald-950/30 text-emerald-200 flex flex-wrap items-center justify-between gap-3 shadow-md shadow-emerald-950/20">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />
              <div>
                <div className="text-sm font-bold font-mono">
                  Synchronization Complete
                </div>
                <div className="text-xs text-emerald-300/80 font-mono">
                  Outage:{" "}
                  {activeSyncResult.outage_duration_seconds
                    ? `${activeSyncResult.outage_duration_seconds.toFixed(1)}s`
                    : "instant"}{" "}
                  | Reconciled without data loss or duplicates.
                </div>
              </div>
            </div>
            <div className="flex items-center gap-4 text-xs font-mono">
              <span className="px-2.5 py-1 rounded bg-emerald-500/20 border border-emerald-500/30">
                Synced: <b>{activeSyncResult.sync.synced}</b>
              </span>
              <span className="px-2.5 py-1 rounded bg-rose-500/20 border border-rose-500/30">
                Failed: <b>{activeSyncResult.sync.failed}</b>
              </span>
              <span className="px-2.5 py-1 rounded bg-amber-500/20 border border-amber-500/30">
                Remaining: <b>{activeSyncResult.sync.remaining_pending}</b>
              </span>
            </div>
          </div>
        )}

        {/* Last Created Option Preview */}
        {lastCreatedOption && (
          <div className="mt-5 p-4 rounded-xl border border-zinc-700/60 bg-zinc-950/60 text-xs font-mono">
            <div className="flex items-center justify-between text-zinc-400 pb-2 border-b border-zinc-800">
              <span className="font-semibold text-zinc-200">
                Latest Operation Response (from Backend)
              </span>
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  isOfflineMode
                    ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                    : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                }`}
              >
                {isOfflineMode ? "CAPTURED IN SQLITE" : "LIVE ENGINE"}
              </span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
              <div>
                <span className="text-zinc-500 block">Option ID:</span>
                <span className="text-zinc-300 font-bold truncate block">
                  {lastCreatedOption.id}
                </span>
              </div>
              <div>
                <span className="text-zinc-500 block">Agent ID:</span>
                <span className="text-cyan-300 font-semibold">
                  {lastCreatedOption.agent_id}
                </span>
              </div>
              <div>
                <span className="text-zinc-500 block">Capability:</span>
                <span className="text-zinc-200">
                  {lastCreatedOption.capability}
                </span>
              </div>
              <div>
                <span className="text-zinc-500 block">
                  Status & Probability:
                </span>
                <span className="text-emerald-400 font-semibold">
                  {lastCreatedOption.status} (p={lastCreatedOption.probability})
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Visual Architectural Flow ("How It Works") */}
      <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/40 p-6 shadow-lg">
        <h3 className="text-sm font-semibold text-zinc-200 mb-4 font-mono uppercase tracking-wider flex items-center gap-2">
          <Zap className="h-4 w-4 text-cyan-400" />
          <span>Resilience Architecture — How It Works</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-7 gap-2 items-center text-center text-xs font-mono">
          <div className="p-3 rounded-xl border border-zinc-800 bg-zinc-950/60 flex flex-col items-center justify-center">
            <span className="font-bold text-zinc-200">Agent Request</span>
            <span className="text-[10px] text-zinc-500 mt-1">
              Conditional option
            </span>
          </div>

          <div className="flex justify-center text-zinc-500">
            <span className="hidden md:inline">→</span>
            <ArrowDown className="md:hidden h-4 w-4" />
          </div>

          <div
            className={`p-3 rounded-xl border transition-all flex flex-col items-center justify-center ${
              isOfflineMode
                ? "border-rose-500/50 bg-rose-950/30 text-rose-200 shadow-md shadow-rose-950/30"
                : "border-zinc-800 bg-zinc-950/60 text-zinc-400"
            }`}
          >
            <span className="font-bold">Connectivity Lost</span>
            <span className="text-[10px] text-zinc-500 mt-1">
              Network outage
            </span>
          </div>

          <div className="flex justify-center text-zinc-500">
            <span className="hidden md:inline">→</span>
            <ArrowDown className="md:hidden h-4 w-4" />
          </div>

          <div
            className={`p-3 rounded-xl border transition-all flex flex-col items-center justify-center ${
              isOfflineMode
                ? "border-amber-500/60 bg-amber-950/30 text-amber-200 shadow-md shadow-amber-950/30 animate-pulse"
                : "border-zinc-800 bg-zinc-950/60 text-zinc-400"
            }`}
          >
            <span className="font-bold">Local Processing</span>
            <span className="text-[10px] text-amber-400/80 mt-1">
              SQLite Durable Queue
            </span>
          </div>

          <div className="flex justify-center text-zinc-500">
            <span className="hidden md:inline">→</span>
            <ArrowDown className="md:hidden h-4 w-4" />
          </div>

          <div
            className={`p-3 rounded-xl border transition-all flex flex-col items-center justify-center ${
              !isOfflineMode && stats.synced > 0
                ? "border-emerald-500/50 bg-emerald-950/30 text-emerald-200 shadow-md shadow-emerald-950/30"
                : "border-zinc-800 bg-zinc-950/60 text-zinc-400"
            }`}
          >
            <span className="font-bold">Auto-Reconcile</span>
            <span className="text-[10px] text-emerald-400/80 mt-1">
              Live RESERVE-X Core
            </span>
          </div>
        </div>
      </div>

      {/* SQLite Durable Queue Live Inspector */}
      <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/40 p-6 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-zinc-200 font-mono uppercase tracking-wider">
              Durable SQLite Queue
            </h3>
            <span className="text-xs text-zinc-500 font-mono">
              (data/offline_resilience.db)
            </span>
          </div>
          <span className="text-xs text-zinc-400 font-mono">
            Showing {queue.length} records
          </span>
        </div>

        {queue.length === 0 ? (
          <div className="text-center py-10 border border-dashed border-zinc-800 rounded-xl text-zinc-500 text-xs font-mono">
            No offline operations recorded yet. Click "Simulate Disconnect" and
            then "Create Offline Option" to test.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="border-b border-zinc-800 text-zinc-400 bg-zinc-950/40">
                <tr>
                  <th className="py-2.5 px-3">Operation ID</th>
                  <th className="py-2.5 px-3">Agent</th>
                  <th className="py-2.5 px-3">Capability</th>
                  <th className="py-2.5 px-3">Prob / Amt</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Retries</th>
                  <th className="py-2.5 px-3">Timestamp / Reconciled ID</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/50">
                {queue.map((op) => {
                  const isPending = op.sync_status === "PENDING";
                  const isSynced = op.sync_status === "SYNCED";

                  return (
                    <tr
                      key={op.operation_id}
                      className="hover:bg-zinc-800/30 transition-colors"
                    >
                      <td className="py-2.5 px-3 font-semibold text-zinc-300">
                        {op.operation_id.slice(0, 8)}...
                      </td>
                      <td className="py-2.5 px-3 text-cyan-300">
                        {op.agent_id}
                      </td>
                      <td className="py-2.5 px-3 text-zinc-300">
                        {op.capability}
                      </td>
                      <td className="py-2.5 px-3 text-zinc-400">
                        p={op.probability} (×{op.amount})
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                            isPending
                              ? "bg-amber-500/20 text-amber-300 border-amber-500/40 animate-pulse"
                              : isSynced
                              ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                              : "bg-rose-500/20 text-rose-300 border-rose-500/40"
                          }`}
                        >
                          {op.sync_status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-zinc-400">
                        {op.retry_count}
                      </td>
                      <td className="py-2.5 px-3 text-zinc-400">
                        {isSynced && op.reconciled_option_id ? (
                          <span className="text-emerald-400">
                            Reconciled → {op.reconciled_option_id.slice(0, 8)}
                            ...
                          </span>
                        ) : (
                          <span>
                            {new Date(op.timestamp).toLocaleTimeString()}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Audit Event Feed */}
      <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/40 p-6 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Server className="h-4 w-4 text-violet-400" />
            <h3 className="text-sm font-semibold text-zinc-200 font-mono uppercase tracking-wider">
              Offline Audit Log
            </h3>
          </div>
          <span className="text-xs text-zinc-500 font-mono">
            {offlineEvents.length} events
          </span>
        </div>

        {offlineEvents.length === 0 ? (
          <div className="text-zinc-500 text-xs font-mono text-center py-6">
            No offline events recorded.
          </div>
        ) : (
          <div className="space-y-2 max-h-56 overflow-y-auto pr-2 font-mono text-xs">
            {offlineEvents.slice(0, 15).map((evt) => (
              <div
                key={evt.event_id}
                className="flex items-center justify-between p-2.5 rounded-lg bg-zinc-950/50 border border-zinc-800/60"
              >
                <div className="flex items-center gap-3">
                  <span className="px-2 py-0.5 rounded bg-zinc-800 text-[10px] font-bold text-zinc-300">
                    {evt.event_type}
                  </span>
                  <span className="text-zinc-400 text-[11px] truncate max-w-xs md:max-w-md">
                    {evt.operation_id
                      ? `Op ${evt.operation_id.slice(0, 8)}...`
                      : JSON.stringify(evt.details)}
                  </span>
                </div>
                <span className="text-[10px] text-zinc-500 shrink-0">
                  {new Date(evt.timestamp).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
