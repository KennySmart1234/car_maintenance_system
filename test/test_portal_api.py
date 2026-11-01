"""End-to-end tests for the customer portal, notifications, profile and the
admin list/search/report endpoints (real app, in-memory SQLite)."""

from decimal import Decimal
from uuid import UUID, uuid4

from sqlmodel import Session

from app.enums.payment_transaction_status import PaymentTransactionStatus
from app.models.payment_transaction import PaymentTransaction
from app.config.settings import settings
from test_admin_api import (  # noqa: F401  (fixtures + helpers)
    PNG, _add_service, _advance, client, engine, world,
)


def _pay(client, world, service_id, amount="5000", method="CASH"):
    return client.post("/payments/", json={
        "maintenance_request_id": world["request_id"], "maintenance_service_id": service_id,
        "amount": amount, "method": method}, headers=world["admin"])


# ------------------------------------------------------------ profile & auth

def test_profile_password_and_refresh(client, world):
    me = client.get("/auth/me", headers=world["customer"]).json()
    assert me["email"] == "cust@mail.com" and "password" not in me and me["role"] == "CUSTOMER"
    assert client.get("/auth/me").status_code == 401

    updated = client.patch("/auth/me", json={"first_name": "Chidiebere", "phone": "08111111111"},
                           headers=world["customer"]).json()
    assert updated["first_name"] == "Chidiebere" and updated["phone"] == "08111111111"
    assert client.patch("/auth/me", json={"first_name": "X"}, headers=world["customer"]).status_code == 422

    bad = client.post("/auth/change-password", headers=world["customer"],
                      json={"current_password": "wrong-password", "new_password": "BrandNewPass123"})
    assert bad.status_code == 400
    same = client.post("/auth/change-password", headers=world["customer"],
                       json={"current_password": "Passw0rd12345", "new_password": "Passw0rd12345"})
    assert same.status_code == 400
    ok = client.post("/auth/change-password", headers=world["customer"],
                     json={"current_password": "Passw0rd12345", "new_password": "BrandNewPass123"})
    assert ok.status_code == 200
    assert client.post("/auth/login", json={"email": "cust@mail.com", "password": "BrandNewPass123"}).status_code == 200
    assert client.post("/auth/login", json={"email": "cust@mail.com", "password": "Passw0rd12345"}).status_code in (400, 401, 403)

    fresh = client.post("/auth/refresh", headers=world["customer"]).json()
    assert fresh["token_type"] == "bearer"
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {fresh['access_token']}"}).status_code == 200
    assert client.post("/auth/refresh").status_code == 401


# ------------------------------------------------- my requests / car / photo

def test_my_requests_car_detail_and_photo(client, world):
    _advance(client, world, "ACCEPTED", "INSPECTING")
    _add_service(client, world, name="Oil change", cost="8000")
    _add_service(client, world, additional=True, name="Disc", cost="40000")

    mine = client.get("/customer/maintenance-requests", headers=world["customer"]).json()
    assert len(mine) == 1
    r = mine[0]
    assert r["description"].startswith("Brake") and r["car"]["plate_number"] == "ABC-123"
    assert r["pending_approval_count"] == 1
    assert Decimal(r["total_cost"]) == Decimal("8000")  # unapproved extra not billed
    assert client.get("/customer/maintenance-requests", headers=world["other"]).json() == []

    car = client.get(f"/customer/cars/{world['car_id']}", headers=world["customer"]).json()
    assert car["vin"] == "1HGBH41JXMN109186" and len(car["requests"]) == 1 and car["image_url"] is None
    assert client.get(f"/customer/cars/{world['car_id']}", headers=world["other"]).status_code == 403

    up = client.post(f"/customer/cars/{world['car_id']}/photo", headers=world["customer"],
                     files={"file": ("car.png", PNG, "image/png")})
    assert up.status_code == 200 and up.json()["image_url"].endswith(".png")
    assert client.post(f"/customer/cars/{world['car_id']}/photo", headers=world["other"],
                       files={"file": ("car.png", PNG, "image/png")}).status_code == 403
    assert client.post(f"/customer/cars/{world['car_id']}/photo", headers=world["customer"],
                       files={"file": ("x.png", b"not an image", "image/png")}).status_code == 415

    again = client.post(f"/customer/cars/{world['car_id']}/photo", headers=world["customer"],
                        files={"file": ("c2.png", PNG, "image/png")}).json()
    assert again["image_url"] != up.json()["image_url"]  # replaced
    admin_view = client.get("/admin/vehicles", headers=world["admin"]).json()
    assert admin_view[0]["image_url"] == again["image_url"]


