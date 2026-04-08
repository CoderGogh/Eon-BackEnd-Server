# 🚀 EON: EV Charging Platform Backend

> **전기차 사용자를 위한 실시간 충전소 정보 및 보조금 데이터 제공 API**
>
> 이 서비스는 고성능 공간 데이터 처리와 효율적인 외부 API 통합을 통해 사용자에게 가장 빠른 경로의 충전 인프라 정보를 제공합니다.
> 성남시 주최 프로젝트의 일환으로 개발되었으며, **실시간 데이터 정합성**과 **시스템 확장성**을 핵심 가치로 설계되었습니다.

---

## 📌 목차

1. [핵심 아키텍처](#-핵심-아키텍처--성능-전략)
2. [기술 스택](#-기술-스택)
3. [데이터베이스 스키마](#-데이터베이스-스키마)
4. [API 명세](#-api-명세)
5. [시작하기](#-시작하기)
6. [보안 및 관리자 설정](#-보안--관리자-설정)
7. [프로젝트 구조](#-프로젝트-구조)

---

## 🏗️ 핵심 아키텍처 & 성능 전략

단순한 CRUD API를 넘어, 대량의 외부 API 데이터를 효율적으로 서빙하기 위해 다음과 같은 백엔드 최적화 전략을 채택했습니다.

### 1. Multi-Tier Caching (Redis)

외부 API(KEPCO)의 응답 지연 및 Rate Limit 문제를 극복하기 위해 **3단계 캐싱**을 구현했습니다.

| 계층 | 대상 데이터 | TTL | 목적 |
| :---: | :--- | :---: | :--- |
| **L1** Short-term | 좌표 기반 검색 결과 | 5분 | 반복 요청 응답 최적화 |
| **L2** Persistent | 충전소 위치·이름 등 정적 정보 | 24시간 | 인프라 데이터 보존 |
| **L3** Detail | 실시간 충전기 상태 정보 | 30분 | 데이터 신선도 유지 |

> **결과:** API 평균 응답 속도 **70% 이상 개선** 및 외부 API Rate Limit 회피를 통한 시스템 안정성 확보.

---

### 2. Spatial Data Optimization (PostGIS)

수만 개의 충전소 데이터를 단순 위경도 비교가 아닌 **PostGIS 공간 인덱스**를 통해 처리합니다.

- `ST_DWithin`을 활용한 인덱스 기반 반경 검색으로 대량 데이터셋에서도 **O(1)에 가까운 검색 성능** 확보
- 좌표 정규화(Bucket) 및 반올림 전략(`CACHE_COORD_ROUND_DECIMALS`)을 통해 **캐시 히트율 극대화**

---

### 3. Fault-Tolerant Data Pipeline

외부 API 장애 시에도 서비스 연속성을 보장하는 방어적 로직을 구축했습니다.

- **Geocoding Fallback:** Nominatim 실패 시 지역 단위 폴백으로 서비스 중단 없이 위치 검색 유지
- **Async I/O:** `httpx`와 `asyncpg`를 이용한 완전 비동기 처리로 동시성 요청 처리 능력 향상

---

## 🛠 기술 스택

| 분류 | 기술 | 선택 이유 |
| :--- | :--- | :--- |
| **Framework** | FastAPI | 고성능 비동기 처리 및 자동화된 API 명세(Swagger) 활용 |
| **Database** | PostgreSQL + PostGIS | 공간 데이터(Geometry) 엔진을 통한 고정밀 위치 검색 |
| **Cache** | Redis | 다층 캐시 구조 구현 및 시스템 성능 메트릭 추적 |
| **ORM / Migration** | SQLAlchemy 2.0 / Alembic | Async 환경 최적화 및 안정적인 스키마 버전 관리 |
| **Auth** | JWT / X-API-Key | 프론트엔드 통신 보안 및 사용자 인증의 이중화 |
| **Infra** | Docker / Render.com | 컨테이너화를 통한 환경 일관성 및 CI/CD 자동화 |

---

## 📊 데이터베이스 스키마

시스템의 핵심은 **정적 데이터(Station)**와 **동적 데이터(Charger 상태)**의 분리 및 효율적 연동입니다.

```
stations (1) ──── (N) chargers
    │
    └── PostGIS Geometry 컬럼 (공간 인덱스 기반 반경 검색)

subsidies ──── 국가·지자체 보조금 데이터 (ILIKE 패턴 매칭)
api_logs  ──── 외부 API 통신 이력 및 응답 상태 기록
```

| 테이블 | 역할 | 핵심 기술 |
| :--- | :--- | :--- |
| `stations` | 충전소 위치·이름 등 정적 정보 | PostGIS `Geometry` 컬럼, 공간 인덱스 |
| `chargers` | 실시간 충전기 상태 및 충전 타입 | `stations`와 1:N 관계 |
| `subsidies` | 전국 단위 전기차 보조금 데이터 | `ILIKE` 패턴 매칭 고속 조회 |
| `api_logs` | 외부 API 통신 및 응답 상태 기록 | 장애 추적성(Traceability) 확보 |

---

## 🔌 API 명세

| Endpoint | Method | Auth | Description |
| :--- | :---: | :---: | :--- |
| `/api/v1/stations` | `GET` | X-API-Key | 좌표 + 반경 기반 주변 충전소 검색 (Cache-First) |
| `/api/v1/station/{id}/chargers` | `GET` | X-API-Key | 실시간 충전기 가동 상태 및 상세 스펙 조회 |
| `/subsidy` | `GET` | X-API-Key | 제조사 / 모델별 국고 및 지방비 보조금 검색 |
| `/api/v1/auth/token` | `POST` | None | 사용자 인증 및 JWT 발급 |

---

## 🚀 시작하기

### 사전 요구사항

- Python 3.12+ / Poetry
- Docker & Docker Compose (PostGIS, Redis 환경 구성용)

### 로컬 실행

**1. 의존성 설치**

```bash
poetry install
```

**2. 인프라 실행 (PostgreSQL + Redis)**

```bash
docker-compose up -d
```

**3. DB 마이그레이션 및 초기 데이터 적재**

```bash
poetry run alembic upgrade head
poetry run python app/db/init_db.py
```

**4. 개발 서버 실행**

```bash
poetry run uvicorn app.main:app --reload
```

서버가 실행되면 `http://localhost:8000/docs` 에서 Swagger UI를 통해 API를 확인할 수 있습니다.

---

## 🛡 보안 & 관리자 설정

| 설정 | 방식 | 설명 |
| :--- | :--- | :--- |
| **Admin Mode** | `ADMIN_MODE=true` 환경변수 | HTTP Basic Auth로 보호된 Swagger UI 및 Redis 모니터링 엔드포인트 활성화 |
| **API Security** | `x-api-key` 헤더 | 허가된 프론트엔드 서비스와의 통신만 허용 |
| **User Auth** | JWT Bearer Token | `/api/v1/auth/token` 발급 후 인증 필요 엔드포인트에 사용 |

---

## 📂 프로젝트 구조

```
Backend_Server/
├── app/
│   ├── api/          # 라우터 및 의존성 정의 (Dependency Injection)
│   ├── core/         # 환경 설정 (Pydantic Settings)
│   ├── db/           # 비동기 엔진 및 리포지토리 패턴
│   ├── services/     # 지오코딩 및 보조금 조회 비즈니스 로직
│   └── models.py     # SQLAlchemy ORM 모델
├── alembic/          # DB 마이그레이션 히스토리
├── scripts/          # 데이터 동기화 및 운영 스크립트
└── docker-compose.yml
```
