from fastapi import APIRouter, Depends, Query, status, UploadFile, File, HTTPException
from typing import List, Optional
import os
import uuid

from core.dependencies import get_db, require_role
from core.enums import Role
from core.schemas import CurrentUser, MessageResponse
from modules.inventory.schemas import (
    ChemicalCreate, ChemicalUpdate, ChemicalOut,
    InventoryLocationCreate, InventoryLocationUpdate, InventoryLocationOut
)
from modules.inventory.repository import get_inventory_repository
from modules.inventory.service import InventoryService

router = APIRouter()

def get_inventory_service(db=Depends(get_db)) -> InventoryService:
    repo = get_inventory_repository(db)
    return InventoryService(repo)

# ═══════════════════════════════════════════════════════════════
# Locations
# ═══════════════════════════════════════════════════════════════

@router.post("/locations", response_model=InventoryLocationOut, status_code=status.HTTP_201_CREATED)
def create_location(
    data: InventoryLocationCreate,
    service: InventoryService = Depends(get_inventory_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    """Create a new storage location (Admin only)."""
    return service.create_location(data)

@router.get("/locations", response_model=List[InventoryLocationOut])
def list_locations(
    service: InventoryService = Depends(get_inventory_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    """List all inventory storage locations."""
    return service.list_locations()

@router.patch("/locations/{location_id}", response_model=InventoryLocationOut)
def update_location(
    location_id: str,
    data: InventoryLocationUpdate,
    service: InventoryService = Depends(get_inventory_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    """Update a location's details (Admin only)."""
    return service.update_location(location_id, data)

@router.delete("/locations/{location_id}", response_model=MessageResponse)
def delete_location(
    location_id: str,
    service: InventoryService = Depends(get_inventory_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    """Delete a storage location. Fails if it contains chemicals."""
    try:
        service.delete_location(location_id)
        return MessageResponse(message="Location deleted successfully")
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))

# ═══════════════════════════════════════════════════════════════
# Chemicals
# ═══════════════════════════════════════════════════════════════

@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF))
):
    """Upload a chemical image to the local server."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join("uploads", filename)
    
    with open(filepath, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    # Return the relative URL to the uploaded file
    return {"url": f"http://localhost:8000/uploads/{filename}"}


@router.post("", response_model=ChemicalOut, status_code=status.HTTP_201_CREATED)
def add_chemical(
    data: ChemicalCreate, 
    service: InventoryService = Depends(get_inventory_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF))
):
    """Register a new chemical in the inventory."""
    return service.add_chemical(data, current_user.user_id)

@router.get("", response_model=List[ChemicalOut])
def list_chemicals(
    location_id: Optional[str] = None,
    hazard_class: Optional[str] = None,
    service: InventoryService = Depends(get_inventory_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    """List chemicals, optionally filtered by location and hazard class."""
    return service.list_chemicals(location_id, hazard_class)

@router.get("/{chemical_id}", response_model=ChemicalOut)
def get_chemical(
    chemical_id: str,
    service: InventoryService = Depends(get_inventory_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    return service.get_chemical(chemical_id)

@router.patch("/{chemical_id}", response_model=ChemicalOut)
def update_chemical(
    chemical_id: str,
    data: ChemicalUpdate,
    service: InventoryService = Depends(get_inventory_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF))
):
    """Update chemical quantity or storage location."""
    return service.update_chemical(chemical_id, data, current_user.user_id)

@router.delete("/{chemical_id}", response_model=MessageResponse)
def delete_chemical(
    chemical_id: str,
    service: InventoryService = Depends(get_inventory_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    """Remove a chemical from the system completely (Admin only)."""
    service.delete_chemical(chemical_id, current_user.user_id)
    return MessageResponse(message="Chemical removed successfully")
