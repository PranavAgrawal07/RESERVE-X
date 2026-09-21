/**
 * Frontend Agent Metadata Registry
 * 
 * NOTE: The backend does not maintain an Agent table/model.
 * These profiles provide rich display metadata (names, roles, colors, icons)
 * for known simulation agents while gracefully falling back for any arbitrary agent_id.
 */

export interface AgentMetadata {
  id: string;
  name: string;
  role: string;
  badgeColor: string;
  avatarColor: string;
  description: string;
  defaultCapabilities: string[];
}

export const KNOWN_AGENTS: Record<string, AgentMetadata> = {
  "agent-001": {
    id: "agent-001",
    name: "Coding Agent",
    role: "Software Engineering & Implementation",
    badgeColor: "border-sky-500/30 bg-sky-500/10 text-sky-400",
    avatarColor: "from-sky-600 to-blue-700",
    description: "Executes code generation, debugging workflows, and local unit test runs.",
    defaultCapabilities: ["TERMINAL", "TESTING", "LLM_INFERENCE", "DEPLOYMENT"],
  },
  "agent-002": {
    id: "agent-002",
    name: "Research Agent",
    role: "Information Synthesis & Web Search",
    badgeColor: "border-purple-500/30 bg-purple-500/10 text-purple-400",
    avatarColor: "from-purple-600 to-indigo-700",
    description: "Queries web tools, extracts real-time docs, and performs deep topic synthesis.",
    defaultCapabilities: ["WEB_SEARCH", "LLM_INFERENCE"],
  },
  "agent-003": {
    id: "agent-003",
    name: "Testing Agent",
    role: "QA & Integration Testing",
    badgeColor: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
    avatarColor: "from-emerald-600 to-teal-700",
    description: "Prepares regression suites, test environments, and failure diagnostics.",
    defaultCapabilities: ["TESTING", "TERMINAL", "LLM_INFERENCE"],
  },
  "agent-004": {
    id: "agent-004",
    name: "Security Agent",
    role: "Vulnerability Scanning & Audit",
    badgeColor: "border-rose-500/30 bg-rose-500/10 text-rose-400",
    avatarColor: "from-rose-600 to-red-700",
    description: "Performs dependency vulnerability scans and security posture verification.",
    defaultCapabilities: ["SECURITY_SCAN", "TESTING", "LLM_INFERENCE"],
  },
  "agent-005": {
    id: "agent-005",
    name: "Data Analysis Agent",
    role: "Data Pipelines & GPU Compute",
    badgeColor: "border-amber-500/30 bg-amber-500/10 text-amber-400",
    avatarColor: "from-amber-600 to-orange-700",
    description: "Loads datasets, queries analytics databases, and runs heavy GPU inference jobs.",
    defaultCapabilities: ["DATABASE", "GPU_COMPUTE", "LLM_INFERENCE"],
  },
};

/**
 * Safely resolves an agent's display name.
 * If the agent is unknown, falls back to "Agent {agent_id}" or "Unknown Agent".
 */
export function getAgentDisplayName(agentId?: string | null): string {
  if (!agentId) return "System Agent";
  const known = KNOWN_AGENTS[agentId];
  if (known) return known.name;
  return `Agent ${agentId}`;
}

/**
 * Returns the full metadata for an agent, generating a clean fallback if not in the registry.
 */
export function getAgentMetadata(agentId: string): AgentMetadata {
  const known = KNOWN_AGENTS[agentId];
  if (known) return known;

  return {
    id: agentId,
    name: `Agent ${agentId}`,
    role: "Autonomous AI Agent",
    badgeColor: "border-zinc-700 bg-zinc-800/40 text-zinc-300",
    avatarColor: "from-zinc-600 to-zinc-800",
    description: "Autonomous task execution agent interacting with RESERVE-X resources.",
    defaultCapabilities: [],
  };
}
