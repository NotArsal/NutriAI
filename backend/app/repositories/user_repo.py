"""
app/repositories/user_repo.py — Database interactions for User model.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash


class UserRepository:
    @staticmethod
    async def get_by_email(session: AsyncSession, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: int) -> User | None:
        return await session.get(User, user_id)

    @staticmethod
    async def create(session: AsyncSession, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            role="patient",
            is_active=True,
        )
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj
