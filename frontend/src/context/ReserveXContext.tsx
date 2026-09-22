import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { api, ApiError } from "../services/api";
import type {
  Allocation,
  CreateOptionRequest,
  CreateResourceRequest,
  EventLog,
  Resource,
  ResourceOption,
  SystemRiskSummary,
  SystemStatus,
  UpdateOptionRequest,
  ConnectivityStatus,
  ReconnectResponse,
} from "../types/reservex";

export interface ToastMessage {
  id: string;
  type: "success" | "warning" | "error" | "info";
  title: string;
  message: string;
  timestamp: Date;
}

interface ReserveXContextValue {
  status: SystemStatus | null;
  resources: Resource[];
  options: ResourceOption[];
  allocations: Allocation[];
  risk: SystemRiskSummary | null;
  events: EventLog[];
  loading: boolean;
  isInitialLoading: boolean;
  error: string | null;
  isOnline: boolean;
  connectivity: ConnectivityStatus | null;
  lastSyncResult: ReconnectResponse | null;
  lastUpdated: Date | null;
  isPolling: boolean;
  togglePolling: () => void;
  refresh: () => Promise<void>;
  simulateDisconnect: (reason?: string) => Promise<boolean>;
  reconnectAndSync: () => Promise<ReconnectResponse | null>;
  toasts: ToastMessage[];
  addToast: (toast: Omit<ToastMessage, "id" | "timestamp">) => void;
  removeToast: (id: string) => void;

  // Actions
  exerciseOption: (optionId: string) => Promise<boolean>;
  cancelOption: (optionId: string) => Promise<boolean>;
  updateOption: (optionId: string, data: UpdateOptionRequest) => Promise<boolean>;
  releaseAllocation: (allocationId: string) => Promise<boolean>;
  createResource: (data: CreateResourceRequest) => Promise<boolean>;
  createOption: (data: CreateOptionRequest) => Promise<boolean>;
}

const ReserveXContext = createContext<ReserveXContextValue | null>(null);

