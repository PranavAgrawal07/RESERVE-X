import React, { useState } from "react";
import { Modal } from "../common/Modal";
import { KNOWN_AGENTS } from "../../data/agents";
import { useReserveX } from "../../context/ReserveXContext";

interface CreateOptionModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const CAPABILITIES = [
  "GPU_COMPUTE",
  "CODE_EXECUTION",
  "WEB_SEARCH",
  "LLM_INFERENCE",
];

export const CreateOptionModal: React.FC<CreateOptionModalProps> = ({
  isOpen,
  onClose,
}) => {
  const { createOption } = useReserveX();
  const [agentId, setAgentId] = useState("agent-001");
  const [capability, setCapability] = useState("GPU_COMPUTE");
  const [probability, setProbability] = useState(0.8);
  const [amount, setAmount] = useState(1);
  const [priority, setPriority] = useState(1);
  const [expiresInMinutes, setExpiresInMinutes] = useState(5);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    const expiresAt = new Date(
      Date.now() + expiresInMinutes * 60 * 1000
    ).toISOString();

    const success = await createOption({
      agent_id: agentId,
      capability,
      probability: Number(probability),
      amount: Number(amount),
      priority: Number(priority),
      expires_at: expiresAt,
    });

    setIsSubmitting(false);
    if (success) {
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create Contingent Option"
      subtitle="Simulate an agent pre-registering a future conditional resource need"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-mono uppercase text-zinc-400 mb-1">
            Requesting Agent
          </label>
          <select
            value={agentId}
            onChange={(e) => setAgentId(e.target.value)}
            className="w-full rounded-lg border border-zinc-700/80 bg-zinc-950 px-3.5 py-2 text-sm text-zinc-100 focus:border-cyan-500 focus:outline-none font-mono"
          >
            {Object.values(KNOWN_AGENTS).map((ag) => (
              <option key={ag.id} value={ag.id}>
                {ag.id} — {ag.name} ({ag.role})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-mono uppercase text-zinc-400 mb-1">
            Required Capability
          </label>
          <select
            value={capability}
            onChange={(e) => setCapability(e.target.value)}
            className="w-full rounded-lg border border-zinc-700/80 bg-zinc-950 px-3.5 py-2 text-sm text-zinc-100 focus:border-cyan-500 focus:outline-none font-mono"
          >
            {CAPABILITIES.map((cap) => (
              <option key={cap} value={cap}>
                {cap}
              </option>
            ))}
          </select>
        </div>

        <div>
          <div className="flex justify-between text-xs font-mono uppercase text-zinc-400 mb-1">
            <span>Prediction Probability</span>
            <span className="text-cyan-300 font-bold">
              {Math.round(probability * 100)}%
            </span>
          </div>
          <input
            type="range"
            min={0.1}
            max={1.0}
            step={0.05}
            value={probability}
            onChange={(e) => setProbability(parseFloat(e.target.value))}
            className="w-full accent-cyan-400 bg-zinc-800 rounded-lg cursor-pointer"
          />
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-mono uppercase text-zinc-400 mb-1">
              Amount (Units)
            </label>
            <input
              type="number"
              min={1}
              max={10}
              value={amount}
              onChange={(e) => setAmount(Math.max(1, parseInt(e.target.value) || 1))}
              className="w-full rounded-lg border border-zinc-700/80 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 focus:border-cyan-500 focus:outline-none font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-zinc-400 mb-1">
              Priority
            </label>
            <input
              type="number"
              min={0}
              max={10}
              value={priority}
              onChange={(e) => setPriority(Math.max(0, parseInt(e.target.value) || 0))}
              className="w-full rounded-lg border border-zinc-700/80 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 focus:border-cyan-500 focus:outline-none font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-zinc-400 mb-1">
              Expires In
            </label>
            <input
              type="number"
              min={1}
              max={60}
              value={expiresInMinutes}
              onChange={(e) => setExpiresInMinutes(Math.max(1, parseInt(e.target.value) || 1))}
              className="w-full rounded-lg border border-zinc-700/80 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 focus:border-cyan-500 focus:outline-none font-mono"
            />
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-zinc-800">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-zinc-800 px-4 py-2 text-xs font-mono text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-lg border border-cyan-500/40 bg-cyan-500/20 px-4 py-2 text-xs font-mono font-semibold text-cyan-200 hover:bg-cyan-500/30 transition-all disabled:opacity-50"
          >
            {isSubmitting ? "Creating..." : "Create Option"}
          </button>
        </div>
      </form>
    </Modal>
  );
};
