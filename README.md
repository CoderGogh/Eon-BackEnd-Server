# Codyssey EV Charger Backend

FastAPI, PostgreSQL(PostGIS), Redis 기반의 전기차 충전 인프라 백엔드 서비스입니다.

성남시 주최 프로젝트로 개발된 이 시스템은 시의 전기차 진흥 정책에 발맞추어 기획되었습니다.

Google 설문조사를 통해 확인된 **전기차 수요 상승 트렌드**와 **시민들의 인프라 정보 접근성 강화 요구**를 바탕으로,


성남 시민들이 전기차를 더욱 스마트하게 활용할 수 있도록 돕는 백엔드 인프라를 제공합니다.


---

## 1. 소개

이 프로젝트는 **실시간 전기차 충전소 및 충전기 정보** 및 **성남시와 국가 보조금 정보**를 효율적으로 제공하기 위해 설계되었습니다. 


**PostGIS**를 통한 지리 정보 처리와 **Redis**를 활용한 고성능 캐싱을 지원하며, **Render** 환경에 최적화되어 있습니다.

### Tech Stack
- **Framework:** FastAPI (Python 3.10+)
- **Database:** PostgreSQL + PostGIS (공간 데이터 처리)
- **Caching:** Redis (성능 최적화 및 세션 관리)
- **Migration:** Alembic (DB 버전 관리)
- **Dependency:** Poetry
- **Deployment:** Render.com

---

## 2.  주요 기능 (Key Features)

###  데이터 API
- **보조금 조회:** 제조사 및 모델 그룹별 보조금 정보 제공 (`/subsidy`) -- 성남시에서 제공하는 데이터 API
- **DB 테스트:** 제조사/모델 그룹별 데이터 쿼리 테스트 (`/db-test`)
- **상태 점검:** 시스템 가동 상태 확인 (`/health`, `/`) -- Uptime Robot 사용

### 보안 및 인증
- **API Key 인증:** 프론트엔드 전용 `X-API-KEY` 헤더 검증
- **CORS 설정:** 허용된 Origin(`ALLOWED_ORIGINS`)만 접근 허용
- **JWT 보안:** `SECRET_KEY` 기반의 안전한 인증 체계
- **읽기 전용 보호:** DB 사용자 권한 및 코드 레벨의 `Read-Only` 방어 로직

### 운영 및 모니터링
- **Cold Start 방지:** UptimeRobot 등의 `HEAD` 요청 대응 핸들러 포함
- **Admin Mode:** 환경 변수에 따른 선택적 API 문서(`Swagger/ReDoc`) 노출 제어

---

## 3. 개발 설정 (Configuration & Setup)

### 모듈 참조 구조
시스템의 주요 설정 및 모듈 간의 참조 관계도입니다. 모든 설정은 `app/core/config.py`로 집중하여 일관성을 유지합니다.

```text
                 .env (optional, 프로젝트 루트)
                         |
                         v
              +-----------------------+
              | app/core/config.py    |  <- 메인 설정(Primary)
              |  Settings -> settings |
              +-----------------------+
                       ^       
                       |       
    +----------------+   +-------------+-------+-------------------+
    | app/main.py    |   | alembic/env.py                          |
    | app/api/...    |   | app/auth.py                             |
    +----------------+   +-----------------------------------------+

    (Legacy/Scripts)
    +----------------+
    | app/config.py  |  <- 보조 설정 (일부 스크립트 전용)
    +----------------+
            |
            v
    app/db/init_db.py