# ----------------------------------------------------------------- payments

def test_payments_summary_history_and_verify(client, world, engine, monkeypatch):
    service_id = _add_service(client, world, cost="15000").json()["maintenance_service_id"]

    summary = client.get("/customer/payments/summary", headers=world["customer"]).json()
    assert Decimal(summary["outstanding_balance"]) == Decimal("15000")
    assert summary["unpaid_services"][0]["service_id"] == service_id

    assert _pay(client, world, service_id, "5000").status_code == 200
    summary = client.get("/customer/payments/summary", headers=world["customer"]).json()
    assert Decimal(summary["total_paid"]) == Decimal("5000")
    assert Decimal(summary["outstanding_balance"]) == Decimal("10000")

    with Session(engine, expire_on_commit=False) as session:
        for ref, status in (("PSK-FAIL", PaymentTransactionStatus.FAILED), ("PSK-OK", PaymentTransactionStatus.SUCCESS)):
            session.add(PaymentTransaction(
                reference=ref, user_id=world["customer_user"].id,
                maintenance_request_id=UUID(world["request_id"]),
                maintenance_service_id=UUID(service_id), amount=Decimal("2000"), status=status))
        session.commit()

    history = client.get("/customer/payments", headers=world["customer"]).json()
    statuses = {h["status"] for h in history}
    assert "SUCCESS" in statuses and "FAILED" in statuses
    assert all(h["reference"] != "PSK-OK" for h in history)  # success without a payment row is not invented
    assert client.get("/customer/payments", headers=world["other"]).json() == []

    ok = client.get("/customer/payments/verify/PSK-OK", headers=world["customer"]).json()
    assert ok["status"] == "SUCCESS" and Decimal(ok["amount"]) == Decimal("2000")
    assert client.get("/customer/payments/verify/PSK-OK", headers=world["other"]).status_code == 404
    assert client.get("/customer/payments/verify/NOPE", headers=world["customer"]).status_code == 404


