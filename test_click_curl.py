"""
Generates curl commands to manually test the Click Prepare and Complete callbacks.

Usage:
    python test_click_curl.py

Steps:
    1. Start your server:  uvicorn app.main:app --reload
    2. Run this script to get the curl commands with correct signatures
    3. Execute the curl commands in order (prepare first, then complete)
"""

import hashlib

# ── Config (must match your .env) ────────────────────────────────────────────
SERVICE_ID       = 99674
SECRET_KEY       = "0MIYh977pjNF6"
BASE_URL         = "http://localhost:8000"

# ── Fake Click transaction values ─────────────────────────────────────────────
CLICK_TRANS_ID   = 999999          # fake Click transaction ID
CLICK_PAYDOC_ID  = 888888          # fake Click paydoc ID
MERCHANT_TRANS_ID = "1"            # your payment.id (must exist in DB)
AMOUNT           = 10.0            # must match the payment's amount in DB
SIGN_TIME        = "2026-04-15 12:00:00"

# ── Signature helpers ─────────────────────────────────────────────────────────
def sign_prepare():
    raw = f"{CLICK_TRANS_ID}{SERVICE_ID}{SECRET_KEY}{MERCHANT_TRANS_ID}{AMOUNT}0{SIGN_TIME}"
    return hashlib.md5(raw.encode()).hexdigest()

def sign_complete(merchant_prepare_id: int):
    raw = f"{CLICK_TRANS_ID}{SERVICE_ID}{SECRET_KEY}{MERCHANT_TRANS_ID}{merchant_prepare_id}{AMOUNT}1{SIGN_TIME}"
    return hashlib.md5(raw.encode()).hexdigest()

# ── Print commands ────────────────────────────────────────────────────────────
prepare_sign = sign_prepare()
# merchant_prepare_id is the payment.id returned by Prepare — same as MERCHANT_TRANS_ID here
complete_sign = sign_complete(int(MERCHANT_TRANS_ID))

print("=" * 70)
print("STEP 0 — Create a payment record first (requires a logged-in session)")
print("=" * 70)
print(f"""
curl -X POST "{BASE_URL}/api/payment/initiate/1" \\
  -H "Cookie: session=<your-session-cookie>" \\
  -H "Content-Type: application/json"
""")

print("=" * 70)
print("STEP 1 — Simulate Click PREPARE callback (action=0)")
print("=" * 70)
print(f"sign_string = md5({CLICK_TRANS_ID}{SERVICE_ID}{SECRET_KEY}{MERCHANT_TRANS_ID}{AMOUNT}0{SIGN_TIME})")
print(f"           = {prepare_sign}")
print(f"""
curl -X POST "{BASE_URL}/api/payment/prepare" \\
  -F "click_trans_id={CLICK_TRANS_ID}" \\
  -F "service_id={SERVICE_ID}" \\
  -F "click_paydoc_id={CLICK_PAYDOC_ID}" \\
  -F "merchant_trans_id={MERCHANT_TRANS_ID}" \\
  -F "amount={AMOUNT}" \\
  -F "action=0" \\
  -F "error=0" \\
  -F "error_note=Success" \\
  -F "sign_time={SIGN_TIME}" \\
  -F "sign_string={prepare_sign}"
""")
print("Expected response: {{ \"error\": 0, \"merchant_prepare_id\": {MERCHANT_TRANS_ID}, ... }}")

print()
print("=" * 70)
print("STEP 2 — Simulate Click COMPLETE callback (action=1)")
print("=" * 70)
print(f"sign_string = md5({CLICK_TRANS_ID}{SERVICE_ID}{SECRET_KEY}{MERCHANT_TRANS_ID}{MERCHANT_TRANS_ID}{AMOUNT}1{SIGN_TIME})")
print(f"           = {complete_sign}")
print(f"""
curl -X POST "{BASE_URL}/api/payment/complete" \\
  -F "click_trans_id={CLICK_TRANS_ID}" \\
  -F "service_id={SERVICE_ID}" \\
  -F "click_paydoc_id={CLICK_PAYDOC_ID}" \\
  -F "merchant_trans_id={MERCHANT_TRANS_ID}" \\
  -F "merchant_prepare_id={MERCHANT_TRANS_ID}" \\
  -F "amount={AMOUNT}" \\
  -F "action=1" \\
  -F "error=0" \\
  -F "error_note=Success" \\
  -F "sign_time={SIGN_TIME}" \\
  -F "sign_string={complete_sign}"
""")
print(f"Expected response: {{ \"error\": 0, \"merchant_confirm_id\": {MERCHANT_TRANS_ID}, ... }}")

print()
print("=" * 70)
print("STEP 3 — Check payment status")
print("=" * 70)
print(f"""
curl "{BASE_URL}/api/payment/status/1" \\
  -H "Cookie: session=<your-session-cookie>"
""")
print('Expected response: { "test_id": 1, "paid": true }')

print()
print("=" * 70)
print("STEP 4 — Test that the test is now accessible (was blocked before payment)")
print("=" * 70)
print(f"""
curl "{BASE_URL}/api/client/tests/1" \\
  -H "Cookie: session=<your-session-cookie>"
""")
print("Expected: full test with questions (not 402 Payment Required)")

print()
print("=" * 70)
print("BONUS — Test invalid signature (should return error -1)")
print("=" * 70)
print(f"""
curl -X POST "{BASE_URL}/api/payment/prepare" \\
  -F "click_trans_id={CLICK_TRANS_ID}" \\
  -F "service_id={SERVICE_ID}" \\
  -F "click_paydoc_id={CLICK_PAYDOC_ID}" \\
  -F "merchant_trans_id={MERCHANT_TRANS_ID}" \\
  -F "amount={AMOUNT}" \\
  -F "action=0" \\
  -F "error=0" \\
  -F "error_note=Success" \\
  -F "sign_time={SIGN_TIME}" \\
  -F "sign_string=invalidsignature"
""")
print('Expected response: { "error": -1, "error_note": "Invalid sign_string" }')
