export type CapabilityType =
  | "GPU_COMPUTE"
  | "CODE_EXECUTION"
  | "WEB_SEARCH"
  | "LLM_INFERENCE"
  | "TESTING"
  | "TERMINAL"
  | "DATABASE"
  | "SECURITY_SCAN"
  | "DEPLOYMENT"
  | string;

export type OptionStatus = "PENDING" | "EXERCISED" | "EXPIRED" | "CANCELLED";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type EventType =
  | "OPTION_CREATED"
  | "OPTION_EXERCISED"
  | "OPTION_EXPIRED"
  | "OPTION_CANCELLED"
  | "OPTION_UPDATED"
  | "EXERCISE_FAILED"
  | "ALLOCATION_CREATED"
  | "ALLOCATION_RELEASED"
  | "RESOURCE_REGISTERED";

export interface Resource {
  id: string;
  name: string;
  capability: CapabilityType;
  total_capacity: number;
  allocated_capacity: number;
  created_at: string;
  available_capacity: number;
}

export interface ResourceOption {
  id: string;
  agent_id: string;
  capability: CapabilityType;
  probability: number;
  amount: number;
  priority: number;
  status: OptionStatus;
  created_at: string;
  expires_at: string;
  exercised_at?: string | null;
  cancelled_at?: string | null;
}

export interface Allocation {
  id: string;
  option_id: string;
  resource_id: string;
  agent_id: string;
  capability: CapabilityType;
  amount: number;
  allocated_at: string;
  released_at?: string | null;
}

export interface RiskReport {
  capability: CapabilityType;
  resource_ids: string[];
  total_capacity: number;
  allocated_capacity: number;
  available_capacity: number;
  pending_options_count: number;
  total_pending_demand: number;
  expected_demand: number;
  overcommit_probability: number;
  risk_level: RiskLevel;
}

export interface SystemRiskSummary {
  timestamp: string;
  capability_risks: RiskReport[];
  highest_risk_level: RiskLevel;
  total_pending_options: number;
  total_active_allocations: number;
}

export interface SystemStatus {
  timestamp: string;
  resources: Resource[];
  options: ResourceOption[];
  allocations: Allocation[];
  risk: SystemRiskSummary;
}

export interface EventLog {
  id: string;
  timestamp: string;
  event_type: EventType;
  agent_id?: string | null;
  option_id?: string | null;
  resource_id?: string | null;
  details: Record<string, any>;
}

export interface CreateResourceRequest {
  name: string;
  capability: string;
  total_capacity: number;
}

export interface CreateOptionRequest {
  agent_id: string;
  capability: string;
  probability: number;
  amount?: number;
  priority?: number;
  expires_at: string;
}

export interface UpdateOptionRequest {
  probability?: number | null;
  expires_at?: string | null;
}

// ── What-If Simulation ──────────────────────────────────────────

export interface WhatIfRequest {
  agent_count: number;
  resource_capacity: number;
  average_probability: number;
}

export interface WhatIfMetrics {
  capacity: number;
  pending_options?: number | null;
  agent_count?: number | null;
  expected_demand: number;
  overcommit_probability: number;
  risk_level: RiskLevel;
}

export interface WhatIfResponse {
  current: WhatIfMetrics;
  scenario: WhatIfMetrics;
}

// ── Offline Resilience & Connectivity ───────────────────────────

export interface QueueStats {
  total: number;
  pending: number;
  failed: number;
  synced: number;
}

export interface ConnectivityStatus {
  mode: "ONLINE" | "OFFLINE";
  is_offline: boolean;
  offline_reason?: string | null;
  outage_started_at: string | null;
  queue_stats: QueueStats;
  db_path: string;
}

export interface SyncResult {
  synced: number;
  failed: number;
  remaining_pending: number;
}

export interface ReconnectResponse {
  mode: "ONLINE" | "OFFLINE";
  outage_duration_seconds: number | null;
  sync: SyncResult;
}

export interface QueuedOperation {
  operation_id: string;
  idempotency_key: string;
  operation_type: string;
  timestamp: string;
  agent_id: string;
  capability: string;
  probability: number;
  amount: number;
  priority: number;
  expires_at: string;
  payload_json: string;
  sync_status: "PENDING" | "SYNCED" | "FAILED";
  retry_count: number;
  error_message?: string | null;
  synced_at?: string | null;
  reconciled_option_id?: string | null;
  local_risk_level?: string | null;
  local_expected_demand?: number | null;
}

export interface OfflineEventLog {
  event_id: string;
  operation_id?: string | null;
  event_type: string;
  timestamp: string;
  details: Record<string, any>;
}
