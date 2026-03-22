from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional

from app.models import User as DBUser
from app.schemas.user import UserCreate


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[DBUser]:
    stmt = select(DBUser).where(DBUser.username == username)
    result = await db.execute(stmt)
    return result.scalars().first()


async def create_user(db: AsyncSession, user: UserCreate, hashed_password: str) -> DBUser:
    new_user = DBUser(
        username=user.username,
        email=user.email,
        role=user.role,
        hashed_password=hashed_password
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
