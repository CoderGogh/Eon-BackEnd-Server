# Codyssey EV Charger Backend

FastAPI 기반 전기차 충전소 정보 및 보조금 조회 백엔드 서비스입니다.
성남시 주최 프로젝트로, 시민들의 전기차 충전 인프라 접근성을 높이기 위해 개발되었습니다.

---

## Tech Stack

| 분류 | 기술 |
|------|------|
| Framework | FastAPI (Python 3.12) |
| Database | PostgreSQL + PostGIS (공간 데이터) |
| ORM | SQLAlchemy 2.0 (async) + asyncpg |
| Cache | Redis (redis-py 6.x async) |
| Migration | Alembic |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| HTTP Client | httpx (async) |
| Dependency | Poetry |
| Deployment | Render.com (Docker) |

---

## 프로젝트 구조

```
Backend_Server/
├── app/
│   ├── main.py                    # FastAPI 앱 진입점, 핵심 엔드포인트 정의
│   ├── auth.py                    # JWT 생성/검증, bcrypt 비밀번호 처리
│   ├── models.py                  # SQLAlchemy ORM 모델 (5개 테이블)
│   ├── redis_client.py            # Redis 연결 풀 및 캐시 헬퍼
│   ├── mock_api.py                # 개발용 목 데이터 (초기 시드 전용)
│   ├── schemas.py                 # 레거시 Pydantic 스키마 (구버전 호환)
│   │
│   ├── core/
│   │   └── config.py              # 메인 설정 (Pydantic Settings, 환경변수 로드)
│   │
│   ├── api/
│   │   ├── deps.py                # X-API-Key 인증 의존성
│   │   └── v1/
│   │       ├── api.py             # v1 라우터 집계 (현재 auth만 포함)
│   │       ├── auth.py            # POST /api/v1/auth/token (JWT 발급)
│   │       ├── subsidy_router.py  # GET /subsidies/search (미사용, 비활성화됨)
│   │       ├── station_router_legacy.py  # 미사용 (station_service 의존)
│   │       └── station_router_simple.py  # 미사용 스텁
│   │
│   ├── db/
│   │   ├── database.py            # 비동기 엔진 및 세션팩토리
│   │   ├── init_db.py             # 초기 테이블 생성 + 목 데이터 시드 스크립트
│   │   └── repository/
│   │       └── user.py            # 사용자 DB 조회/생성 함수
│   │
│   ├── repository/
│   │   └── station_repository.py  # StationRepository, ChargerRepository (미사용)
│   │
│   ├── schemas/
│   │   ├── station.py             # StationSummary, StationDetail, ChargerDetail 등
│   │   ├── subsidy.py             # SubsidyRequest, SubsidyPublic, SubsidyListResponse
│   │   └── user.py                # UserRole, UserCreate, Token, TokenData 등
│   │
│   └── services/
│       ├── geocoding_service.py   # Nominatim 역지오코딩, 하버사인 거리 계산
│       └── subsidy_service.py     # SubsidyService (SQLAlchemy 기반 보조금 조회)
│
├── alembic/                       # DB 마이그레이션 히스토리
├── scripts/                       # 운영/유지보수 스크립트 모음
├── Dockerfile                     # Python 3.12-slim 기반 컨테이너 빌드
├── docker-compose.yml             # 로컬 개발용 (FastAPI + PostgreSQL + Redis)
├── render.yaml                    # Render 배포 설정 템플릿
├── pyproject.toml                 # Poetry 의존성 정의
├── alembic.ini                    # Alembic 설정
└── .env.template                  # 환경변수 템플릿
```

---

## 데이터베이스 스키마

### `users`
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| username | String(50) UNIQUE | |
| hashed_password | String(255) | bcrypt 해시 |
| role | String(20) | `user` / `admin` / `manager` |
| created_at / updated_at | DateTime | |

### `stations`
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| station_code | String(50) UNIQUE | 내부 충전소 코드 |
| cs_id | String(50) UNIQUE | KEPCO 충전소 ID |
| name / cs_nm | String | 충전소 이름 |
| address / addr | Text | 주소 |
| lat / longi | String(20) | 위도/경도 (문자열) |
| location | Geometry(POINT, 4326) | PostGIS 공간 인덱스 |
| provider | String(100) | 데이터 제공사 |
| raw_data | JSON | 외부 API 원본 응답 |
| last_synced_at | DateTime | 마지막 KEPCO API 동기화 시각 |
| static_data_updated_at | DateTime | 정적 데이터 갱신 시각 |
| dynamic_data_updated_at | DateTime | 동적 데이터 갱신 시각 |

