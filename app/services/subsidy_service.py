from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Subsidy
from app.schemas.subsidy import SubsidyPublic


class SubsidyService:
    @staticmethod
    async def get_subsidy_info(db: AsyncSession, manufacturer: str, model_group: str) -> List[SubsidyPublic]:
        manufacturer = (manufacturer or "").strip()
        model_group = (model_group or "").strip()

        query = select(Subsidy).where(
            Subsidy.manufacturer == manufacturer,
            Subsidy.model_group.ilike(f"{model_group}%")
        ).order_by(Subsidy.model_name)

        result = await db.execute(query)
        return [
            SubsidyPublic(
                model_name=s.model_name,
                subsidy_national_10k_won=s.subsidy_national_10k_won,
                subsidy_local_10k_won=s.subsidy_local_10k_won,
                subsidy_total_10k_won=s.subsidy_total_10k_won,
                sale_price=s.sale_price if hasattr(s, "sale_price") else None
            )
            for s in result.scalars().all()
        ]


subsidy_service = SubsidyService()
