from fastapi import APIRouter, Depends, Query, status, UploadFile, File, HTTPException, Request
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
    request: Request,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF))
):
    """Upload a chemical image."""
    import shutil
    from pathlib import Path

    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = upload_dir / filename

    with filepath.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"url": f"/uploads/{filename}"}

import csv
import io
from core.enums import HazardClass

@router.post("/locations/{location_id}/import")
async def import_chemicals_csv(
    location_id: str,
    file: UploadFile = File(...),
    service: InventoryService = Depends(get_inventory_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF))
):
    """Import chemicals from a CSV file directly into a location."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
        
    content = await file.read()
    try:
        decoded = content.decode('utf-8-sig') # Handle BOM if present
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Please upload a UTF-8 CSV.")
        
    reader = csv.DictReader(io.StringIO(decoded))
    print(f"DEBUG: CSV Headers read: {reader.fieldnames}", flush=True)
    
    success_count = 0
    errors = []
    
    # Define aliases for common header names
    name_aliases = ["name", "chemical name", "chemical", "label"]
    cas_aliases = ["cas_number", "cas number", "cas", "cas no", "cas_no", "cas #", "casnumber"]
    hazard_aliases = ["hazard_class", "hazard class", "hazard", "hazard category", "hazardclass"]
    qty_aliases = ["quantity", "qty", "amount", "count"]
    unit_aliases = ["unit", "units", "measurement"]
    desc_aliases = ["description", "desc", "details", "info", "notes", "comments", "remarks", "about"]
    image_aliases = ["image_url", "image url", "image", "photo", "picture", "photo_url", "photo url"]
    
    for row_num, row in enumerate(reader, start=2):
        try:
            # Normalize keys to lowercase and stripped string
            row_norm = {str(k).strip().lower(): v for k, v in row.items() if k is not None}
            print(f"DEBUG: Row normalized data: {row_norm}", flush=True)
            
            def get_val(aliases, default=""):
                for alias in aliases:
                    if alias in row_norm:
                        val = row_norm[alias]
                        return str(val).strip() if val is not None else default
                return default
                
            name = get_val(name_aliases)
            if not name:
                continue
                
            hazard_raw = get_val(hazard_aliases, "non_hazardous").lower()
            try:
                hazard_class = HazardClass(hazard_raw)
            except ValueError:
                # Handle cases like "toxic" -> "toxic", or map spaces to underscores
                hazard_raw_clean = hazard_raw.replace(" ", "_")
                try:
                    hazard_class = HazardClass(hazard_raw_clean)
                except ValueError:
                    hazard_class = HazardClass.NON_HAZARDOUS
                
            qty_raw = get_val(qty_aliases, "0")
            try:
                quantity = float(qty_raw) if qty_raw else 0.0
            except ValueError:
                quantity = 0.0
                
            chem_create = ChemicalCreate(
                location_id=location_id,
                name=name,
                cas_number=get_val(cas_aliases) or None,
                hazard_class=hazard_class,
                quantity=quantity,
                unit=get_val(unit_aliases, "mL") or "mL",
                description=get_val(desc_aliases) or None,
                image_url=get_val(image_aliases) or None
            )
            
            service.add_chemical(chem_create, current_user.user_id)
            success_count += 1
            
        except Exception as e:
            errors.append(f"Row {row_num} error: {str(e)}")
            
    return {"message": f"Successfully imported {success_count} chemicals.", "errors": errors}


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
