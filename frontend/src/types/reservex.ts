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
