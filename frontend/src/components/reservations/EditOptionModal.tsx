import React, { useState, useEffect } from "react";
import { Modal } from "../common/Modal";
import type { ResourceOption } from "../../types/reservex";
import { useReserveX } from "../../context/ReserveXContext";

interface EditOptionModalProps {
  option: ResourceOption | null;
  isOpen: boolean;
  onClose: () => void;
}

export const EditOptionModal: React.FC<EditOptionModalProps> = ({
  option,
  isOpen,
  onClose,
}) => {
  const { updateOption } = useReserveX();
  const [probability, setProbability] = useState<number>(0.75);
  const [expiresInMinutes, setExpiresInMinutes] = useState<number>(10);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (option) {
      setProbability(option.probability);
      // default 10 minutes from now if extending
      setExpiresInMinutes(10);
    }
  }, [option]);

  if (!option) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    const newExpiresAt = new Date(
      Date.now() + expiresInMinutes * 60 * 1000
    ).toISOString();

    const success = await updateOption(option.id, {
      probability: Number(probability),
      expires_at: newExpiresAt,
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
      title="Edit Conditional Option"
      subtitle={`Modify predicted parameters for Option ${option.id.substring(0, 8)}`}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800 text-xs font-mono">
          <div className="flex justify-between text-zinc-400">
            <span>Agent:</span>
            <span className="text-zinc-200">{option.agent_id}</span>
          </div>
          <div className="flex justify-between text-zinc-400 mt-1">
            <span>Capability:</span>
            <span className="text-cyan-400">{option.capability}</span>
          </div>
          <div className="flex justify-between text-zinc-400 mt-1">
            <span>Units:</span>
            <span className="text-zinc-200">{option.amount}</span>
          </div>
        </div>

        <div>
          <div className="flex justify-between text-xs font-mono uppercase text-zinc-400 mb-1">
            <span>Predicted Probability</span>
            <span className="text-cyan-300 font-bold">
              {Math.round(probability * 100)}%
            </span>
          </div>
          <input
            type="range"
            min={0.05}
            max={1.0}
            step={0.05}
            value={probability}
            onChange={(e) => setProbability(parseFloat(e.target.value))}
            className="w-full accent-cyan-400 bg-zinc-800 rounded-lg cursor-pointer"
          />
          <p className="text-[11px] text-zinc-500 mt-1">
            Alters the agent's confidence. The backend risk engine will re-evaluate overcommit probability immediately.
          </p>
        </div>

        <div>
          <label className="block text-xs font-mono uppercase text-zinc-400 mb-1">
            Extend Expiration (Minutes from now)
          </label>
          <input
            type="number"
            min={1}
            max={120}
            value={expiresInMinutes}
            onChange={(e) => setExpiresInMinutes(Math.max(1, parseInt(e.target.value) || 1))}
            className="w-full rounded-lg border border-zinc-700/80 bg-zinc-950 px-3.5 py-2 text-sm text-zinc-100 focus:border-cyan-500 focus:outline-none font-mono"
          />
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
            {isSubmitting ? "Updating..." : "Update Option"}
          </button>
        </div>
      </form>
    </Modal>
  );
};
