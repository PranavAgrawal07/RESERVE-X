"""
RESERVE-X API Client for connecting Agent Simulation to the RESERVE-X reservation service.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

try:
    from .resources import RESOURCE_TO_CAPABILITY_MAP, map_resource_to_capability
except ImportError:
    from resources import RESOURCE_TO_CAPABILITY_MAP, map_resource_to_capability


class ReserveXClient:
    """
    Lightweight HTTP client for RESERVE-X API using Python standard library.
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        data: dict[str, Any] | None = None,
        raise_on_error: bool = False,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {
            "Accept": "application/json",
        }
        body_bytes = None
        if data is not None:
            headers["Content-Type"] = "application/json"
            body_bytes = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                res_data = response.read().decode("utf-8")
                return json.loads(res_data) if res_data else {}
        except urllib.error.HTTPError as e:
            if raise_on_error:
                raise
            res_data = e.read().decode("utf-8")
            try:
                error_body = json.loads(res_data) if res_data else {}
            except Exception:
                error_body = {"raw": res_data}
            if isinstance(error_body, dict):
                error_body["status_code"] = e.code
            return error_body


    def create_option(
        self,
        agent_id: str,
        capability: str,
        probability: float,
        expires_at: str,
    ) -> dict[str, Any]:
        """
        Create a conditional ResourceOption via POST /api/v1/options.
        """
        payload = {
            "agent_id": agent_id,
            "capability": capability,
            "probability": probability,
            "expires_at": expires_at,
        }
        return self._request("POST", "/api/v1/options", data=payload)

    def get_options(self) -> dict[str, Any]:
        """
        Retrieve all ResourceOptions via GET /api/v1/options.
        """
        return self._request("GET", "/api/v1/options")

    def get_risk(self) -> dict[str, Any]:
        """
        Retrieve current system risk metrics via GET /api/v1/risk.
        """
        return self._request("GET", "/api/v1/risk")

    def get_status(self) -> dict[str, Any]:
        """
        Retrieve system status via GET /api/v1/status.
        """
        return self._request("GET", "/api/v1/status")

    def get_events(self) -> dict[str, Any]:
        """
        Retrieve system event logs via GET /api/v1/events.
        """
        return self._request("GET", "/api/v1/events")

    def cancel_option(self, option_id: str) -> dict[str, Any]:
        """
        Cancel a pending option via POST /api/v1/options/{option_id}/cancel.
        """
        return self._request("POST", f"/api/v1/options/{option_id}/cancel")

    def exercise_option(self, option_id: str) -> dict[str, Any]:
        """
        Exercise a pending option via POST /api/v1/options/{option_id}/exercise.
        """
        return self._request("POST", f"/api/v1/options/{option_id}/exercise")

    def release_allocation(self, allocation_id: str) -> dict[str, Any]:
        """
        Release an active allocation via POST /api/v1/allocations/{allocation_id}/release.
        """
        return self._request("POST", f"/api/v1/allocations/{allocation_id}/release")


class MockReserveXClient:
    """
    In-memory test double for ReserveXClient.
    Enables thorough unit testing without requiring a live backend service.
    """

    def __init__(self):
        self.options: list[dict[str, Any]] = []
        self.exercised_options: list[str] = []
        self.cancelled_options: list[str] = []
        self.released_allocations: list[str] = []

    def create_option(
        self,
        agent_id: str,
        capability: str,
        probability: float,
        expires_at: str,
    ) -> dict[str, Any]:
        option_id = f"opt-{len(self.options) + 1:04d}"
        record = {
            "id": option_id,
            "option_id": option_id,
            "agent_id": agent_id,
            "capability": capability,
            "probability": probability,
            "expires_at": expires_at,
            "status": "PENDING",
        }
        self.options.append(record)
        return record

    def get_options(self) -> list[dict[str, Any]]:
        return list(self.options)

    def get_risk(self) -> dict[str, Any]:
        risk_by_capability: dict[str, Any] = {}
        for opt in self.options:
            if opt["status"] != "PENDING":
                continue
            cap = opt["capability"]
            if cap not in risk_by_capability:
                risk_by_capability[cap] = {
                    "total_probability": 0.0,
                    "competing_agents": [],
                    "risk_level": "LOW",
                }
            risk_by_capability[cap]["total_probability"] += opt["probability"]
            risk_by_capability[cap]["competing_agents"].append(opt["agent_id"])

        for cap, info in risk_by_capability.items():
            tot = round(info["total_probability"], 2)
            info["total_probability"] = tot
            if tot > 1.5 or len(info["competing_agents"]) >= 3:
                info["risk_level"] = "HIGH"
            elif tot > 0.8 or len(info["competing_agents"]) >= 2:
                info["risk_level"] = "MEDIUM"

        return {"risk": risk_by_capability}

    def exercise_option(self, option_id: str) -> dict[str, Any]:
        self.exercised_options.append(option_id)
        for opt in self.options:
            if opt["option_id"] == option_id:
                opt["status"] = "EXERCISED"
                return {
                    "id": f"alloc-{option_id}",
                    "option_id": option_id,
                    "resource_id": f"res-{opt['capability']}",
                    "agent_id": opt["agent_id"],
                    "capability": opt["capability"],
                    "amount": 1,
                    "allocated_at": "2026-09-22T00:00:00Z",
                    "released_at": None,
                }
        return {"error": "Option not found"}

    def cancel_option(self, option_id: str) -> dict[str, Any]:
        self.cancelled_options.append(option_id)
        for opt in self.options:
            if opt["option_id"] == option_id:
                opt["status"] = "CANCELLED"
                return opt
        return {"error": "Option not found"}

    def release_allocation(self, allocation_id: str) -> dict[str, Any]:
        self.released_allocations.append(allocation_id)
        return {
            "id": allocation_id,
            "released_at": "2026-09-22T00:00:00Z",
        }