def test_paystack_callback_redirects_to_frontend(client, world, engine, monkeypatch):
    monkeypatch.setattr(settings, "frontend_base_url", "https://app.motora.test")
    with Session(engine, expire_on_commit=False) as session:
        session.add(PaymentTransaction(
            reference="PSK-REV", user_id=world["customer_user"].id,
            maintenance_request_id=UUID(world["request_id"]), maintenance_service_id=uuid4(),
            amount=Decimal("100"), status=PaymentTransactionStatus.NEEDS_REVIEW))
        session.commit()

    response = client.get("/payments/paystack/callback", params={"reference": "PSK-REV"},
                          follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers["location"] == \
        "https://app.motora.test/app/payments/success?reference=PSK-REV&status=NEEDS_REVIEW"


# ------------------------------------------------------------ notifications

def test_notifications_are_created_listed_and_marked_read(client, world):
    rid = world["request_id"]
    _advance(client, world, "ACCEPTED", "INSPECTING")
    service_id = _add_service(client, world, additional=True, cost="40000").json()["maintenance_service_id"]
    client.patch(f"/customer/maintenance-services/{service_id}/approve", headers=world["customer"])
    _pay(client, world, service_id, "1000")

    everything = client.get("/customer/notifications", headers=world["customer"]).json()
    titles = [n["title"] for n in everything]
    assert {"Maintenance Request Accepted", "Inspection Started",
            "Additional Service Requires Approval", "Payment Received"} <= set(titles)
    assert everything[0]["created_at"] >= everything[-1]["created_at"]  # newest first
    assert all(n["maintenance_request_id"] == rid for n in everything)

    assert [n["title"] for n in client.get("/customer/notifications", params={"category": "PAYMENTS"},
            headers=world["customer"]).json()] == ["Payment Received"]
    assert client.get("/customer/notifications", headers=world["other"]).json() == []
    assert client.get("/customer/notifications/unread-count", headers=world["customer"]).json()["unread"] == len(everything)

    first = everything[0]["id"]
    assert client.patch(f"/customer/notifications/{first}/read", headers=world["other"]).status_code == 404
    done = client.patch(f"/customer/notifications/{first}/read", headers=world["customer"]).json()
    assert done["is_read"] is True
    assert client.get("/customer/notifications/unread-count", headers=world["customer"]).json()["unread"] == len(everything) - 1
    assert len(client.get("/customer/notifications", params={"unread_only": True}, headers=world["customer"]).json()) == len(everything) - 1

    assert client.post("/customer/notifications/read-all", headers=world["customer"]).json()["marked"] == len(everything) - 1
    assert client.get("/customer/notifications/unread-count", headers=world["customer"]).json()["unread"] == 0


# ----------------------------------------------------------- admin lists etc.

def test_admin_customers_vehicles_search(client, world):
    customers = client.get("/admin/customers", headers=world["admin"]).json()
    assert {c["email"] for c in customers} == {"cust@mail.com", "other@mail.com"}
    assert [c["vehicle_count"] for c in customers if c["email"] == "cust@mail.com"] == [1]
    assert [c["first_name"] for c in client.get("/admin/customers", params={"search": "chid"}, headers=world["admin"]).json()] == ["Chidi"]
    assert client.get("/admin/customers", params={"search": "zzz"}, headers=world["admin"]).json() == []

    vehicles = client.get("/admin/vehicles", params={"search": "camry"}, headers=world["admin"]).json()
    assert vehicles[0]["owner_name"] == "Chidi User" and vehicles[0]["plate_number"] == "ABC-123"
    assert [v["plate_number"] for v in client.get("/admin/vehicles", params={"search": "chidi"}, headers=world["admin"]).json()] == ["ABC-123"]

    found = client.get("/admin/search", params={"q": "abc-1"}, headers=world["admin"]).json()
    assert len(found["requests"]) == 1 and len(found["vehicles"]) == 1 and found["customers"] == []
    found = client.get("/admin/search", params={"q": "chidi"}, headers=world["admin"]).json()
    assert [c["first_name"] for c in found["customers"]] == ["Chidi"]
    assert client.get("/admin/search", params={"q": "a"}, headers=world["admin"]).status_code == 422
    assert client.get("/admin/customers", headers=world["customer"]).status_code == 403


def test_admin_payments_images_reports_and_pagination(client, world):
    service_id = _add_service(client, world, cost="15000").json()["maintenance_service_id"]
    _pay(client, world, service_id, "6000", "TRANSFER")
    _pay(client, world, service_id, "4000", "CASH")

    payments = client.get("/admin/payments", headers=world["admin"]).json()
    assert len(payments) == 2 and payments[0]["customer_name"] == "Chidi User"
    assert payments[0]["service_name"] == "Brake pads" and payments[0]["plate_number"] == "ABC-123"
    assert len(client.get("/admin/payments", params={"limit": 1}, headers=world["admin"]).json()) == 1
    assert len(client.get("/admin/payments", params={"limit": 1, "offset": 1}, headers=world["admin"]).json()) == 1

    for cat in ("BEFORE", "AFTER"):
        client.post("/admin/maintenance-images/upload", headers=world["admin"],
                    data={"maintenance_request_id": world["request_id"], "category": cat},
                    files={"file": ("p.png", PNG, "image/png")})
    gallery = client.get("/admin/maintenance-images", headers=world["admin"]).json()
    assert len(gallery) == 2 and gallery[0]["customer_name"] == "Chidi User"
    assert [g["category"] for g in client.get("/admin/maintenance-images", params={"category": "AFTER"}, headers=world["admin"]).json()] == ["AFTER"]
    assert client.get("/admin/maintenance-images", params={"request_id": str(uuid4())}, headers=world["admin"]).json() == []

    report = client.get("/admin/reports", headers=world["admin"]).json()
    assert Decimal(report["total_revenue"]) == Decimal("10000")
    assert len(report["revenue_by_month"]) == 1 and Decimal(report["revenue_by_month"][0]["revenue"]) == Decimal("10000")
    assert {k: Decimal(v) for k, v in report["payments_by_method"].items()} == {"TRANSFER": Decimal("6000"), "CASH": Decimal("4000")}
    assert report["requests_by_status"]["PENDING"] == 1 and report["requests_created"] == 1
    assert report["top_services"][0]["name"] == "Brake pads"
    assert client.get("/admin/reports", params={"days": 1}, headers=world["admin"]).status_code == 422

    assert len(client.get("/admin/maintenance-requests", params={"limit": 1}, headers=world["admin"]).json()) == 1
    assert client.get("/admin/maintenance-requests", params={"offset": 5}, headers=world["admin"]).json() == []
