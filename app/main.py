import contextlib
import time
from datetime import datetime, timezone, timedelta
import os

from fastapi import FastAPI, Depends, HTTPException, status, APIRouter, Response, Header, Query, Path
from typing import Optional
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from redis.asyncio import Redis
import httpx
import math
import json
import re

from app.core.config import settings
from app.db.database import get_async_session
from app.redis_client import (
    init_redis_pool,
    close_redis_pool,
    get_redis_client,
    set_cache,
    get_cache
)
from app.api.v1.api import api_router
from app.api.deps import frontend_api_key_required

IS_ADMIN = os.getenv("ADMIN_MODE", "false").lower() == "true"

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis_pool()
    yield
    await close_redis_pool()

security = HTTPBasic()
raw_admins = os.getenv("ADMIN_CREDENTIALS", "")
ADMIN_ACCOUNTS = dict([cred.split(":") for cred in raw_admins.split(",") if cred])

def admin_required(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username not in ADMIN_ACCOUNTS or ADMIN_ACCOUNTS[credentials.username] != credentials.password:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


def ensure_read_only_sql(sql: str):
    """SELECT 쿼리만 허용하는 방어적 가드. DB 사용자 권한과 병행해서 사용해야 함."""
    if not sql.strip().lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Only read-only SELECT queries are allowed")

# --- FastAPI Application 생성 ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    description="Codyssey EV Charging Station API",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json" if IS_ADMIN else None
)

# --- CORS: restrict origins to allowed list from env ---
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
else:
    allowed_origins = []

if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- 관리자용 docs & redoc 엔드포인트 ---
if IS_ADMIN:
    @app.get("/docs", include_in_schema=False)
    async def get_docs(credentials: HTTPBasicCredentials = Depends(admin_required)):
        return get_swagger_ui_html(openapi_url=app.openapi_url, title=f"{settings.PROJECT_NAME} - Swagger UI")

    @app.get("/redoc", include_in_schema=False)
    async def get_redoc(credentials: HTTPBasicCredentials = Depends(admin_required)):
        return get_redoc_html(openapi_url=app.openapi_url, title=f"{settings.PROJECT_NAME} - ReDoc")

# --- 기본 헬스 체크 엔드포인트 ---
@app.get("/", tags=["Infrastructure"])
def read_root():
    return {
        "message": "Server is running successfully!",
        "project": settings.PROJECT_NAME,
        "api_version": settings.API_VERSION
    }


@app.head("/", include_in_schema=False)
def head_root():
    return Response(status_code=200)


@app.get("/health", tags=["Infrastructure"], summary="Health check (DB & Redis)")
@app.head("/health")
async def health_check(db: AsyncSession = Depends(get_async_session), redis_client: Redis = Depends(get_redis_client)):
    db_ok = False
    redis_ok = False

    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    try:
        if redis_client:
            await redis_client.ping()
            redis_ok = True
    except Exception:
        pass

    if db_ok or redis_ok:
        return JSONResponse(status_code=200, content={"status": "ok", "db": db_ok, "redis": redis_ok})
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"status": "down", "db": db_ok, "redis": redis_ok})


def _query_subsidies(manufacturer: str, model_group: str):
    return (
        "SELECT model_name, subsidy_national_10k_won, subsidy_local_10k_won, subsidy_total_10k_won, sale_price "
        "FROM subsidies "
        "WHERE manufacturer = :manufacturer AND model_group = :model_group "
        "ORDER BY model_name LIMIT 100"
    )


def _map_subsidy_rows(rows) -> list:
    mapped = []
    for r in rows:
        m = r._mapping
        nat = m.get("subsidy_national_10k_won")
        loc = m.get("subsidy_local_10k_won")
        tot = m.get("subsidy_total_10k_won")
        mapped.append({
            "model_name": m.get("model_name"),
            "subsidy_national": int(nat) if nat is not None else None,
            "subsidy_local": int(loc) if loc is not None else None,
            "subsidy_total": int(tot) if tot is not None else None,
            "salePrice": int(m.get("sale_price")) if m.get("sale_price") is not None else None,
        })
    return mapped


@app.get("/subsidy", tags=["Subsidy"], summary="Lookup subsidies by manufacturer and model_group")
async def subsidy_lookup(manufacturer: str, model_group: str, db: AsyncSession = Depends(get_async_session), _ok: bool = Depends(frontend_api_key_required)):
    try:
        query_sql = _query_subsidies(manufacturer, model_group)
        ensure_read_only_sql(query_sql)
        result = await db.execute(text(query_sql), {"manufacturer": manufacturer, "model_group": model_group})
        return JSONResponse(status_code=200, content=_map_subsidy_rows(result.fetchall()))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/subsidy/by", tags=["Subsidy"], summary="Lookup subsidies (camelCase) by manufacturer and modelGroup")
async def subsidy_lookup_camel(manufacturer: str, modelGroup: str, db: AsyncSession = Depends(get_async_session), _ok: bool = Depends(frontend_api_key_required)):
    """camelCase modelGroup 파라미터를 허용하는 호환성 래퍼."""
    try:
        query_sql = _query_subsidies(manufacturer, modelGroup)
        ensure_read_only_sql(query_sql)
        result = await db.execute(text(query_sql), {"manufacturer": manufacturer, "model_group": modelGroup})
        return JSONResponse(status_code=200, content=_map_subsidy_rows(result.fetchall()))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stations", tags=["Station"], summary="충전소 검색")
