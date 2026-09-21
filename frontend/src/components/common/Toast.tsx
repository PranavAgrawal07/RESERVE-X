import React from "react";
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from "lucide-react";
import { useReserveX } from "../../context/ReserveXContext";

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useReserveX();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-md w-full pointer-events-none">
      {toasts.map((toast) => {
        let icon = <Info className="h-5 w-5 text-sky-400 shrink-0" />;
        let borderClass = "border-sky-500/30 bg-zinc-900/90";

        if (toast.type === "success") {
          icon = <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />;
          borderClass = "border-emerald-500/30 bg-zinc-900/95";
        } else if (toast.type === "warning") {
          icon = <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0" />;
          borderClass = "border-amber-500/40 bg-zinc-900/95 shadow-lg shadow-amber-950/20";
        } else if (toast.type === "error") {
          icon = <XCircle className="h-5 w-5 text-rose-400 shrink-0" />;
          borderClass = "border-rose-500/40 bg-zinc-900/95 shadow-lg shadow-rose-950/20";
        }

        return (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-start gap-3 rounded-xl border p-4 shadow-xl backdrop-blur-md transition-all duration-300 animate-in fade-in slide-in-from-bottom-3 ${borderClass}`}
          >
            {icon}
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-semibold tracking-wide text-zinc-100">
                {toast.title}
              </h4>
              <p className="mt-0.5 text-xs text-zinc-300 break-words leading-relaxed">
                {toast.message}
              </p>
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="text-zinc-400 hover:text-zinc-200 transition-colors p-1"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
};
