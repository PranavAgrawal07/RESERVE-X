import React, { useState } from "react";
import { Modal } from "../common/Modal";
import { useReserveX } from "../../context/ReserveXContext";

interface AddResourceModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const CAPABILITIES = [
  "GPU_COMPUTE",
  "CODE_EXECUTION",
  "WEB_SEARCH",
  "LLM_INFERENCE",
];

export const AddResourceModal: React.FC<AddResourceModalProps> = ({
  isOpen,
  onClose,
}) => {
  const { createResource } = useReserveX();
  const [name, setName] = useState("");
  const [capability, setCapability] = useState("GPU_COMPUTE");
  const [totalCapacity, setTotalCapacity] = useState(4);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setIsSubmitting(true);
    const success = await createResource({
      name: name.trim(),
      capability,
      total_capacity: Number(totalCapacity),
    });
    setIsSubmitting(false);

    if (success) {
      setName("");
      setTotalCapacity(4);
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Register Scarce Resource"
      subtitle="Define a new compute, API, or service cluster in RESERVE-X"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-mono uppercase text-zinc-400 mb-1">
            Resource Name
          </label>
          <input
            type="text"
            required
            placeholder="e.g. NVIDIA H100 Cluster Beta"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-lg border border-zinc-700/80 bg-zinc-950 px-3.5 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:border-cyan-500 focus:outline-none font-sans"
          />
        </div>

        <div>
          <label className="block text-xs font-mono uppercase text-zinc-400 mb-1">
            Target Capability
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
          <p className="text-[11px] text-zinc-500 mt-1">
            Agents submit conditional options referencing abstract capabilities.
          </p>
        </div>

        <div>
          <label className="block text-xs font-mono uppercase text-zinc-400 mb-1">
            Total Capacity (Units)
          </label>
          <input
            type="number"
            required
            min={1}
            max={1000}
            value={totalCapacity}
            onChange={(e) => setTotalCapacity(Math.max(1, parseInt(e.target.value) || 1))}
            className="w-full rounded-lg border border-zinc-700/80 bg-zinc-950 px-3.5 py-2 text-sm text-zinc-100 focus:border-cyan-500 focus:outline-none font-mono"
          />
          <p className="text-[11px] text-zinc-500 mt-1">
            Maximum concurrency or allocation units supported by this pool.
          </p>
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
            {isSubmitting ? "Registering..." : "Register Resource"}
          </button>
        </div>
      </form>
    </Modal>
  );
};