### `chargers`
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| station_id | FK → stations.id | |
| cp_id | String(50) UNIQUE | KEPCO 충전기 ID |
| cp_nm | String(200) | 충전기 이름 |
| cp_stat | String(10) | 상태 코드 (1=충전가능, 2=충전중 등) |
| charge_tp | String(10) | 충전 방식 (1=완속, 2=급속) |
| cs_id | String(50) | 소속 충전소 KEPCO ID |
| stat_update_datetime | DateTime | 상태 갱신 시각 |
| kepco_stat_update_datetime | DateTime(timezone) | KEPCO 제공 타임스탬프 |

### `subsidies`
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| manufacturer | String | 제조사 (예: 현대자동차) |
| model_group | String | 모델 그룹 (예: GV60) |
| model_name | String UNIQUE | 세부 모델명 |
| subsidy_national_10k_won | Integer | 국고 보조금 (만 원) |
| subsidy_local_10k_won | Integer | 지자체 보조금 (만 원) |
| subsidy_total_10k_won | Integer | 합계 보조금 (만 원) |
| sale_price | Integer (nullable) | 판매가 (원) |

### `api_logs`
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | |
| endpoint / method / api_type | String | |
| status_code / response_code | Integer | |
| response_msg | String | |

---

## 인증 체계

세 가지 인증 레이어가 독립적으로 운용됩니다.

### 1. X-API-Key (프론트엔드 ↔ 백엔드)
- 헤더: `x-api-key`
- 환경변수 `FRONTEND_API_KEYS`에 콤마로 복수 키 등록 가능
- 충전소 검색, 보조금 조회, 충전기 상세 등 모든 주요 엔드포인트에 적용
- 키 미설정 시 403 반환

### 2. JWT Bearer Token (사용자 인증)
```
POST /api/v1/auth/token
  form: username, password
  → { access_token, token_type: "bearer" }
```
- bcrypt로 DB에 저장된 비밀번호와 비교 후 JWT 발급
- Payload: `{ sub_username, role, exp }`
- 알고리즘: HS256, 만료: `ACCESS_TOKEN_EXPIRE_MINUTES` (기본 60분)

### 3. HTTP Basic Auth (관리자 전용)
- `ADMIN_CREDENTIALS` 환경변수: `user1:pass1,user2:pass2` 형식
- `/admin/*` 엔드포인트 및 Swagger/ReDoc(`ADMIN_MODE=true` 시) 보호

---

## API 엔드포인트

### 인프라

| 메서드 | 경로 | 인증 | 설명 |
|--------|------|------|------|
| GET/HEAD | `/` | 없음 | 서버 상태 확인 (UptimeRobot ping용) |
| GET/HEAD | `/health` | 없음 | DB + Redis 연결 상태 반환 |
| GET | `/db-test` | X-API-Key | subsidies 쿼리로 DB 연결 테스트 |
| GET | `/redis-test` | X-API-Key | set/get으로 Redis 연결 테스트 |

### 보조금

| 메서드 | 경로 | 인증 | 설명 |
|--------|------|------|------|
| GET | `/subsidy` | X-API-Key | 보조금 조회 (`manufacturer`, `model_group`) |
| GET | `/subsidy/by` | X-API-Key | 동일 기능, camelCase `modelGroup` 파라미터 허용 |

응답 예시:
```json
[
  {
    "model_name": "GV60 스탠다드 2WD",
    "subsidy_national": 287,
    "subsidy_local": 148,
    "subsidy_total": 435,
    "salePrice": 55000000
  }
]
```

### 충전소 검색

| 메서드 | 경로 | 인증 | 설명 |
|--------|------|------|------|
| GET | `/api/v1/stations` | X-API-Key | 좌표 + 반경으로 주변 충전소 검색 |
| GET | `/api/v1/stations-kepco-2025` | X-API-Key | 구 URL 호환 → 307 리다이렉트 |
| GET | `/api/v1/station/{station_id}/chargers` | X-API-Key | 충전소별 충전기 스펙 및 상태 조회 |

### 인증

| 메서드 | 경로 | 인증 | 설명 |
|--------|------|------|------|
| POST | `/api/v1/auth/token` | 없음 | username/password → JWT 발급 |

### 관리자

| 메서드 | 경로 | 인증 | 설명 |
|--------|------|------|------|
| GET | `/admin/redis/keys` | HTTP Basic | Redis 키 SCAN (패턴 지정 가능) |
| GET | `/admin/redis/debug` | HTTP Basic | Redis 연결 상태 및 키 수 확인 |
| GET | `/docs` | HTTP Basic | Swagger UI (`ADMIN_MODE=true` 시) |
| GET | `/redoc` | HTTP Basic | ReDoc (`ADMIN_MODE=true` 시) |