async def search_ev_stations_requirement_compliant(
    lat: str = Query(..., description="사용자 위도 (string 타입)", regex=r"^-?\d+\.?\d*$"),
    lon: str = Query(..., description="사용자 경도 (string 타입)", regex=r"^-?\d+\.?\d*$"),
    radius: int = Query(..., description="반경(m) - 5000,10000,15000 기준", ge=100, le=15000),
    page: int = Query(1, description="페이지 번호", ge=1),
    limit: int = Query(20, description="페이지당 결과 수", ge=1, le=100),
    api_key: str = Depends(frontend_api_key_required),
    db: AsyncSession = Depends(get_async_session),
    redis_client: Redis = Depends(get_redis_client)
):
    """좌표 → 주소 변환 후 캐시/DB/KEPCO API 순서로 충전소를 조회합니다."""
    try:
        lat_float = float(lat)
        lon_float = float(lon)

        # 좌표 → 시/군/구 주소 변환 (Nominatim)
        async with httpx.AsyncClient() as client:
            nominatim_response = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={
                    "lat": lat_float,
                    "lon": lon_float,
                    "format": "json",
                    "accept-language": "ko",
                    "addressdetails": 1
                },
                headers={"User-Agent": "Codyssey-EV-App/1.0"},
                timeout=10.0
            )

            addr = "서울특별시"
            if nominatim_response.status_code == 200:
                address_components = nominatim_response.json().get("address", {})
                city = address_components.get("city") or address_components.get("town") or ""
                district = address_components.get("borough") or address_components.get("suburb") or ""
                addr = f"{city} {district}".strip() or "서울특별시"

        # 반경을 최소 캐노니컬 버킷으로 정규화 (5000 / 10000 / 15000)
        radius_standards = [5000, 10000, 15000]
        try:
            requested_radius = int(round(float(radius)))
        except Exception:
            requested_radius = radius
        actual_radius = next((r for r in radius_standards if requested_radius <= r), radius_standards[-1])

        # 캐시 키 생성 (좌표를 반올림하여 미세한 차이로 인한 키 분산 방지)
        coord_decimals = getattr(settings, "CACHE_COORD_ROUND_DECIMALS", 2)
        lat_round = round(lat_float, coord_decimals)
        lon_round = round(lon_float, coord_decimals)
        cache_key = f"stations:lat{lat_round}:lon{lon_round}:r{actual_radius}:p{page}:l{limit}"
        persistent_key = f"stations_persistent:lat{lat_round}:lon{lon_round}:r{actual_radius}:p{page}:l{limit}"

        try:
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                cached_result = json.loads(cached_data)
                filtered_stations = []
                for station in cached_result.get("stations", []):
                    dist = calculate_distance_haversine(
                        lat_float, lon_float,
                        float(station["lat"]), float(station["lon"])
                    )
                    if dist <= radius:
                        station_out = dict(station)
                        station_out["distance_m"] = str(int(dist))
                        try:
                            counts_q = "SELECT COUNT(*) AS total_ch, COALESCE(SUM( (cp_stat::text = '1')::int ), 0) AS avail_ch FROM chargers WHERE cs_id = :cs_id"
                            cnt_res = await db.execute(text(counts_q), {"cs_id": station_out.get("station_id")})
                            cnt_row = cnt_res.fetchone()
                            if cnt_row:
                                total_ch = int(cnt_row._mapping.get("total_ch") or 0)
                                avail_ch = int(cnt_row._mapping.get("avail_ch") or 0)
                            else:
                                total_ch = 0
                                avail_ch = 0
                        except Exception:
                            total_ch = 0
                            avail_ch = 0

                        station_out["total_chargers"] = total_ch
                        station_out["available_chargers"] = avail_ch
                        filtered_stations.append(station_out)

                filtered_stations.sort(key=lambda x: int(x["distance_m"]))
                try:
                    if redis_client:
                        await redis_client.incr("metrics:stations:cache_hits:short")
                except Exception:
                    pass

                return {
                    "source": "cache",
                    "addr": addr,
                    "radius_normalized": actual_radius,
                    "stations": filtered_stations
                }
            # 단기 캐시 미스 → 장기 정적 캐시 확인
            try:
                persistent_raw = await redis_client.get(persistent_key)
                if persistent_raw:
                    persistent_result = json.loads(persistent_raw)
                    filtered_stations = []
                    station_ids = [s.get("station_id") for s in persistent_result.get("stations", []) if s.get("station_id")]

                    counts_map = {}
                    try:
                        if station_ids:
                            counts_q = """
                                SELECT cs_id, COUNT(*) AS total_ch, COALESCE(SUM( (cp_stat::text = '1')::int ), 0) AS avail_ch
                                FROM chargers
                                WHERE cs_id = ANY(:cs_ids)
                                GROUP BY cs_id
                            """
                            res = await db.execute(text(counts_q), {"cs_ids": station_ids})
                            for r in res.fetchall():
                                m = r._mapping
                                counts_map[str(m.get("cs_id"))] = {
                                    "total": int(m.get("total_ch") or 0),
                                    "avail": int(m.get("avail_ch") or 0)
                                }
                    except Exception:
                        pass

                    for station in persistent_result.get("stations", []):
                        try:
                            dist = calculate_distance_haversine(
                                lat_float, lon_float,
                                float(station["lat"]), float(station["lon"])
                            )
                        except Exception:
                            dist = 999999

                        if dist <= radius:
                            station_out = dict(station)
                            station_out["distance_m"] = str(int(dist))
                            sid = str(station_out.get("station_id")) if station_out.get("station_id") is not None else None
                            if sid and sid in counts_map:
                                station_out["total_chargers"] = counts_map[sid]["total"]
                                station_out["available_chargers"] = counts_map[sid]["avail"]
                            else:
                                station_out["total_chargers"] = None
                                station_out["available_chargers"] = None
                            filtered_stations.append(station_out)

                    filtered_stations.sort(key=lambda x: int(x["distance_m"]))
                    try:
                        if redis_client:
                            await redis_client.incr("metrics:stations:cache_hits:persistent")
                    except Exception:
                        pass

                    return {
                        "source": "persistent_cache",
                        "addr": addr,
                        "radius_normalized": actual_radius,
                        "stations": filtered_stations
                    }
            except Exception:
                pass
        except Exception:
            pass

        try:
            # PostGIS 공간 쿼리 우선 시도, 실패 시 주소 LIKE 쿼리로 폴백
            spatial_query = """
                SELECT DISTINCT
                    cs_id as station_id,
                    COALESCE(address, '') as addr,
                    COALESCE(name, '') as station_name,
                    ST_Y(location)::text as lat,
                    ST_X(location)::text as lon,
                    ROUND(ST_Distance(location::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography))::int as distance_m,
                    (SELECT COUNT(*) FROM chargers WHERE cs_id = stations.cs_id) AS total_chargers,
                    (SELECT COALESCE(SUM( (cp_stat::text = '1')::int ), 0) FROM chargers WHERE cs_id = stations.cs_id) AS available_chargers
                FROM stations
                WHERE location IS NOT NULL
                  AND ST_DWithin(
                      location::geography,
                      ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                      :radius_m
                  )
                ORDER BY distance_m
                LIMIT :limit OFFSET :offset
            """

            fallback_name_query = """
                SELECT DISTINCT
                    cs_id as station_id,
                    COALESCE(address, '') as addr,
                    COALESCE(name, '') as station_name,
                    ST_Y(location)::text as lat,
                    ST_X(location)::text as lon,
                    ROUND(ST_Distance(location::geography, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography))::int as distance_m,
                    (SELECT COUNT(*) FROM chargers WHERE cs_id = stations.cs_id) AS total_chargers,
                    (SELECT COALESCE(SUM( (cp_stat::text = '1')::int ), 0) FROM chargers WHERE cs_id = stations.cs_id) AS available_chargers
                FROM stations
                WHERE (COALESCE(address, '') LIKE :addr_pattern OR COALESCE(name, '') LIKE :addr_pattern)
                AND location IS NOT NULL
                ORDER BY distance_m
                LIMIT :limit OFFSET :offset
            """

            try:
                offset = (page - 1) * limit
                result = await db.execute(
                    text(spatial_query),
                    {"lon": lon_float, "lat": lat_float, "radius_m": actual_radius, "limit": limit, "offset": offset}
                )
            except Exception:
                result = await db.execute(
                    text(fallback_name_query),
                    {
                        "addr_pattern": f"%{addr.split()[0] if addr else '서울'}%",
                        "lon": lon_float,
                        "lat": lat_float
                    }
                )
            db_stations = result.fetchall()

            if db_stations:
                db_result = []
                for row in db_stations:
                    try:
                        row_dict = row._mapping
                        db_distance = row_dict.get("distance_m")
                        try:
                            dist_val = int(db_distance) if db_distance is not None else int(calculate_distance_haversine(
                                lat_float, lon_float, float(row_dict["lat"]), float(row_dict["lon"])
                            ))
                        except Exception:
                            dist_val = int(calculate_distance_haversine(lat_float, lon_float, float(row_dict["lat"]), float(row_dict["lon"])))

                        if dist_val <= radius:
                            db_result.append({
                                "station_id": str(row_dict["station_id"]),
                                "addr": str(row_dict["addr"]),
                                "station_name": str(row_dict["station_name"]),
                                "lat": str(row_dict["lat"]),
                                "lon": str(row_dict["lon"]),
                                "distance_m": str(int(dist_val)),
                                "total_chargers": int(row_dict.get("total_chargers") or 0),
                                "available_chargers": int(row_dict.get("available_chargers") or 0)
                            })
                    except Exception:
                        continue
                
                if db_result:
                    db_result.sort(key=lambda x: calculate_distance_haversine(
                        lat_float, lon_float, float(x["lat"]), float(x["lon"])
                    ))
                    try:
                        cache_stations = [{k: v for k, v in s.items() if k not in ("distance_m", "total_chargers", "available_chargers")} for s in db_result]
                        cache_data = {"stations": _serialize_for_cache(cache_stations), "timestamp": datetime.now(timezone.utc).isoformat()}
                        await redis_client.setex(cache_key, settings.CACHE_EXPIRE_SECONDS, json.dumps(_serialize_for_cache(cache_data), ensure_ascii=False))
                        try:
                            persistent_ttl = getattr(settings, "PERSISTENT_STATION_CACHE_SECONDS", 86400)
                            await redis_client.setex(persistent_key, persistent_ttl, json.dumps(_serialize_for_cache(cache_data), ensure_ascii=False))
                        except Exception:
                            pass
                        try:
                            if redis_client:
                                await redis_client.incr("metrics:stations:cache_hits:db")
                        except Exception:
                            pass
                    except Exception:
                        pass

                    return {
                        "source": "database",
                        "addr": addr,
                        "radius_normalized": actual_radius,
                        "stations": db_result
                    }
        except Exception as db_error:
            try:
                await db.rollback()
            except Exception:
                pass

        kepco_url = settings.EXTERNAL_STATION_API_BASE_URL
        kepco_key = settings.EXTERNAL_STATION_API_KEY

        if not kepco_url or not kepco_key:
            raise HTTPException(status_code=500, detail="KEPCO API 설정 누락")

        async with httpx.AsyncClient() as client:
            kepco_response = await client.get(
                kepco_url,
                params={
                    "addr": addr,
                    "apiKey": kepco_key,
                    "returnType": "json"
                },
                timeout=30.0
            )

            if kepco_response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"KEPCO API 오류: HTTP {kepco_response.status_code}"
                )

            kepco_data = kepco_response.json()

        api_stations = []
        now = datetime.now(timezone.utc)
        
        if isinstance(kepco_data, dict) and "data" in kepco_data:
            raw_data = kepco_data["data"]
            
            if isinstance(raw_data, list):
                for item in raw_data:
                    try:
                        item_lat = float(item.get("lat", 0))
                        item_lon = float(item.get("longi", 0))

                        if item_lat == 0 or item_lon == 0:
                            continue

                        dist = calculate_distance_haversine(lat_float, lon_float, item_lat, item_lon)
                        if dist > radius:
                            continue

                        api_stations.append({
                            "station_id": str(item.get("csId", "")),
                            "addr": str(item.get("addr", "")),
                            "station_name": str(item.get("csNm", "")),
                            "lat": str(item_lat),
                            "lon": str(item_lon),
                            "distance_m": str(int(dist))
                        })

                        try:
                            await _clear_db_transaction(db)
                            insert_sql = """
                                INSERT INTO stations (cs_id, address, name, location, raw_data, last_synced_at)
                                VALUES (:cs_id, :address, :name, ST_SetSRID(ST_MakePoint(:longi, :lat), 4326), :raw_data, :update_time)
                                ON CONFLICT (cs_id) DO UPDATE SET
                                    address = EXCLUDED.address,
                                    name = EXCLUDED.name,
                                    location = EXCLUDED.location,
                                    raw_data = EXCLUDED.raw_data,
                                    last_synced_at = EXCLUDED.last_synced_at
                            """
                            await db.execute(text(insert_sql), {
                                "cs_id": item.get("csId"),
                                "address": item.get("addr"),
                                "name": item.get("csNm"),
                                "lat": item_lat,
                                "longi": item_lon,
                                "raw_data": json.dumps(item, ensure_ascii=False),
                                "update_time": now
                            })
                        except Exception:
                            try:
                                await _clear_db_transaction(db)
                            except Exception:
                                pass

                    except Exception:
                        continue

                try:
                    await db.commit()
                except Exception:
                    await db.rollback()

        api_stations.sort(key=lambda x: calculate_distance_haversine(
            lat_float, lon_float, float(x["lat"]), float(x["lon"])
        ))
        try:
            api_stations = _dedupe_stations_by_id(api_stations)
        except Exception:
            pass

        try:
            if api_stations:
                cache_stations = [{k: v for k, v in s.items() if k not in ("distance_m", "total_chargers", "available_chargers")} for s in api_stations]
                cache_data = {"stations": _serialize_for_cache(cache_stations), "timestamp": now.isoformat()}
                await redis_client.setex(cache_key, settings.CACHE_EXPIRE_SECONDS, json.dumps(_serialize_for_cache(cache_data), ensure_ascii=False))
                try:
                    persistent_ttl = getattr(settings, "PERSISTENT_STATION_CACHE_SECONDS", 86400)
                    await redis_client.setex(persistent_key, persistent_ttl, json.dumps(_serialize_for_cache(cache_data), ensure_ascii=False))
                except Exception:
                    pass
                try:
                    if redis_client:
                        await redis_client.incr("metrics:stations:cache_hits:api")
                except Exception:
                    pass
        except Exception:
            pass

        return {
            "source": "kepco_api",
            "addr": addr,
            "radius_normalized": actual_radius,
            "stations": api_stations
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def calculate_distance_haversine(lat1, lon1, lat2, lon2):
    """하버사인 공식으로 두 지점 간 거리(미터)를 계산합니다."""
    try:
        R = 6371000
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))
    except Exception:
        return 999999


