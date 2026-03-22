from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChargerBase(BaseModel):
    charger_code: Optional[str] = Field(None, description="충전기 고유 코드")
    charger_type: Optional[str] = Field(None, description="충전 방식 (예: DC차데모, AC완속)")
    output_kw: Optional[float] = Field(None, description="충전기 출력 (kW)")
    connector_type: Optional[str] = Field(None, description="커넥터 타입")
    status_code: Optional[int] = Field(None, description="충전기 상태 코드 (0: 사용가능, 1: 충전중 등)")


class StationPublic(BaseModel):
    id: int
    station_code: str = Field(..., description="충전소 고유 코드")
    name: str = Field(..., description="충전소 이름")
    address: Optional[str] = Field(None, description="주소")
    provider: Optional[str] = Field(None, description="충전소 제공 사업자")
    latitude: Optional[float] = Field(None, description="위도 (WGS 84)")
    longitude: Optional[float] = Field(None, description="경도 (WGS 84)")
    chargers: List[ChargerBase] = Field(default_factory=list, description="충전소에 속한 충전기 목록")

    class Config:
        from_attributes = True


class SubsidyPublic(BaseModel):
    id: int
    manufacturer: str = Field(..., description="제조사")
    model_group: str = Field(..., description="모델 그룹명 (예: IONIQ5)")
    model_name: str = Field(..., description="모델 상세 이름 (예: IONIQ 5 롱 레인지 2WD)")
    max_subsidy_amount: int = Field(..., description="최대 보조금액 (국비 + 지방비)")
    national_subsidy: int = Field(..., description="국비 보조금액")
    local_subsidy: int = Field(..., description="지자체(local) 보조금액")
    is_performance_verified: bool = Field(..., description="성능평가 통과 여부")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApiLogBase(BaseModel):
    endpoint: str = Field(..., description="요청 엔드포인트 경로")
    method: str = Field(..., description="HTTP 메서드 (GET, POST 등)")
    api_type: str = Field(..., description="API 타입 (예: StationInfo, StatusUpdate)")
    status_code: int = Field(..., description="HTTP 응답 상태 코드")
    response_code: Optional[int] = Field(None, description="외부 API 응답 코드")
    response_msg: Optional[str] = Field(None, description="외부 API 응답 메시지")
    response_time_ms: float = Field(..., description="응답 시간 (밀리초)")

    class Config:
        from_attributes = True


class ChargerStatusUpdate(BaseModel):
    new_status_code: int = Field(..., description="업데이트할 새로운 충전기 상태 코드")
