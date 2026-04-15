"""Payment database model for Click payment integration."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, DateTime, Integer, ForeignKey, DECIMAL, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Payment(Base):
    """Tracks Click payment transactions for test purchases.

    States:
        pending   - created, waiting for Click Prepare
        prepared  - Prepare received and validated
        completed - Complete received, payment successful, test unlocked
        cancelled - Complete received with error, payment failed
    """

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Our identifiers
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    test_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)

    # Click identifiers (filled in during callbacks)
    click_trans_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    click_paydoc_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Status: pending | prepared | completed | cancelled
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="select")
    test: Mapped["Test"] = relationship("Test", lazy="select")

    __table_args__ = (
        Index("idx_payment_user_test", "user_id", "test_id"),
        Index("idx_payment_status", "status"),
        Index("idx_payment_click_trans", "click_trans_id"),
    )

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, user_id={self.user_id}, test_id={self.test_id}, status={self.status})>"


from app.models.user import User  # noqa: E402, F401
from app.models.test import Test  # noqa: E402, F401
