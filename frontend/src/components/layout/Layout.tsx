import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { ToastContainer } from "../common/Toast";
import { ConnectivityBanner } from "../connectivity/ConnectivityBanner";
import { useReserveX } from "../../context/ReserveXContext";

interface LayoutProps {
  children: React.ReactNode;
  currentTab: string;
  onTabChange: (tab: string) => void;
}

export const Layout: React.FC<LayoutProps> = ({
  children,
  currentTab,
  onTabChange,
}) => {
  const { isOnline, refresh, loading, error } = useReserveX();

  return (
    <div className="min-h-screen bg-[#090d16] text-zinc-100 flex flex-col antialiased selection:bg-cyan-500/20 selection:text-cyan-200">
      <Header />
      <ConnectivityBanner onNavigateToOfflinePage={() => onTabChange("offline")} />

      {/* Offline Alert Banner (shown prominently if disconnected) */}
      {!isOnline && (
        <div className="bg-rose-950/70 border-b border-rose-500/30 px-6 py-3 text-rose-200 flex flex-wrap items-center justify-between gap-3 shadow-lg shadow-rose-950/20">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-rose-400 shrink-0 animate-bounce" />
            <div>
              <p className="text-sm font-semibold text-rose-100">
                Backend Offline — Connection Lost
              </p>
              <p className="text-xs text-rose-300">
                {error ||
                  "Unable to connect to RESERVE-X backend service at http://127.0.0.1:8000."}
              </p>
            </div>
          </div>
          <button
            onClick={() => refresh()}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg border border-rose-400/40 bg-rose-500/20 px-3 py-1.5 text-xs font-mono font-semibold text-rose-100 hover:bg-rose-500/30 transition-colors disabled:opacity-50"
          >
            <RefreshCw
              className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`}
            />
            <span>{loading ? "Reconnecting..." : "Retry Connection"}</span>
          </button>
        </div>
      )}

      {/* Main Workspace with Sidebar & Dynamic Page View */}
      <div className="flex flex-1 overflow-hidden">
        <Sidebar currentTab={currentTab} onTabChange={onTabChange} />
        <main className="flex-1 overflow-y-auto p-6 lg:p-8 max-w-[1600px] mx-auto w-full">
          {children}
        </main>
      </div>

      <ToastContainer />
    </div>
  );
};
