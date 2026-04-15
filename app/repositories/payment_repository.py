"""Payment repository for database operations."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, db: AsyncSession):
        super().__init__(Payment, db)

    async def create_payment(self, user_id: int, test_id: int, amount: float) -> Payment:
        return await super().create(user_id=user_id, test_id=test_id, amount=amount)

    async def get_by_id(self, payment_id: int) -> Optional[Payment]:
        return await super().get_by_id(payment_id)

    async def get_completed_payment(self, user_id: int, test_id: int) -> Optional[Payment]:
        """Check if user has a completed payment for a test."""
        result = await self.db.execute(
            select(Payment).where(
                Payment.user_id == user_id,
                Payment.test_id == test_id,
                Payment.status == "completed",
            )
        )
        return result.scalar_one_or_none()

    async def get_pending_payment(self, user_id: int, test_id: int) -> Optional[Payment]:
        """Get an existing pending/prepared payment for a test."""
        result = await self.db.execute(
            select(Payment).where(
                Payment.user_id == user_id,
                Payment.test_id == test_id,
                Payment.status.in_(["pending", "prepared"]),
            )
        )
        return result.scalar_one_or_none()
