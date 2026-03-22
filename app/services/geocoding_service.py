import logging
import math
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


class GeocodingService:
    def __init__(self):
        self.timeout = 10.0

    async def reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """좌표를 시/군/구/동 수준 주소로 변환합니다 (Nominatim 사용)."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://nominatim.openstreetmap.org/reverse",
                    params={"format": "json", "lat": lat, "lon": lon, "zoom": 10, "addressdetails": 1, "accept-language": "ko"},
                    headers={"User-Agent": "EVChargingStationApp/1.0"}
                )
                response.raise_for_status()
                data = response.json()

                if "address" not in data:
                    return None

                address = data["address"]
                state = address.get("state") or address.get("province") or ""
                city = address.get("city") or address.get("county") or address.get("town") or ""
                district = address.get("suburb") or address.get("neighbourhood") or address.get("quarter") or ""

                addr_parts = [p for p in [state, city, district] if p]
                return " ".join(addr_parts) if addr_parts else None

        except Exception as e:
            logger.error(f"Reverse geocoding failed for ({lat}, {lon}): {e}")
            return None

    def calculate_distance_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """하버사인 공식으로 두 좌표 간 거리(km)를 계산합니다."""
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return 6371 * 2 * math.asin(math.sqrt(a))

    def is_within_radius(self, center_lat: float, center_lon: float,
                         point_lat: float, point_lon: float, radius_m: int) -> bool:
        return self.calculate_distance_km(center_lat, center_lon, point_lat, point_lon) <= (radius_m / 1000)


geocoding_service = GeocodingService()