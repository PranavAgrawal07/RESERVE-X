import React, { useState } from "react";
import {
  Play,
  Pause,
  RotateCcw,
  Zap,
  Activity,
  Gauge,
  Sparkles,
} from "lucide-react";
import { useReserveX } from "../../context/ReserveXContext";

export const LiveSimulationControls: React.FC = () => {
  const {
    liveSimulation,
    startLiveSimulation,
    pauseLiveSimulation,
    resetLiveSimulation,
  } = useReserveX();

  const [selectedSpeed, setSelectedSpeed] = useState<number>(
    liveSimulation?.speed || 1.0
  );
  const [actionLoading, setActionLoading] = useState<boolean>(false);

  const isRunning = liveSimulation?.running && !liveSimulation?.paused;
  const isPaused = liveSimulation?.running && liveSimulation?.paused;
  const currentTick = liveSimulation?.tick || 0;

  const handleStart = async (speed: number) => {
    setActionLoading(true);
    setSelectedSpeed(speed);
    await startLiveSimulation(speed);
    setActionLoading(false);
  };

  const handlePause = async () => {
    setActionLoading(true);
    await pauseLiveSimulation();
    setActionLoading(false);
  };

  const handleReset = async () => {
    setActionLoading(true);
    await resetLiveSimulation();
    setActionLoading(false);
  };

  return (
    <div className="rounded-2xl border border-cyan-500/30 bg-gradient-to-r from-zinc-950/90 via-zinc-900/80 to-cyan-950/20 p-5 shadow-xl shadow-cyan-950/20 backdrop-blur-xl">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Left: Info & Live Badge */}
        <div className="flex items-start sm:items-center gap-3.5">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-cyan-500/40 bg-cyan-500/10 text-cyan-400 shadow-md shadow-cyan-950/30">
            <Zap className={`h-6 w-6 ${isRunning ? "animate-pulse fill-cyan-400/30" : ""}`} />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h3 className="font-mono text-base font-bold tracking-wide text-zinc-100">
                Autonomous Live Multi-Agent Simulation
              </h3>
              <span
                className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold border ${
                  isRunning
                    ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300 shadow-sm shadow-emerald-950/30"
                    : isPaused
                    ? "border-amber-500/40 bg-amber-500/10 text-amber-300"
                    : "border-zinc-700 bg-zinc-800/40 text-zinc-400"
                }`}
              >
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    isRunning
                      ? "bg-emerald-400 animate-ping"
                      : isPaused
                      ? "bg-amber-400"
                      : "bg-zinc-500"
                  }`}
                />
                <span>{isRunning ? "AUTONOMOUS ACTIVE" : isPaused ? "PAUSED" : "STANDBY"}</span>
              </span>
            </div>
            <p className="text-xs text-zinc-400 mt-1 flex items-center gap-2">
              <span>Learned capability predictions → Conditional options → Contention exercise → Duration release</span>
              <span className="hidden md:inline-flex items-center gap-1 font-mono text-cyan-300/80">
                <Sparkles className="h-3 w-3" /> ML Heuristics Active
              </span>
            </p>
          </div>
        </div>

        {/* Right: Controls & Speed Selector */}
        <div className="flex flex-wrap items-center gap-3 self-end lg:self-auto">
          {/* Tick Counter */}
          <div className="flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-950/80 px-3 py-1.5 font-mono text-xs text-zinc-300">
            <Activity className="h-3.5 w-3.5 text-cyan-400" />
            <span className="text-zinc-500">Tick:</span>
            <span className="font-bold text-cyan-300">{currentTick}</span>
          </div>

          {/* Speed Selector */}
          <div className="flex items-center rounded-xl border border-zinc-800 bg-zinc-950/80 p-1 text-xs font-mono">
            <Gauge className="h-3.5 w-3.5 text-zinc-500 ml-1.5 mr-1" />
            {[1, 2, 5].map((speed) => (
              <button
                key={speed}
                onClick={() => handleStart(speed)}
                disabled={actionLoading}
                className={`px-2.5 py-1 rounded-lg transition-all font-semibold ${
                  selectedSpeed === speed
                    ? "bg-cyan-500/20 text-cyan-200 border border-cyan-500/40 shadow-sm"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {speed}x
              </button>
            ))}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            {!isRunning ? (
              <button
                onClick={() => handleStart(selectedSpeed)}
                disabled={actionLoading}
                className="flex items-center gap-2 rounded-xl border border-emerald-500/40 bg-emerald-500/15 px-4 py-2 text-xs font-mono font-bold text-emerald-200 hover:bg-emerald-500/25 shadow-lg shadow-emerald-950/20 transition-all disabled:opacity-50"
              >
                <Play className="h-3.5 w-3.5 fill-emerald-300" />
                <span>{isPaused ? "Resume" : "Start Live Sim"}</span>
              </button>
            ) : (
              <button
                onClick={handlePause}
                disabled={actionLoading}
                className="flex items-center gap-2 rounded-xl border border-amber-500/40 bg-amber-500/15 px-4 py-2 text-xs font-mono font-bold text-amber-200 hover:bg-amber-500/25 shadow-lg shadow-amber-950/20 transition-all disabled:opacity-50"
              >
                <Pause className="h-3.5 w-3.5 fill-amber-300" />
                <span>Pause</span>
              </button>
            )}

            <button
              onClick={handleReset}
              disabled={actionLoading}
              title="Reset simulation workflows"
              className="flex h-8 w-8 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900/80 text-zinc-400 hover:border-zinc-700 hover:bg-zinc-800 hover:text-white transition-all disabled:opacity-50"
            >
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
