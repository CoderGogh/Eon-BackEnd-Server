from pydantic import BaseModel, Field, conint
from typing import List, Optional


class SubsidyRequest(BaseModel):
    manufacturer: str = Field(..., description="자동차 제조사 이름 (필수)")
    model_group: str = Field(..., description="차량 모델 그룹 이름 (필수, 예: GV60)")


class SubsidyPublic(BaseModel):
    model_name: str = Field(..., description="세부 모델 이름 (풀 스펙)")
    subsidy_national_10k_won: conint(ge=0) = Field(..., description="국고 보조금 (단위: 만 원)")
    subsidy_local_10k_won: conint(ge=0) = Field(..., description="지자체 보조금 (단위: 만 원)")
    subsidy_total_10k_won: conint(ge=0) = Field(..., description="총 보조금 (단위: 만 원)")
    sale_price: Optional[int] = Field(None, description="판매가(원)")

    class Config:
        from_attributes = True


class SubsidyListResponse(BaseModel):
    data: List[SubsidyPublic]