---

## 기능 시퀀스

### 충전소 검색 `GET /api/v1/stations`

```
클라이언트
  │
  ├─ 파라미터: lat(str), lon(str), radius(int), page, limit
  │
  ▼
[1] 파라미터 파싱 & 반경 정규화
    lat/lon → float 변환
    radius → 캐노니컬 버킷으로 올림 (5000 / 10000 / 15000 m)

  ▼
[2] Nominatim 역지오코딩 (httpx)
    좌표 → 시/구/동 수준 주소 (addr)
    실패 시 addr = "서울특별시" 로 폴백

  ▼
[3] 캐시 키 생성
    lat/lon을 소수점 CACHE_COORD_ROUND_DECIMALS 자리로 반올림
    short_key  = "stations:lat{X}:lon{Y}:r{R}:p{P}:l{L}"
    persist_key = "stations_persistent:lat{X}:lon{Y}:r{R}:p{P}:l{L}"

  ▼
[4] 단기 캐시 확인 (Redis, TTL 5분)
    HIT  → 실제 radius로 재필터링
           charger 수 DB 단건 조회 (cs_id 기준)
           distance_m 기준 정렬 후 반환 (source: "cache")

  ▼ (MISS)
[5] 장기 정적 캐시 확인 (Redis, TTL 24시간)
    HIT  → station_id 배열로 charger 수 배치 조회 (ANY 쿼리)
           실제 radius 재필터링 후 반환 (source: "persistent_cache")

  ▼ (MISS)
[6] PostgreSQL PostGIS 공간 쿼리
    ST_DWithin(location, center, radius_m)
    서브쿼리로 total_chargers / available_chargers 포함
    실패 시 → address LIKE '%addr%' 폴백 쿼리

    HIT  → 단기 캐시 + 장기 캐시에 동시 저장
           source: "database" 로 반환

  ▼ (DB 실패 또는 결과 없음)
[7] KEPCO 외부 API 호출 (httpx)
    addr + apiKey 파라미터로 GET 요청
    응답 파싱 → 반경 필터 → stations INSERT/UPSERT (ON CONFLICT)
    charger 데이터도 동시 upsert
    단기 + 장기 캐시 저장
    source: "kepco_api" 로 반환
```

---

### 충전기 상세 조회 `GET /api/v1/station/{station_id}/chargers`

```
클라이언트 (station_id, addr 파라미터)
  │
  ▼
[1] stations 테이블 조회
    primary: static_data_updated_at 포함 쿼리
    실패(ProgrammingError) 시 fallback: updated_at 쿼리

  ▼
[2] Redis 상세 캐시 확인
    키: "station_detail:{station_id}"
    TTL 기준(CACHE_DETAIL_EXPIRE_SECONDS, 기본 300초) 이내이면 즉시 반환
    (source: "cache")

  ▼ (캐시 미스)
[3] 30분 룰 판정
    DB chargers의 stat_update_datetime 확인
    30분 이내 → DB에서 충전기 데이터 직접 조회 (need_api_call = False)

  ▼ (30분 초과 또는 DB에 데이터 없음)
[4] KEPCO 외부 API 호출
    csId 일치 항목 파싱
    station_info 보완 (DB에 없을 경우)
    충전기 데이터 upsert:
      station 없으면 INSERT RETURNING id
      charger ON CONFLICT(cp_id) DO UPDATE

  ▼
[5] 상태 코드 → 텍스트 변환
    "0"→사용가능, "1"→충전가능, "2"→충전중,
    "3"→고장/점검, "4"→통신장애, "5"→통신미연결,
    "6"→예약중, "7"→운영중지, "8"→정비중, "9"→일시정지

    충전 방식 변환:
    "1"→완속(AC3상), "2"→급속(DC차데모), "3"→급속(DC콤보) 등

  ▼
[6] Redis 상세 캐시 저장
    "station_detail:{station_id}" → TTL: CACHE_DETAIL_EXPIRE_SECONDS

  ▼
최종 응답: station_name, available_charge_types, charger_details[], total_chargers, source, timestamp
```

---

### 보조금 조회 `GET /subsidy`

```
클라이언트 (manufacturer, model_group)
  │
  ▼
[1] ensure_read_only_sql() 방어 가드 (SELECT만 허용)

  ▼
[2] subsidies 테이블 직접 쿼리
    WHERE manufacturer = :manufacturer
      AND model_group ILIKE :model_group (접두어 일치)
    LIMIT 100, ORDER BY model_name

  ▼
응답: [{ model_name, subsidy_national, subsidy_local, subsidy_total, salePrice }]
```