export const ReserveXProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [events, setEvents] = useState<EventLog[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [isInitialLoading, setIsInitialLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState<boolean>(false);
  const [connectivity, setConnectivity] = useState<ConnectivityStatus | null>(() => {
    if (typeof navigator !== "undefined" && !navigator.onLine) {
      return {
        mode: "OFFLINE",
        is_offline: true,
        offline_reason: "NETWORK_DISCONNECTED",
        outage_started_at: new Date().toISOString(),
        queue_stats: { total: 0, pending: 0, failed: 0, synced: 0 },
        db_path: "data/offline_resilience.db",
      };
    }
    return null;
  });
  const [lastSyncResult, setLastSyncResult] = useState<ReconnectResponse | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isPolling, setIsPolling] = useState<boolean>(true);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const isFetchingRef = useRef(false);

  const addToast = useCallback(
    (toast: Omit<ToastMessage, "id" | "timestamp">) => {
      const id = Math.random().toString(36).substring(2, 9);
      const newToast: ToastMessage = {
        ...toast,
        id,
        timestamp: new Date(),
      };
      setToasts((prev) => [...prev.slice(-4), newToast]);

      // Auto dismiss after 6 seconds
      setTimeout(() => {
        removeToast(id);
      }, 6000);
    },
    []
  );

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const refresh = useCallback(async () => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;
    setLoading(true);

    try {
      const [statusRes, eventsRes, connRes] = await Promise.all([
        api.getStatus(),
        api.getEvents({ limit: 50 }),
        api.getConnectivityStatus().catch(() => null),
      ]);

      setStatus(statusRes);
      setEvents(eventsRes);
      if (connRes) {
        setConnectivity(connRes);
      }
      setIsOnline(true);
      setError(null);
      setLastUpdated(new Date());
    } catch (err: any) {
      setIsOnline(false);
      setError(
        err?.message ||
          "Unable to connect to RESERVE-X backend at http://127.0.0.1:8000."
      );
    } finally {
      setLoading(false);
      setIsInitialLoading(false);
      isFetchingRef.current = false;
    }
  }, []);

  // Polling loop (approx every 2 seconds)
  useEffect(() => {
    // Initial fetch
    refresh();

    if (!isPolling) return;

    const interval = setInterval(() => {
      // Don't poll if document is hidden to conserve resources
      if (document.hidden) return;
      refresh();
    }, 2000);

    return () => clearInterval(interval);
  }, [refresh, isPolling]);

  const togglePolling = useCallback(() => {
    setIsPolling((prev) => !prev);
  }, []);

  // Action: Exercise Option
  const exerciseOption = useCallback(
    async (optionId: string): Promise<boolean> => {
      try {
        await api.exerciseOption(optionId);
        addToast({
          type: "success",
          title: "Option Exercised",
          message: "Real resource allocation created successfully.",
        });
        await refresh();
        return true;
      } catch (err: any) {
        if (err instanceof ApiError && err.isConflict) {
          addToast({
            type: "warning",
            title: "Capacity Conflict (HTTP 409)",
            message:
              err.message ||
              "Insufficient capacity available. Option remains PENDING.",
          });
        } else {
          addToast({
            type: "error",
            title: "Exercise Failed",
            message: err?.message || "Failed to exercise option.",
          });
        }
        await refresh();
        return false;
      }
    },
    [addToast, refresh]
  );

  // Action: Cancel Option
  const cancelOption = useCallback(
    async (optionId: string): Promise<boolean> => {
      try {
        await api.cancelOption(optionId);
        addToast({
          type: "info",
          title: "Option Cancelled",
          message: "Option cancelled. No resource capacity was consumed.",
        });
        await refresh();
        return true;
      } catch (err: any) {
        addToast({
          type: "error",
          title: "Cancel Failed",
          message: err?.message || "Failed to cancel option.",
        });
        await refresh();
        return false;
      }
    },
    [addToast, refresh]
  );

  // Action: Update Option
  const updateOption = useCallback(
    async (
      optionId: string,
      data: UpdateOptionRequest
    ): Promise<boolean> => {
      try {
        await api.updateOption(optionId, data);
        addToast({
          type: "success",
          title: "Option Updated",
          message: "Option parameters updated. System risk recalculated.",
        });
        await refresh();
        return true;
      } catch (err: any) {
        addToast({
          type: "error",
          title: "Update Failed",
          message: err?.message || "Failed to update option.",
        });
        await refresh();
        return false;
      }
    },
    [addToast, refresh]
  );

  // Action: Release Allocation
  const releaseAllocation = useCallback(
    async (allocationId: string): Promise<boolean> => {
      try {
        await api.releaseAllocation(allocationId);
        addToast({
          type: "success",
          title: "Allocation Released",
          message: "Capacity released back to the scarce resource pool.",
        });
        await refresh();
        return true;
      } catch (err: any) {
        addToast({
          type: "error",
          title: "Release Failed",
          message: err?.message || "Failed to release allocation.",
        });
        await refresh();
        return false;
      }
    },
    [addToast, refresh]
  );

  // Action: Create Resource
  const createResource = useCallback(
    async (data: CreateResourceRequest): Promise<boolean> => {
      try {
        await api.createResource(data);
        addToast({
          type: "success",
          title: "Resource Registered",
          message: `Resource "${data.name}" added to system pool.`,
        });
        await refresh();
        return true;
      } catch (err: any) {
        addToast({
          type: "error",
          title: "Registration Failed",
          message: err?.message || "Failed to create resource.",
        });
        return false;
      }
    },
    [addToast, refresh]
  );

  // Action: Create Option
  const createOption = useCallback(
    async (data: CreateOptionRequest): Promise<boolean> => {
      try {
        await api.createOption(data);
        addToast({
          type: "success",
          title: "Option Created",
          message: `Conditional option created for ${data.capability} at ${Math.round(
            data.probability * 100
          )}%.`,
        });
        await refresh();
        return true;
      } catch (err: any) {
        addToast({
          type: "error",
          title: "Option Creation Failed",
          message: err?.message || "Failed to create option.",
        });
        return false;
      }
    },
    [addToast, refresh]
  );

  // Action: Simulate Disconnect
  const simulateDisconnect = useCallback(
    async (reason: string = "MANUAL"): Promise<boolean> => {
      try {
        setLastSyncResult(null);
        const conn = await api.simulateDisconnect(reason);
        setConnectivity(conn);
        addToast({
          type: "warning",
          title:
            reason === "NETWORK_DISCONNECTED"
              ? "Network Disconnected (Hardware / Wi-Fi)"
              : "Connectivity Lost (Simulated)",
          message:
            reason === "NETWORK_DISCONNECTED"
              ? "Real network connection lost. System switched to OFFLINE mode with SQLite queue."
              : "System is now in OFFLINE mode. Local processing and SQLite queue active.",
        });
        await refresh();
        return true;
      } catch (err: any) {
        addToast({
          type: "error",
          title: "Failed to Switch Offline",
          message: err?.message || "Error switching to offline mode.",
        });
        return false;
      }
    },
    [addToast, refresh]
  );

  // Action: Reconnect & Sync
  const reconnectAndSync = useCallback(async (): Promise<ReconnectResponse | null> => {
    try {
      const res = await api.reconnectAndSync();
      setLastSyncResult(res);
      addToast({
        type: "success",
        title: "Connectivity Restored (ONLINE)",
        message: `Synchronized ${res.sync.synced} operations (${res.sync.remaining_pending} remaining).`,
      });
      await refresh();
      return res;
    } catch (err: any) {
      addToast({
        type: "error",
        title: "Reconnection Failed",
        message: err?.message || "Error restoring online connectivity.",
      });
      return null;
    }
  }, [addToast, refresh]);

  // Real laptop network connectivity listeners (Wi-Fi / Ethernet state)
  const refreshRef = useRef(refresh);
  refreshRef.current = refresh;
  const reconnectAndSyncRef = useRef(reconnectAndSync);
  reconnectAndSyncRef.current = reconnectAndSync;
  const addToastRef = useRef(addToast);
  addToastRef.current = addToast;

  useEffect(() => {
    const handleNetworkOffline = async () => {
      // 1. Immediately update UI to 🔴 OFFLINE MODE (Network disconnected) & start/continue outage timer
      setConnectivity((prev) => ({
        mode: "OFFLINE",
        is_offline: true,
        offline_reason: "NETWORK_DISCONNECTED",
        outage_started_at: prev?.outage_started_at || new Date().toISOString(),
        queue_stats: prev?.queue_stats || { total: 0, pending: 0, failed: 0, synced: 0 },
        db_path: prev?.db_path || "data/offline_resilience.db",
      }));

      addToastRef.current({
        type: "warning",
        title: "Network Disconnected (Hardware / Wi-Fi)",
        message:
          "Laptop lost network connectivity. Automatically switched to OFFLINE mode with local SQLite queue.",
      });

      // 3. Call the LOCAL backend: POST /api/v1/connectivity/offline?reason=NETWORK_DISCONNECTED
      try {
        const conn = await api.simulateDisconnect("NETWORK_DISCONNECTED");
        // 4. Refresh backend connectivity state
        setConnectivity(conn);
        await refreshRef.current();
      } catch (err: any) {
        console.error("Failed to transition backend to offline on network disconnect:", err);
      }
    };

    const handleNetworkOnline = async () => {
      // 1. Immediately update UI to 🟢 ONLINE (Network connected)
      setConnectivity((prev) =>
        prev
          ? {
              ...prev,
              mode: "ONLINE",
              is_offline: false,
              offline_reason: null,
            }
          : null
      );

      // 2 & 3. Call POST /api/v1/connectivity/online to trigger existing OfflineManager auto-sync
      try {
        const res = await reconnectAndSyncRef.current();
        if (res) {
          setLastSyncResult(res);
        }
      } catch (err: any) {
        console.error("Failed to reconnect and sync on network restore:", err);
        await refreshRef.current();
      }
    };

    // Initial check if browser is already offline on load
    if (typeof navigator !== "undefined" && !navigator.onLine) {
      handleNetworkOffline();
    }

    // Register ONE offline event listener and ONE online event listener
    window.addEventListener("offline", handleNetworkOffline);
    window.addEventListener("online", handleNetworkOnline);

    return () => {
      // Clean up listeners correctly
      window.removeEventListener("offline", handleNetworkOffline);
      window.removeEventListener("online", handleNetworkOnline);
    };
  }, []);

  const value: ReserveXContextValue = {
    status,
    resources: status?.resources || [],
    options: status?.options || [],
    allocations: status?.allocations || [],
    risk: status?.risk || null,
    events,
    loading,
    isInitialLoading,
    error,
    isOnline,
    connectivity,
    lastSyncResult,
    lastUpdated,
    isPolling,
    togglePolling,
    refresh,
    simulateDisconnect,
    reconnectAndSync,
    toasts,
    addToast,
    removeToast,
    exerciseOption,
    cancelOption,
    updateOption,
    releaseAllocation,
    createResource,
    createOption,
  };

  return (
    <ReserveXContext.Provider value={value}>
      {children}
    </ReserveXContext.Provider>
  );
};

export const useReserveX = (): ReserveXContextValue => {
  const context = useContext(ReserveXContext);
  if (!context) {
    throw new Error("useReserveX must be used within a ReserveXProvider");
  }
  return context;
};
