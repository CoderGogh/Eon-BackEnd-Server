from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "EV Charger Management API"
    API_VERSION: str = "1.0.0"

    DATABASE_URL: str

    SECRET_KEY: str = "YOUR_SUPER_SECRET_KEY_REPLACE_ME_NOW"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: Optional[str] = None
    # 충전소 검색 결과 단기 캐시 TTL (초)
    CACHE_EXPIRE_SECONDS: int = 300
    # 충전소 위치 정적 데이터 장기 캐시 TTL (초)
    PERSISTENT_STATION_CACHE_SECONDS: int = 86400
    # 충전소 상세(충전기 상태) 캐시 TTL (초)
    CACHE_DETAIL_EXPIRE_SECONDS: int = 300
    # 캐시 키 좌표 반올림 자릿수
    CACHE_COORD_ROUND_DECIMALS: int = 8

    @property
    def KEPCO_API_KEY(self) -> Optional[str]:
        return self.EXTERNAL_STATION_API_KEY

    EXTERNAL_STATION_API_BASE_URL: Optional[str] = None
    EXTERNAL_STATION_API_KEY: Optional[str] = None
    EXTERNAL_STATION_API_AUTH_TYPE: str = "header"
    EXTERNAL_STATION_API_KEY_HEADER_NAME: str = "Authorization"
    EXTERNAL_STATION_API_KEY_PARAM_NAME: str = "apiKey"
    EXTERNAL_STATION_API_RETURN_TYPE: str = "json"
    EXTERNAL_STATION_API_TIMEOUT_SEED_SECONDS: int = 30
    EXTERNAL_STATION_API_TIMEOUT_SECONDS: int = 10

    ENVIRONMENT: str = "production"  # development / docker / production
    DOCKER_ENV: Optional[bool] = False

    @field_validator("DOCKER_ENV", mode="before")
    def parse_docker_env(cls, v):
        if isinstance(v, str):
            return v.lower() in ("1", "true", "yes")
        return v

    @model_validator(mode="after")
    def switch_redis_host(self):
        """Docker 환경에서 Redis 호스트를 내부 서비스 이름으로 전환합니다."""
        if (self.ENVIRONMENT or "").lower() == "docker":
            self.REDIS_HOST = self.REDIS_HOST or "ev_charger_redis"
            self.REDIS_PORT = self.REDIS_PORT or 6379
        return self


settings = Settings()
