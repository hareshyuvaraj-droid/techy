from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from models import Zone
from auth.routes import get_current_user, require_admin

router = APIRouter()

class ZoneCreate(BaseModel):
    zone_id: str; name: str; capacity: int; location: str = ""

class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    location: Optional[str] = None

@router.get("/")
async def get_zones(user=Depends(get_current_user)):
    zones = await Zone.find_all().to_list()
    return [{"id": str(z.id), "zone_id": z.zone_id, "name": z.name,
             "capacity": z.capacity, "count": z.count,
             "density_pct": z.density_pct, "status": z.status,
             "location": z.location, "updated_at": z.updated_at} for z in zones]

@router.get("/{zone_id}")
async def get_zone(zone_id: str, user=Depends(get_current_user)):
    z = await Zone.find_one(Zone.zone_id == zone_id)
    if not z: raise HTTPException(404, "Zone not found")
    return {"id": str(z.id), "zone_id": z.zone_id, "name": z.name,
            "capacity": z.capacity, "count": z.count,
            "density_pct": z.density_pct, "status": z.status,
            "location": z.location, "updated_at": z.updated_at}

@router.post("/")
async def add_zone(req: ZoneCreate, admin=Depends(require_admin)):
    if await Zone.find_one(Zone.zone_id == req.zone_id.upper()):
        raise HTTPException(409, "Zone already exists")
    await Zone(zone_id=req.zone_id.upper(), name=req.name,
               capacity=req.capacity, location=req.location).insert()
    return {"message": f"Zone {req.zone_id} created"}

@router.patch("/{zone_id}")
async def update_zone(zone_id: str, req: ZoneUpdate, admin=Depends(require_admin)):
    z = await Zone.find_one(Zone.zone_id == zone_id)
    if not z: raise HTTPException(404, "Zone not found")
    if req.name:     z.name     = req.name
    if req.capacity: z.capacity = req.capacity
    if req.location: z.location = req.location
    await z.save()
    return {"message": "Zone updated"}
