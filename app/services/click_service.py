"""Click payment integration service.

Implements the two-phase Click SHOP-API:
  - Prepare  (action=0): validate order, reserve it
  - Complete (action=1): confirm or cancel payment
"""

import hashlib
import logging
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.payment import Payment
from app.models.test import Test

logger = logging.getLogger(__name__)

# ── Error codes returned to Click ────────────────────────────────────────────
ERR_OK = 0
ERR_SIGN = -1          # Invalid sign_string
ERR_INCORRECT_PARAMS = -2
ERR_ACTION = -3        # Action not found
ERR_ALREADY_PAID = -4  # Transaction already confirmed
ERR_USER_NOT_FOUND = -5
ERR_TRANSACTION_NOT_FOUND = -6
ERR_BAD_REQUEST = -8
ERR_TRANSACTION_CANCELLED = -9


def _sign_prepare(
    click_trans_id: int,
    service_id: int,
    secret_key: str,
    merchant_trans_id: str,
    amount: float,
    action: int,
    sign_time: str,
) -> str:
    """Compute MD5 signature for Prepare request."""
    raw = f"{click_trans_id}{service_id}{secret_key}{merchant_trans_id}{amount}{action}{sign_time}"
    return hashlib.md5(raw.encode()).hexdigest()


def _sign_complete(
    click_trans_id: int,
    service_id: int,
    secret_key: str,
    merchant_trans_id: str,
    merchant_prepare_id: int,
    amount: float,
    action: int,
    sign_time: str,
) -> str:
    """Compute MD5 signature for Complete request."""
    raw = (
        f"{click_trans_id}{service_id}{secret_key}{merchant_trans_id}"
        f"{merchant_prepare_id}{amount}{action}{sign_time}"
    )
    return hashlib.md5(raw.encode()).hexdigest()


class ClickService:
    """Handles Click Prepare and Complete callbacks."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.service_id = settings.click_service_id
        self.secret_key = settings.click_secret_key

    # ── Prepare ───────────────────────────────────────────────────────────────

    async def prepare(self, data: dict) -> dict:
        """Handle Click Prepare request (action=0).

        merchant_trans_id format: "<payment_id>"
        """
        click_trans_id = int(data["click_trans_id"])
        service_id = int(data["service_id"])
        merchant_trans_id = str(data["merchant_trans_id"])
        amount = float(data["amount"])
        action = int(data["action"])
        sign_time = str(data["sign_time"])
        sign_string = str(data["sign_string"])

        # Verify signature
        expected = _sign_prepare(
            click_trans_id, service_id, self.secret_key,
            merchant_trans_id, amount, action, sign_time,
        )
        if expected != sign_string:
            logger.warning("Prepare: invalid sign for click_trans_id=%s", click_trans_id)
            return self._error(click_trans_id, merchant_trans_id, ERR_SIGN, "Invalid sign_string")

        # Find payment record
        payment = await self._get_payment(merchant_trans_id)
        if payment is None:
            return self._error(click_trans_id, merchant_trans_id, ERR_TRANSACTION_NOT_FOUND, "Payment not found")

        # Already completed
        if payment.status == "completed":
            return self._error(click_trans_id, merchant_trans_id, ERR_ALREADY_PAID, "Already paid")

        # Already cancelled
        if payment.status == "cancelled":
            return self._error(click_trans_id, merchant_trans_id, ERR_TRANSACTION_CANCELLED, "Transaction cancelled")

        # Validate amount (allow ±1 sum tolerance for float rounding)
        if abs(float(payment.amount) - amount) > 1:
            return self._error(click_trans_id, merchant_trans_id, ERR_INCORRECT_PARAMS, "Incorrect amount")

        # Mark as prepared
        payment.click_trans_id = click_trans_id
        payment.click_paydoc_id = int(data.get("click_paydoc_id", 0))
        payment.status = "prepared"
        await self.db.commit()

        logger.info("Prepare OK: payment_id=%s click_trans_id=%s", payment.id, click_trans_id)
        return {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_prepare_id": payment.id,
            "error": ERR_OK,
            "error_note": "Success",
        }

    # ── Complete ──────────────────────────────────────────────────────────────

    async def complete(self, data: dict) -> dict:
        """Handle Click Complete request (action=1)."""
        click_trans_id = int(data["click_trans_id"])
        service_id = int(data["service_id"])
        merchant_trans_id = str(data["merchant_trans_id"])
        merchant_prepare_id = int(data["merchant_prepare_id"])
        amount = float(data["amount"])
        action = int(data["action"])
        sign_time = str(data["sign_time"])
        sign_string = str(data["sign_string"])
        error = int(data["error"])

        # Verify signature
        expected = _sign_complete(
            click_trans_id, service_id, self.secret_key,
            merchant_trans_id, merchant_prepare_id, amount, action, sign_time,
        )
        if expected != sign_string:
            logger.warning("Complete: invalid sign for click_trans_id=%s", click_trans_id)
            return self._error(click_trans_id, merchant_trans_id, ERR_SIGN, "Invalid sign_string")

        # Find payment record
        payment = await self._get_payment(merchant_trans_id)
        if payment is None:
            return self._error(click_trans_id, merchant_trans_id, ERR_TRANSACTION_NOT_FOUND, "Payment not found")

        # Verify prepare_id matches
        if payment.id != merchant_prepare_id:
            return self._error(click_trans_id, merchant_trans_id, ERR_INCORRECT_PARAMS, "Prepare ID mismatch")

        # Already completed
        if payment.status == "completed":
            return self._error(click_trans_id, merchant_trans_id, ERR_ALREADY_PAID, "Already paid")

        # Click signals cancellation (error < 0)
        if error < 0:
            payment.status = "cancelled"
            await self.db.commit()
            logger.info("Complete CANCELLED: payment_id=%s error=%s", payment.id, error)
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_confirm_id": payment.id,
                "error": ERR_TRANSACTION_CANCELLED,
                "error_note": "Transaction cancelled",
            }

        # Validate amount
        if abs(float(payment.amount) - amount) > 1:
            return self._error(click_trans_id, merchant_trans_id, ERR_INCORRECT_PARAMS, "Incorrect amount")

        # Confirm payment — unlock the test for the user
        payment.status = "completed"
        await self.db.commit()

        logger.info("Complete OK: payment_id=%s click_trans_id=%s", payment.id, click_trans_id)
        return {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_confirm_id": payment.id,
            "error": ERR_OK,
            "error_note": "Success",
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _get_payment(self, merchant_trans_id: str) -> Optional[Payment]:
        try:
            payment_id = int(merchant_trans_id)
        except (ValueError, TypeError):
            return None
        result = await self.db.execute(select(Payment).where(Payment.id == payment_id))
        return result.scalar_one_or_none()

    @staticmethod
    def _error(click_trans_id: int, merchant_trans_id: str, code: int, note: str) -> dict:
        return {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_prepare_id": None,
            "error": code,
            "error_note": note,
        }
