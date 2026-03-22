from fastapi import APIRouter, Query, Depends, HTTPException
import logging
from app.api.deps import frontend_api_key_required

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stations", tags=["Station"], summary="Search charging stations by location")
async def search_stations(
    lat: float = Query(..., description="Latitude (required)", ge=-90, le=90),
    lon: float = Query(..., description="Longitude (required)", ge=-180, le=180),
    radius: int = Query(..., description="Search radius in meters (required) - 5000,10000,15000", ge=100, le=15000),
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(20, description="Results per page", ge=1, le=100),
    _: bool = Depends(frontend_api_key_required)
):
    try:
        return {
            "message": "Station search endpoint is ready",
            "status": "active",
            "parameters": {"lat": lat, "lon": lon, "radius": radius, "page": page, "limit": limit}
        }
    except Exception as e:
        logger.error(f"Error in station search: {e}")
        raise HTTPException(status_code=500, detail="Station search temporarily unavailable")


@router.get("/stations/{station_id}", tags=["Station"], summary="Get station details")
async def get_station_detail(
    station_id: str,
    _: bool = Depends(frontend_api_key_required)
):
    return {"message": "Station detail endpoint is ready", "station_id": station_id}


@router.get("/stations/{station_id}/chargers", tags=["Station"], summary="Get chargers for station")
async def get_station_chargers(
    station_id: str,
    _: bool = Depends(frontend_api_key_required)
):
    return {"message": "Station chargers endpoint is ready", "station_id": station_id}
