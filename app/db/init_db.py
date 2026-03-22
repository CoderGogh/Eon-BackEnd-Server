import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from geoalchemy2.functions import ST_GeomFromText
from sqlalchemy.orm import sessionmaker
import asyncpg

from app.models import Base, Station, Charger
from app.mock_api import MOCK_STATIONS_DATA

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_engine_and_session():
    """Settings를 런타임에 불러와 비동기 엔진과 세션팩토리를 반환합니다."""
    from app.core.config import settings

    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    AsyncSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return engine, AsyncSessionLocal


async def init_db():
    """데이터베이스 테이블 생성 및 초기 데이터 삽입"""
    logger.info("Starting database initialization...")

    engine, AsyncSessionLocal = get_engine_and_session()

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully.")

    async with AsyncSessionLocal() as session:
        try:
            for mock_station in MOCK_STATIONS_DATA:
                station_code = mock_station["station_code"]

                existing_station = await session.execute(
                    select(Station).where(Station.station_code == station_code)
                )
                if existing_station.scalar_one_or_none():
                    logger.info(f"Station {station_code} already exists. Skipping.")
                    continue

                wkt_point = f"POINT({mock_station['longitude']} {mock_station['latitude']})"

                new_station = Station(
                    station_code=station_code,
                    name=mock_station["name"],
                    address=mock_station["address"],
                    provider=mock_station["provider"],
                    location=ST_GeomFromText(wkt_point, 4326),
                )
                session.add(new_station)
                await session.flush()

                new_charger = Charger(
                    station_id=new_station.id,
                    charger_code="1",
                    charger_type="DC Combo",
                    connector_type="Type 1",
                    output_kw=50.0,
                    status_code=1
                )
                session.add(new_charger)

            await session.commit()
            logger.info(f"Successfully inserted {len(MOCK_STATIONS_DATA)} stations and initial chargers.")

        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to initialize database: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(init_db())