def _dedupe_stations_by_id(stations):
    """station_id 기준으로 중복 충전소를 제거하고, chargers 목록은 병합합니다."""
    by_id = {}
    for s in stations:
        sid = str(s.get("station_id", "")).strip()
        if not sid:
            by_id[f"_noid_{len(by_id)}"] = s
            continue

        if sid not in by_id:
            by_id[sid] = dict(s)
        else:
            existing = by_id[sid]
            for k, v in s.items():
                if k == "chargers":
                    existing_ch = existing.get("chargers") or []
                    seen = {c.get("charger_id") for c in existing_ch}
                    for c in (v or []):
                        if c.get("charger_id") not in seen:
                            existing_ch.append(c)
                            seen.add(c.get("charger_id"))
                    existing["chargers"] = existing_ch
                else:
                    if not existing.get(k) and v:
                        existing[k] = v

    return list(by_id.values())


async def _clear_db_transaction(db: AsyncSession):
    """이전 오류로 세션이 aborted 상태일 경우 rollback으로 복구합니다."""
    try:
        await db.rollback()
    except Exception:
        pass


async def _ensure_station_db_id(db: AsyncSession, cs_id: str, item: dict = None, now: datetime = None):
    """cs_id에 해당하는 station 행이 없으면 INSERT하고 DB primary key를 반환합니다."""
    if not cs_id:
        return None

    try:
        res = await db.execute(text("SELECT id FROM stations WHERE cs_id = :cs_id LIMIT 1"), {"cs_id": cs_id})
        row = res.fetchone()
        if row and row._mapping.get("id"):
            return row._mapping.get("id")
    except Exception:
        try:
            await _clear_db_transaction(db)
        except Exception:
            pass

    try:
        if now is None:
            now = datetime.now(timezone.utc)

        insert_sql = """
            INSERT INTO stations (cs_id, name, address, location, raw_data, last_synced_at)
            VALUES (:cs_id, :name, :address, ST_SetSRID(ST_MakePoint(:longi, :lat), 4326), :raw_data, :update_time)
            ON CONFLICT (cs_id) DO UPDATE SET
                name = COALESCE(EXCLUDED.name, stations.name),
                address = COALESCE(EXCLUDED.address, stations.address),
                location = COALESCE(EXCLUDED.location, stations.location),
                raw_data = COALESCE(EXCLUDED.raw_data, stations.raw_data),
                last_synced_at = COALESCE(EXCLUDED.last_synced_at, stations.last_synced_at)
            RETURNING id
        """

        params = {
            "cs_id": cs_id,
            "name": (item.get("csNm") if item else None) or (item.get("cs_nm") if item else None) or None,
            "address": (item.get("addr") if item else None) or None,
            "lat": float(item.get("lat")) if item and item.get("lat") else None,
            "longi": float(item.get("longi")) if item and item.get("longi") else None,
            "raw_data": json.dumps(item, ensure_ascii=False) if item else None,
            "update_time": now
        }

        await _clear_db_transaction(db)
        r = await db.execute(text(insert_sql), params)
        row = r.fetchone()
        if row and row._mapping.get("id"):
            return row._mapping.get("id")
    except Exception:
        try:
            await _clear_db_transaction(db)
        except Exception:
            pass

    return None


