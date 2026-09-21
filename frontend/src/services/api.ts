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
} from "../types/reservex";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

export class ApiError extends Error {
  status: number;
  data: any;
  isConflict: boolean;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
    this.isConflict = status === 409;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...(options.headers || {}),
  };

  try {
    const response = await fetch(url, { ...options, headers });
    let responseData: any = null;
    const text = await response.text();
    if (text) {
      try {
        responseData = JSON.parse(text);
      } catch {
        responseData = text;
      }
    }

    if (!response.ok) {
      const errorMessage =
        (typeof responseData === "object" && responseData?.detail) ||
        (typeof responseData === "string" && responseData) ||
        `HTTP ${response.status}: ${response.statusText}`;

      throw new ApiError(response.status, errorMessage, responseData);
    }

    return responseData as T;
  } catch (err: any) {
    if (err instanceof ApiError) {
      throw err;
    }
    // Network or connection error (e.g. backend offline)
    throw new ApiError(0, err.message || "Failed to communicate with backend", err);
  }
}

export const api = {
  // System
  getStatus: () => request<SystemStatus>("/status"),
  getRisk: () => request<SystemRiskSummary>("/risk"),
  getEvents: (params?: { event_type?: string; agent_id?: string; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.event_type) searchParams.set("event_type", params.event_type);
    if (params?.agent_id) searchParams.set("agent_id", params.agent_id);
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    const query = searchParams.toString();
    return request<EventLog[]>(`/events${query ? `?${query}` : ""}`);
  },

  // Resources
  getResources: () => request<Resource[]>("/resources"),
  createResource: (data: CreateResourceRequest) =>
    request<Resource>("/resources", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Options
  getOptions: (params?: { agent_id?: string; capability?: string; status?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.agent_id) searchParams.set("agent_id", params.agent_id);
    if (params?.capability) searchParams.set("capability", params.capability);
    if (params?.status) searchParams.set("status", params.status);
    const query = searchParams.toString();
    return request<ResourceOption[]>(`/options${query ? `?${query}` : ""}`);
  },
  createOption: (data: CreateOptionRequest) =>
    request<ResourceOption>("/options", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateOption: (optionId: string, data: UpdateOptionRequest) =>
    request<ResourceOption>(`/options/${optionId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  exerciseOption: (optionId: string) =>
    request<Allocation>(`/options/${optionId}/exercise`, {
      method: "POST",
    }),
  cancelOption: (optionId: string) =>
    request<ResourceOption>(`/options/${optionId}/cancel`, {
      method: "POST",
    }),

  // Allocations
  releaseAllocation: (allocationId: string) =>
    request<Allocation>(`/allocations/${allocationId}/release`, {
      method: "POST",
    }),
};
