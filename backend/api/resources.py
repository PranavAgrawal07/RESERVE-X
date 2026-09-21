"""Resources API router."""

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from backend.models.enums import CapabilityType
from backend.models.resource import Resource
from backend.engine import resource_manager

router = APIRouter(prefix="/resources", tags=["resources"])


# ── Request schemas ──────────────────────────────────────────────

class CreateResourceRequest(BaseModel):
    name: str
    capability: CapabilityType
    total_capacity: int = Field(ge=1)


# ── Endpoints ────────────────────────────────────────────────────

@router.post("", response_model=Resource, status_code=201)
def create_resource(req: CreateResourceRequest):
    """Register a new scarce resource."""
    return resource_manager.register_resource(
        name=req.name,
        capability=req.capability,
        total_capacity=req.total_capacity,
    )


@router.get("", response_model=list[Resource])
def list_resources():
    """List all registered resources with capacity info."""
    return resource_manager.get_all_resources()
