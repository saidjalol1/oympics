"""Click payment API endpoints.

Handles:
  - POST /api/payment/initiate/{test_id}  — create payment record, return Click redirect URL
  - POST /api/payment/prepare             — Click Prepare callback (action=0)
  - POST /api/payment/complete            — Click Complete callback (action=1)
  - GET  /api/payment/status/{test_id}    — check if current user paid for a test
"""

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.repositories.payment_repository import PaymentRepository
from app.repositories.test_repository import TestRepository
from app.services.click_service import ClickService

router = APIRouter(prefix="/api/payment", tags=["payment"])


# ── Initiate ──────────────────────────────────────────────────────────────────

@router.post("/initiate/{test_id}")
async def initiate_payment(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a payment record and return the Click payment URL.

    The client should redirect the user to the returned `payment_url`.
    After payment Click will call /prepare and /complete on this server.
    """
    test_repo = TestRepository(db)
    test = await test_repo.get_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    payment_repo = PaymentRepository(db)

    # If already paid, return success immediately
    existing = await payment_repo.get_completed_payment(current_user.id, test_id)
    if existing:
        return {"status": "already_paid", "test_id": test_id}

    # Reuse pending payment if one exists
    payment = await payment_repo.get_pending_payment(current_user.id, test_id)
    if not payment:
        payment = await payment_repo.create_payment(
            user_id=current_user.id,
            test_id=test_id,
            amount=float(test.price),
        )

    # Build Click payment URL
    # https://my.click.uz/services/pay?service_id=...&merchant_id=...&amount=...&transaction_param=...
    payment_url = (
        f"https://my.click.uz/services/pay"
        f"?service_id={settings.click_service_id}"
        f"&merchant_id={settings.click_merchant_id}"
        f"&amount={float(test.price)}"
        f"&transaction_param={payment.id}"
        f"&return_url={settings.frontend_url}/tests/{test_id}"
    )

    return {
        "payment_id": payment.id,
        "amount": float(test.price),
        "payment_url": payment_url,
    }


# ── Prepare callback ──────────────────────────────────────────────────────────

@router.post("/prepare")
async def click_prepare(
    click_trans_id: int = Form(...),
    service_id: int = Form(...),
    click_paydoc_id: int = Form(...),
    merchant_trans_id: str = Form(...),
    amount: float = Form(...),
    action: int = Form(...),
    error: int = Form(...),
    error_note: str = Form(...),
    sign_time: str = Form(...),
    sign_string: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Click Prepare callback (action=0). Called by Click servers."""
    service = ClickService(db)
    return await service.prepare({
        "click_trans_id": click_trans_id,
        "service_id": service_id,
        "click_paydoc_id": click_paydoc_id,
        "merchant_trans_id": merchant_trans_id,
        "amount": amount,
        "action": action,
        "error": error,
        "error_note": error_note,
        "sign_time": sign_time,
        "sign_string": sign_string,
    })


# ── Complete callback ─────────────────────────────────────────────────────────

@router.post("/complete")
async def click_complete(
    click_trans_id: int = Form(...),
    service_id: int = Form(...),
    click_paydoc_id: int = Form(...),
    merchant_trans_id: str = Form(...),
    merchant_prepare_id: int = Form(...),
    amount: float = Form(...),
    action: int = Form(...),
    error: int = Form(...),
    error_note: str = Form(...),
    sign_time: str = Form(...),
    sign_string: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Click Complete callback (action=1). Called by Click servers."""
    service = ClickService(db)
    return await service.complete({
        "click_trans_id": click_trans_id,
        "service_id": service_id,
        "click_paydoc_id": click_paydoc_id,
        "merchant_trans_id": merchant_trans_id,
        "merchant_prepare_id": merchant_prepare_id,
        "amount": amount,
        "action": action,
        "error": error,
        "error_note": error_note,
        "sign_time": sign_time,
        "sign_string": sign_string,
    })


# ── Status check ──────────────────────────────────────────────────────────────

@router.get("/status/{test_id}")
async def payment_status(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check whether the current user has paid for a test."""
    payment_repo = PaymentRepository(db)
    paid = await payment_repo.get_completed_payment(current_user.id, test_id)
    return {"test_id": test_id, "paid": paid is not None}