---

## 캐싱 전략

| 계층 | 키 패턴 | TTL | 용도 |
|------|---------|-----|------|
| 단기 | `stations:lat{X}:lon{Y}:r{R}:p{P}:l{L}` | 5분 | 반복 요청 응답 최적화 |
| 장기 | `stations_persistent:lat{X}:lon{Y}:r{R}:p{P}:l{L}` | 24시간 | 위치 정적 데이터 보존 |
| 상세 | `station_detail:{cs_id}` | 5분 (설정 가능) | 충전기 상태 캐시 |
| 메트릭 | `metrics:stations:cache_hits:{short\|persistent\|db\|api}` | 영구 | 캐시 히트율 모니터링 |

- 좌표는 `CACHE_COORD_ROUND_DECIMALS`(기본 8자리)로 반올림하여 키 생산
- 장기 캐시는 위치/이름 등 정적 필드만 저장 (charger 상태는 제외)
- 장기 캐시 히트 시 charger 수는 DB에서 배치 조회하여 실시간 보완

---

## 환경변수

`.env.template` 참고. 필수 항목:

```env
# 데이터베이스
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Redis
REDIS_HOST=
REDIS_PORT=6379
REDIS_PASSWORD=

# 프론트엔드 API 키 (콤마 구분 복수 등록 가능)
FRONTEND_API_KEYS=key1,key2

# KEPCO 외부 충전소 API
EXTERNAL_STATION_API_BASE_URL=
EXTERNAL_STATION_API_KEY=
EXTERNAL_STATION_API_AUTH_TYPE=header
EXTERNAL_STATION_API_KEY_HEADER_NAME=Authorization
EXTERNAL_STATION_API_TIMEOUT_SECONDS=15

# JWT 보안
SECRET_KEY=

# CORS (콤마 구분)
ALLOWED_ORIGINS=https://yourdomain.com

# 배포 환경
ENVIRONMENT=production
DOCKER_ENV=true

# 관리자 (선택)
ADMIN_CREDENTIALS=admin:password
ADMIN_MODE=false
```

캐시 TTL 조정 (선택):
```env
CACHE_EXPIRE_SECONDS=300           # 단기 캐시 TTL (초)
PERSISTENT_STATION_CACHE_SECONDS=86400  # 장기 캐시 TTL (초)
CACHE_DETAIL_EXPIRE_SECONDS=300    # 충전기 상세 캐시 TTL (초)
CACHE_COORD_ROUND_DECIMALS=8       # 캐시 키 좌표 반올림 자릿수
```

---

## 로컬 개발 환경 설정

### 사전 조건
- Python 3.12+
- Poetry
- Docker (PostgreSQL + Redis 실행용)

### 1. 의존성 설치
```bash
poetry install
```

### 2. 인프라 실행 (Docker)
```bash
docker-compose up -d
```
`docker-compose.yml`이 PostgreSQL(PostGIS 포함) + Redis를 로컬에서 띄웁니다.

### 3. 환경변수 설정
```bash
cp .env.template .env
# .env 파일에 값 입력
```

### 4. DB 마이그레이션
```bash
poetry run alembic upgrade head
```

### 5. 서버 실행
```bash
poetry run uvicorn app.main:app --reload
```

---

## 배포 (Render.com)

- `render.yaml` 기반 Docker 빌드 배포
- 프로덕션 서버: `gunicorn -k uvicorn.workers.UvicornWorker app.main:app`
- 모든 환경변수는 Render Dashboard의 Environment Variables(Secrets)에서 관리
- `ADMIN_MODE=true` 설정 시 HTTP Basic Auth로 보호된 `/docs`, `/redoc` 활성화
- `ALLOWED_ORIGINS`로 CORS 허용 도메인 제한 (미설정 시 CORS 미들웨어 비활성)

---

## 운영 스크립트 (`scripts/`)

| 스크립트 | 용도 |
|----------|------|
| `backfill_kepco.py` | KEPCO API 전체 데이터 DB 백필 |
| `sync_incremental.py` | 증분 동기화 |
| `seed_stations.py` | 초기 충전소 데이터 시드 |
| `clear_redis_cache.py` | Redis 캐시 전체 삭제 |
| `check_db.py` | DB 스키마 및 데이터 확인 |
| `run_migrations.sh` | Alembic 마이그레이션 실행 |
| `test_persistent_cache_sim.py` | 장기 캐시 시뮬레이션 테스트 |
| `subsidies_inserts.sql` | 보조금 데이터 SQL 삽입 |