def _serialize_for_cache(obj):
    """datetime 등 JSON 비직렬화 타입을 재귀적으로 직렬화 가능한 값으로 변환합니다."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _serialize_for_cache(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_for_cache(v) for v in obj]
    return obj


def _parse_to_aware_datetime(val) -> Optional[datetime]:
    """다양한 datetime 표현을 UTC-aware datetime으로 정규화합니다.

    Accepts:
    - None -> returns None
    - datetime (naive or aware) -> returns aware datetime in UTC
    - ISO-8601 string (with or without timezone, with trailing Z) -> parsed as UTC when tz absent
    - compact string YYYYMMDDHHMMSS -> parsed as UTC
    - numeric epoch seconds (int/float/str of digits) -> converted to UTC

    Returns None if parsing fails.
    """
    if val is None:
        return None

    # If it's already a datetime
    try:
        if isinstance(val, datetime):
            if val.tzinfo is None:
                return val.replace(tzinfo=timezone.utc)
            return val.astimezone(timezone.utc)
    except Exception:
        pass

    s = str(val).strip()
    if not s:
        return None

    # trailing Z -> convert to +00:00 for fromisoformat
    if s.endswith("Z") and not s.endswith("+00:00"):
        s = s[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(s)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        pass

    # YYYYMMDDHHMMSS 포맷
    try:
        parsed = datetime.strptime(s, "%Y%m%d%H%M%S")
        return parsed.replace(tzinfo=timezone.utc)
    except Exception:
        pass

    # 숫자 epoch 시도
    try:
        if re.fullmatch(r"\d+", s):
            ts = int(s)
            if len(s) >= 13:
                ts = ts / 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        if re.fullmatch(r"\d+\.\d+", s):
            return datetime.fromtimestamp(float(s), tz=timezone.utc)
    except Exception:
        pass

    return None


@app.get("/api/v1/stations-kepco-2025", tags=["Station"], summary="충전소 검색 (구 URL 호환 리다이렉트)")
async def kepco_2025_redirect(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius: int = Query(..., ge=100, le=15000),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    api_key: str = Depends(frontend_api_key_required),
    db: AsyncSession = Depends(get_async_session),
    redis_client: Redis = Depends(get_redis_client)
):
    """/api/v1/stations으로의 하위 호환 리다이렉트."""
    return RedirectResponse(
        url=f"/api/v1/stations?lat={lat}&lon={lon}&radius={radius}&page={page}&limit={limit}",
        status_code=307
    )


app.include_router(api_router, prefix="/api/v1")

admin_router = APIRouter(dependencies=[Depends(admin_required)])


@admin_router.get("/redis/keys", summary="관리자: Redis 키 조회")
async def admin_redis_keys(pattern: str = Query("stations:*", description="SCAN 패턴 (예: stations:*)"),
                           count: int = Query(100, description="SCAN count hint"),
                           redis_client: Redis = Depends(get_redis_client)):
    """관리자 전용: Redis에서 패턴에 맞는 키를 나열합니다. 삭제는 수행하지 않습니다.

    보호: 이 엔드포인트는 `admin_required` 의존성으로 보호됩니다. Render에서 직접 호출하거나
    관리자 자격증명을 사용해 호출하세요.
    """
    if not redis_client:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis client is not available")

    keys = []
    try:
        async for k in redis_client.scan_iter(match=pattern, count=count):
            keys.append(k)
            if len(keys) >= 1000:
                break
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis scan failed: {e}")

    return {"pattern": pattern, "count": len(keys), "keys": keys}


@admin_router.get("/redis/debug", summary="관리자: Redis 디버그 정보")
async def admin_redis_debug(redis_client: Redis = Depends(get_redis_client)):
    if not redis_client:
        return JSONResponse(status_code=503, content={"ok": False, "reason": "redis_unavailable"})
    try:
        ping = await redis_client.ping()
    except Exception as e:
        return JSONResponse(status_code=503, content={"ok": False, "reason": f"ping_failed: {e}"})

    info_summary = {}
    try:
        info = await redis_client.info()
        info_summary = {
            "role": info.get("role"),
            "used_memory_human": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
        }
    except Exception:
        info_summary = {"ok": False, "reason": "info_unavailable"}

    key_count = None
    try:
        cnt = 0
        async for _k in redis_client.scan_iter(match="station_detail:*", count=100):
            cnt += 1
            if cnt >= 1000:
                break
        key_count = cnt
    except Exception:
        key_count = None

    return {
        "ok": True,
        "ping": bool(ping),
        "info": info_summary,
        "station_detail_key_sample_count": key_count
    }


app.include_router(admin_router, prefix="/admin")


@app.get("/db-test", tags=["Infrastructure"], summary="DB 연결 테스트 (subsidies 조회)")
async def db_test_endpoint(manufacturer: str, model_group: str, db: AsyncSession = Depends(get_async_session), _ok: bool = Depends(frontend_api_key_required)):
    start_time = time.time()
    try:
        query_sql = (
            "SELECT model_name, subsidy_national_10k_won, subsidy_local_10k_won, subsidy_total_10k_won, sale_price "
            "FROM subsidies "
            "WHERE manufacturer = :manufacturer AND model_group = :model_group LIMIT 50"
        )
        ensure_read_only_sql(query_sql)
        result = await db.execute(text(query_sql), {"manufacturer": manufacturer, "model_group": model_group})
        rows = result.fetchall()

        response_time_ms = (time.time() - start_time) * 1000
        mapped_rows = []
        for row in rows:
            m = row._mapping
            mapped_rows.append({
                "모델명": m.get("model_name"),
                "국비(만원)": m.get("subsidy_national_10k_won"),
                "지방비(만원)": m.get("subsidy_local_10k_won"),
                "보조금(만원)": m.get("subsidy_total_10k_won"),
                "salePrice": int(m.get("sale_price")) if m.get("sale_price") is not None else None,
            })

        return {
            "message": "Database query executed",
            "status": "ok",
            "manufacturer": manufacturer,
            "model_group": model_group,
            "count": len(mapped_rows),
            "rows": mapped_rows,
            "response_time_ms": f"{response_time_ms:.2f}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database query failed: {e.__class__.__name__}: {e}"
        )


@app.get("/redis-test", tags=["Infrastructure"], summary="Redis 연결 테스트")
async def redis_test_endpoint(redis_client: Redis = Depends(get_redis_client)):
    if not redis_client:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis client is not initialized or connected.")
    test_key = "infra:test:key"
    test_data = {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
    try:
        await set_cache(test_key, test_data, expire=10)
        retrieved_data = await get_cache(test_key)
        if retrieved_data and retrieved_data["status"] == "ok":
            return {"message": "Redis connection test successful!", "data_stored": test_data, "data_retrieved": retrieved_data, "status": "ok"}
        else:
            raise Exception("Data mismatch or retrieval failed.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Redis operation FAILED!: {e.__class__.__name__}: {e}")


@app.get("/api/v1/station/{station_id}/chargers", tags=["Station"], summary="충전기 스펙 조회")
async def get_station_charger_specs(
    station_id: str = Path(..., description="충전소ID"),
    addr: str = Query(..., description="충전기주소"),
    api_key: str = Depends(frontend_api_key_required),
    db: AsyncSession = Depends(get_async_session),
    redis_client: Redis = Depends(get_redis_client)
):
    """DB 조회 → KEPCO API 호출 순으로 충전기 스펙과 상태를 반환합니다. 30분 이내 데이터는 DB를 재사용합니다."""
    try:
        primary_station_query = """
         SELECT id as station_db_id, cs_id, COALESCE(name, '') AS cs_nm, COALESCE(address, '') AS addr,
             ST_Y(location)::text AS lat, ST_X(location)::text AS longi,
             COALESCE(static_data_updated_at, updated_at) AS last_updated,
             (SELECT MAX(stat_update_datetime) FROM chargers WHERE cs_id = stations.cs_id) AS last_charger_update
         FROM stations
         WHERE cs_id = :station_id
         LIMIT 1
     """

        fallback_station_query = """
         SELECT id as station_db_id, cs_id, COALESCE(name, '') AS cs_nm, COALESCE(address, '') AS addr,
             ST_Y(location)::text AS lat, ST_X(location)::text AS longi,
             updated_at AS last_updated,
             (SELECT MAX(stat_update_datetime) FROM chargers WHERE cs_id = stations.cs_id) AS last_charger_update
         FROM stations
         WHERE cs_id = :station_id
         LIMIT 1
     """

        station_row = None
        try:
            try:
                station_result = await db.execute(text(primary_station_query), {"station_id": station_id})
                station_row = station_result.fetchone()
            except ProgrammingError:
                try:
                    await _clear_db_transaction(db)
                except Exception:
                    pass
                try:
                    station_result = await db.execute(text(fallback_station_query), {"station_id": station_id})
                    station_row = station_result.fetchone()
                except Exception:
                    try:
                        await _clear_db_transaction(db)
                    except Exception:
                        pass
                    station_row = None
            except Exception:
                try:
                    await _clear_db_transaction(db)
                except Exception:
                    pass
                station_row = None
        finally:
            try:
                await _clear_db_transaction(db)
            except Exception:
                pass

        if not station_row:
            station_info = None
        else:
            station_dict = station_row._mapping

            def _dt_to_iso(val):
                return val.isoformat() if isinstance(val, datetime) else val

            station_info = {
                "station_db_id": station_dict.get("station_db_id"),
                "station_id": str(station_dict["cs_id"]),
                "station_name": str(station_dict["cs_nm"]),
                "addr": str(station_dict["addr"]),
                "lat": str(station_dict["lat"]),
                "lon": str(station_dict["longi"]),
                "last_updated": _dt_to_iso(station_dict.get("last_updated")),
                "last_charger_update": station_dict.get("last_charger_update")
            }

        try:
            cache_key = f"station_detail:{station_id}"
            cached_blob = None
            if redis_client:
                cached_raw = await redis_client.get(cache_key)
                if cached_raw:
                    try:
                        cached_blob = json.loads(cached_raw)
                    except Exception:
                        cached_blob = None

                if cached_blob and isinstance(cached_blob, dict) and cached_blob.get("timestamp"):
                    cached_ts = _parse_to_aware_datetime(cached_blob.get("timestamp"))
                    if cached_ts is not None:
                        age_min = (datetime.now(timezone.utc) - cached_ts).total_seconds() / 60
                        detail_ttl_min = getattr(settings, "CACHE_DETAIL_EXPIRE_SECONDS", 300) / 60
                        if age_min <= detail_ttl_min:
                            cached_station_info = cached_blob.get("station_info") or {}
                            cached_chargers = cached_blob.get("chargers") or []
                            cached_available = cached_blob.get("available_charge_types") or []
                            return JSONResponse(status_code=200, content={
                                "station_name": cached_station_info.get("station_name") or cached_station_info.get("cs_nm") or "",
                                "available_charge_types": ", ".join(cached_available),
                                "charger_details": cached_chargers,
                                "total_chargers": len(cached_chargers),
                                "source": "cache",
                                "timestamp": cached_blob.get("timestamp")
                            })
        except Exception:
            pass

        need_api_call = True
        cached_chargers = []

        if station_info:
            now = datetime.now(timezone.utc)
            last_charger_update_dt = _parse_to_aware_datetime(station_info.get("last_charger_update"))

            if last_charger_update_dt:
                try:
                    time_diff = (now - last_charger_update_dt).total_seconds() / 60
                except Exception:
                    time_diff = None

                if time_diff is not None and time_diff <= 30:
                    need_api_call = False

            if not need_api_call:
                charger_query = """
                    SELECT station_id, cp_id, cp_nm, cp_stat, charge_tp, cs_id, stat_update_datetime, kepco_stat_update_datetime
                    FROM chargers 
                    WHERE cs_id = :station_id
                    ORDER BY cp_id
                """

                charger_result = await db.execute(text(charger_query), {"station_id": station_id})
                charger_rows = charger_result.fetchall()

                for row in charger_rows:
                    row_dict = row._mapping
                    sdt = row_dict.get("stat_update_datetime")
                    kepco_ts = row_dict.get("kepco_stat_update_datetime")
                    cached_chargers.append({
                        "charger_id": str(row_dict["cp_id"]),
                        "charger_name": str(row_dict["cp_nm"]),
                        "status_code": str(row_dict.get("cp_stat") or ""),
                        "charge_type": str(row_dict.get("charge_tp") or ""),
                        "stat_update_datetime": sdt.isoformat() if isinstance(sdt, datetime) else sdt,
                        "kepco_stat_update_datetime": kepco_ts.isoformat() if isinstance(kepco_ts, datetime) else kepco_ts,
                        "station_db_id": row_dict.get("station_id")
                    })

        if need_api_call:
            kepco_url = settings.EXTERNAL_STATION_API_BASE_URL
            kepco_key = settings.EXTERNAL_STATION_API_KEY

            if not kepco_url or not kepco_key:
                raise HTTPException(status_code=500, detail="KEPCO API 설정 누락")

            async with httpx.AsyncClient() as client:
                kepco_response = await client.get(
                    kepco_url,
                    params={
                        "addr": addr,
                        "apiKey": kepco_key,
                        "returnType": "json"
                    },
                    timeout=30.0
                )

                if kepco_response.status_code != 200:
                    if not cached_chargers:
                        raise HTTPException(
                            status_code=502,
                            detail=f"KEPCO API 오류: HTTP {kepco_response.status_code}"
                        )
                else:
                    kepco_data = kepco_response.json()

                    if isinstance(kepco_data, dict) and "data" in kepco_data:
                        raw_data = kepco_data["data"]
                        updated_chargers = []
                        now = datetime.now(timezone.utc)

                        if isinstance(raw_data, list):
                            for item in raw_data:
                                try:
                                    if str(item.get("csId", "")) == station_id:
                                        if not station_info:
                                            station_info = {
                                                "station_id": str(item.get("csId", "")),
                                                "station_name": str(item.get("csNm", "")),
                                                "addr": str(item.get("addr", "")),
                                                "lat": str(item.get("lat", "")),
                                                "lon": str(item.get("longi", ""))
                                            }

                                        updated_chargers.append({
                                            "charger_id": str(item.get("cpId", "")),
                                            "charger_name": str(item.get("cpNm", "")),
                                            "status_code": str(item.get("cpStat", "")),
                                            "charge_type": str(item.get("chargeTp", ""))
                                        })

                                        try:
                                            station_db_id = station_info.get("station_db_id") if station_info else None
                                            if not station_db_id:
                                                station_db_id = await _ensure_station_db_id(db, str(item.get("csId")), item=item, now=now)

                                                provider_ts = None
                                            for k in ("kepco_stat_update_datetime", "stat_update_datetime", "statUpdateDatetime", "statUpdate", "statUpdDt", "update_time", "update_dt", "lastUpdate", "stat_date", "stat_time", "cpStatTime"):
                                                if k in item and item.get(k):
                                                    raw_ts = item.get(k)
                                                    ts_dt = _parse_to_aware_datetime(raw_ts)
                                                    provider_ts = ts_dt.isoformat() if ts_dt else str(raw_ts)
                                                    break

                                            charger_insert_sql = """
                                                INSERT INTO chargers (station_id, cp_id, cp_nm, cp_stat, charge_tp, cs_id, stat_update_datetime, kepco_stat_update_datetime)
                                                VALUES (:station_id, :cp_id, :cp_nm, :cp_stat, :charge_tp, :cs_id, :update_time, :kepco_ts)
                                                ON CONFLICT (cp_id) DO UPDATE SET
                                                    station_id = COALESCE(EXCLUDED.station_id, chargers.station_id),
                                                    cp_nm = EXCLUDED.cp_nm,
                                                    cp_stat = EXCLUDED.cp_stat,
                                                    charge_tp = EXCLUDED.charge_tp,
                                                    stat_update_datetime = EXCLUDED.stat_update_datetime,
                                                    kepco_stat_update_datetime = EXCLUDED.kepco_stat_update_datetime
                                            """

                                            if station_db_id is not None:
                                                try:
                                                    await _clear_db_transaction(db)
                                                    await db.execute(text(charger_insert_sql), {
                                                        "station_id": station_db_id,
                                                        "cp_id": item.get("cpId"),
                                                        "cp_nm": item.get("cpNm"),
                                                        "cp_stat": item.get("cpStat"),
                                                        "charge_tp": item.get("chargeTp"),
                                                        "cs_id": item.get("csId"),
                                                        "update_time": now,
                                                        "kepco_ts": provider_ts
                                                    })
                                                except Exception:
                                                    try:
                                                        await db.rollback()
                                                    except Exception:
                                                        pass
                                            else:
                                                try:
                                                    await _clear_db_transaction(db)
                                                    station_insert_sql = """
                                                        INSERT INTO stations (cs_id, name, address, location, raw_data, last_synced_at)
                                                        VALUES (:cs_id, :name, :address, ST_SetSRID(ST_MakePoint(:longi, :lat), 4326), :raw_data, :update_time)
                                                        ON CONFLICT (cs_id) DO UPDATE SET
                                                            name = EXCLUDED.name,
                                                            address = EXCLUDED.address,
                                                            location = EXCLUDED.location,
                                                            raw_data = EXCLUDED.raw_data,
                                                            last_synced_at = EXCLUDED.last_synced_at
                                                        RETURNING id
                                                    """
                                                    result = await db.execute(text(station_insert_sql), {
                                                        "cs_id": item.get("csId"),
                                                        "name": item.get("csNm"),
                                                        "address": item.get("addr"),
                                                        "lat": float(item.get("lat", 0)),
                                                        "longi": float(item.get("longi", 0)),
                                                        "raw_data": json.dumps(item, ensure_ascii=False),
                                                        "update_time": now
                                                    })
                                                    station_row = result.fetchone()
                                                    if station_row:
                                                        station_db_id = station_row._mapping.get("id")
                                                        try:
                                                            await db.execute(text(charger_insert_sql), {
                                                                "station_id": station_db_id,
                                                                "cp_id": item.get("cpId"),
                                                                "cp_nm": item.get("cpNm"),
                                                                "cp_stat": item.get("cpStat"),
                                                                "charge_tp": item.get("chargeTp"),
                                                                "cs_id": item.get("csId"),
                                                                "update_time": now,
                                                                "kepco_ts": provider_ts
                                                            })
                                                        except Exception:
                                                            try:
                                                                await db.rollback()
                                                            except Exception:
                                                                pass
                                                except Exception:
                                                    try:
                                                        await _clear_db_transaction(db)
                                                    except Exception:
                                                        pass
                                        except Exception:
                                            try:
                                                await db.rollback()
                                            except Exception:
                                                pass
                                except Exception:
                                    continue

                        await db.commit()
                        cached_chargers = updated_chargers

        if not station_info:
            raise HTTPException(status_code=404, detail="충전소 정보를 찾을 수 없습니다.")

        available_charge_types = list({charger["charge_type"] for charger in cached_chargers if charger["charge_type"]})

        charger_details = []
        for charger in cached_chargers:
            status_code = charger["status_code"]
            status_text = {
                "0": "사용가능",
                "1": "충전가능",
                "2": "충전중", 
                "3": "고장/점검",
                "4": "통신장애",
                "5": "통신미연결",
                "6": "예약중",
                "7": "운영중지",
                "8": "정비중",
                "9": "일시정지"
            }.get(status_code, f"알 수 없음({status_code})")
            
            charger_details.append({
                "charger_id": charger["charger_id"],
                "charger_name": charger["charger_name"],
                "status_code": status_code,
                "status_text": status_text,
                "charge_type": charger["charge_type"],
                "charge_type_description": {
                    "1": "완속 (AC 3상)",
                    "2": "급속 (DC차데모)",
                    "3": "급속 (DC콤보)",
                    "4": "완속 (AC단상)",
                    "5": "급속 (DC차데모+DC콤보)",
                    "6": "급속 (DC차데모+AC3상)",
                    "7": "급속 (DC콤보+AC3상)"
                }.get(charger["charge_type"], f"타입{charger['charge_type']}"),
                "last_updated": charger.get("stat_update_datetime", "정보없음"),
                "availability": "사용가능" if status_code == "1" else "사용불가"
            })

        try:
            cache_key = f"station_detail:{station_id}"
            cache_data = {
                "station_info": _serialize_for_cache(station_info),
                "chargers": _serialize_for_cache(charger_details),
                "available_charge_types": available_charge_types,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await redis_client.setex(cache_key, settings.CACHE_DETAIL_EXPIRE_SECONDS, json.dumps(_serialize_for_cache(cache_data), ensure_ascii=False))
        except Exception:
            pass

        return {
            "station_name": station_info["station_name"],
            "available_charge_types": ", ".join(available_charge_types),
            "charger_details": charger_details,
            "total_chargers": len(charger_details),
            "source": "api" if need_api_call else "database",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
