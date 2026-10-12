import hashlib
import hmac
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import quote

import httpx

from app.config.settings import settings
from app.exceptions.app_exception import AppException

PAYSTACK_BASE_URL = "https://api.paystack.co"
TIMEOUT_SECONDS = 30.0


def to_kobo(amount: Decimal) -> int:
    """Paystack wants whole kobo (naira x 100) as an integer."""
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _headers() -> dict:
    if not settings.paystack_secret_key:
        raise AppException("Online payments are not configured", status_code=503)

    return {
        "Authorization": f"Bearer {settings.paystack_secret_key}",
        "Content-Type": "application/json",
    }


def _call(method: str, path: str, json: dict | None = None) -> dict:
    headers = _headers()

    try:
        response = httpx.request(
            method,
            f"{PAYSTACK_BASE_URL}{path}",
            json=json,
            headers=headers,
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        body = response.json()
    except (httpx.HTTPError, ValueError) as error:
        print("PAYSTACK ERROR:", error)
        raise AppException(
            "Could not reach the payment provider. Please try again.",
            status_code=502,
        )

    if not body.get("status"):
        print("PAYSTACK REJECTED:", body.get("message"))
        raise AppException(
            "The payment provider rejected the request.", status_code=502
        )

    return body["data"]


def initialize_transaction(
    email: str, amount_kobo: int, reference: str, callback_url: str
) -> dict:
    return _call(
        "POST",
        "/transaction/initialize",
        json={
            "email": email,
            "amount": amount_kobo,
            "currency": "NGN",
            "reference": reference,
            "callback_url": callback_url,
        },
    )


def verify_transaction(reference: str) -> dict:
    return _call("GET", f"/transaction/verify/{quote(reference, safe='')}")


def verify_signature(raw_body: bytes, signature: str | None) -> bool:
    """Paystack signs every webhook: HMAC-SHA512 of the raw body, keyed with
    your secret key, sent in the x-paystack-signature header."""
    if not signature or not settings.paystack_secret_key:
        return False

    expected = hmac.new(
        settings.paystack_secret_key.encode("utf-8"),
        raw_body,
        hashlib.sha512,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)