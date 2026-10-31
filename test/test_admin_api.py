"""End-to-end tests of the admin API: real FastAPI app, real auth tokens and
an in-memory SQLite database (no mocks of our own code)."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401  (register tables)
from app.config.dependencies import get_session
from app.config.password import hash_password
from app.config.security import create_access_token
from app.config.settings import settings
from app.enums.email_status import EmailStatus
from app.enums.payment_transaction_status import PaymentTransactionStatus
from app.enums.user_role import UserRole
from app.models.car import Car
from app.models.email_notification import EmailNotification
from app.models.maintenance_request import MaintenanceRequest
from app.models.payment_transaction import PaymentTransaction
from app.models.user import User
from app.services.email_service import EmailService
from main import app as fastapi_app

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def client(engine, tmp_path, monkeypatch):
    def override():
        with Session(engine, expire_on_commit=False) as session:
            yield session

    fastapi_app.dependency_overrides[get_session] = override
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    monkeypatch.setattr(settings, "app_base_url", "http://testserver")
    monkeypatch.setattr(EmailService, "send_additional_maintenance_email", lambda *a, **k: None)
    monkeypatch.setattr(EmailService, "send_notification_email", lambda *a, **k: None)

    yield TestClient(fastapi_app)
    fastapi_app.dependency_overrides.clear()


def _user(engine, role, email, first="Test", phone="08012345678"):
    with Session(engine, expire_on_commit=False) as session:
        user = User(
            first_name=first, last_name="User", email=email, phone=phone,
            password=hash_password("Passw0rd12345"), role=role, email_verified=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def _headers(user):
    return {"Authorization": f"Bearer {create_access_token(user.id, user.role)}"}


@pytest.fixture
def world(engine):
    admin = _user(engine, UserRole.WORKSHOP_ADMIN, "admin@shop.com", "Ada")
    customer = _user(engine, UserRole.CUSTOMER, "cust@mail.com", "Chidi")
    other = _user(engine, UserRole.CUSTOMER, "other@mail.com", "Obi")

    with Session(engine, expire_on_commit=False) as session:
        car = Car(
            customer_id=customer.id, make="Toyota", model="Camry", year=2020,
            color="Black", plate_number="ABC-123", vin="1HGBH41JXMN109186",
        )
        session.add(car)
        session.commit()
        session.refresh(car)

        request = MaintenanceRequest(
            car_id=car.id, description="Brake squeal and vibration",
            request_date=datetime.now(timezone.utc),
        )
        session.add(request)
        session.commit()
        session.refresh(request)

    return {
        "admin": _headers(admin), "customer": _headers(customer),
        "other": _headers(other), "admin_user": admin, "customer_user": customer,
        "car_id": str(car.id), "request_id": str(request.id),
    }


def _advance(client, world, *statuses):
    for status in statuses:
        response = client.patch(
            f"/admin/maintenance-requests/{world['request_id']}/status",
            params={"status": status}, headers=world["admin"],
        )
        assert response.status_code == 200, response.text


def _add_service(client, world, additional=False, name="Brake pads", cost="15000"):
    return client.post(
        "/admin/maintenance-services",
        json={
            "maintenance_request_id": world["request_id"], "name": name,
            "description": "Replace the pads", "cost": cost, "is_additional": additional,
        },
        headers=world["admin"],
    )


# ------------------------------------------------------------------ access

def test_admin_endpoints_reject_customers_and_anonymous(client, world):
    assert client.get("/admin/dashboard").status_code == 401
    assert client.get("/admin/dashboard", headers=world["customer"]).status_code == 403
    assert client.get("/admin/admins", headers=world["customer"]).status_code == 403


# ------------------------------------------------- requests, customer, vehicle

def test_list_filter_and_detail_with_customer_and_vehicle(client, world):
    _add_service(client, world)

    listing = client.get("/admin/maintenance-requests", headers=world["admin"]).json()
    assert len(listing) == 1 and listing[0]["customer"]["email"] == "cust@mail.com"

    assert client.get("/admin/maintenance-requests", params={"status": "PENDING"},
                      headers=world["admin"]).json()[0]["id"] == world["request_id"]
    assert client.get("/admin/maintenance-requests", params={"status": "COMPLETED"},
                      headers=world["admin"]).json() == []

    detail = client.get(f"/admin/maintenance-requests/{world['request_id']}",
                        headers=world["admin"]).json()
    assert detail["customer"]["first_name"] == "Chidi"
    assert detail["vehicle"]["plate_number"] == "ABC-123"
    assert [s["name"] for s in detail["services"]] == ["Brake pads"]
    assert Decimal(detail["total_cost"]) == Decimal("15000")
    assert Decimal(detail["balance"]) == Decimal("15000")
    assert detail["images"] == [] and detail["payments"] == []


def test_detail_404_and_customer_and_vehicle_lookups(client, world):
    assert client.get(f"/admin/maintenance-requests/{uuid4()}",
                      headers=world["admin"]).status_code == 404

    customer = client.get(f"/admin/customers/{world['customer_user'].id}",
                          headers=world["admin"]).json()
    assert customer["customer"]["email"] == "cust@mail.com"
    assert customer["vehicles"][0]["vin"] == "1HGBH41JXMN109186"

    vehicle = client.get(f"/admin/vehicles/{world['car_id']}", headers=world["admin"]).json()
    assert vehicle["owner"]["email"] == "cust@mail.com" and vehicle["request_count"] == 1

    assert client.get(f"/admin/vehicles/{uuid4()}", headers=world["admin"]).status_code == 404


# ----------------------------------------------------------- vehicle checks

def test_verify_vehicle_reports_which_value_differs_and_ignores_formatting(client, world):
    url = f"/admin/verify-vehicle/{world['car_id']}"

    ok = client.get(url, params={"plate_number": " abc 123 ", "vin": "1hgbh41jxmn109186"},
                    headers=world["admin"]).json()
    assert ok == {"verified": True, "car_found": True,
                  "plate_number_matches": True, "vin_matches": True}

    bad_vin = client.get(url, params={"plate_number": "ABC-123", "vin": "WRONG"},
                         headers=world["admin"]).json()
    assert bad_vin["verified"] is False
    assert bad_vin["plate_number_matches"] is True and bad_vin["vin_matches"] is False

    missing = client.get(f"/admin/verify-vehicle/{uuid4()}",
                         params={"plate_number": "X", "vin": "Y"}, headers=world["admin"]).json()
    assert missing["car_found"] is False and missing["verified"] is False


# -------------------------------------------------- accept / inspect / notes

def test_accept_inspect_records_notes_and_notes_can_be_edited(client, world):
    rid = world["request_id"]
    assert client.patch(f"/admin/maintenance-requests/{rid}/accept",
                        headers=world["admin"]).json()["status"] == "ACCEPTED"

    # notes are not editable before the inspection has started
    early = client.put(f"/admin/maintenance-requests/{rid}/inspection-notes",
                       json={"notes": "too early"}, headers=world["admin"])
    assert early.status_code == 409

    inspected = client.patch(f"/admin/maintenance-requests/{rid}/inspect",
                             json={"notes": "Front pads at 1mm, discs scored"},
                             headers=world["admin"]).json()
    assert inspected["status"] == "INSPECTING"
    assert inspected["inspection_notes"] == "Front pads at 1mm, discs scored"
    assert inspected["inspected_at"] is not None

    client.put(f"/admin/maintenance-requests/{rid}/inspection-notes",
               json={"notes": "Also rear pads worn"}, headers=world["admin"])
    detail = client.get(f"/admin/maintenance-requests/{rid}", headers=world["admin"]).json()
    assert detail["inspection_notes"] == "Also rear pads worn"


def test_inspect_without_a_body_still_works(client, world):
    _advance(client, world, "ACCEPTED")
    response = client.patch(f"/admin/maintenance-requests/{world['request_id']}/inspect",
                            headers=world["admin"])
    assert response.status_code == 200 and response.json()["inspection_notes"] is None


# ------------------------------------------- additional services & approvals

def test_additional_service_approval_monitoring_and_gating(client, world):
    rid = world["request_id"]
    _advance(client, world, "ACCEPTED", "INSPECTING")
    _add_service(client, world, additional=False, name="Oil change", cost="8000")
    added = _add_service(client, world, additional=True, name="Disc replacement", cost="40000")
    assert added.status_code == 200 and added.json()["email_sent"] is True
    service_id = added.json()["maintenance_service_id"]

    # request is now awaiting the customer, and the monitor shows it
    queue = client.get("/admin/maintenance-requests/awaiting-approval",
                       headers=world["admin"]).json()
    assert len(queue) == 1
    assert queue[0]["request"]["id"] == rid and queue[0]["request"]["status"] == "AWAITING_APPROVAL"
    assert queue[0]["pending_services"][0]["name"] == "Disc replacement"
    assert queue[0]["approvals"] == {"pending": 1, "approved": 0, "rejected": 0}

    # work cannot start while the customer has not answered
    blocked = client.patch(f"/admin/maintenance-requests/{rid}/status",
                           params={"status": "IN_PROGRESS"}, headers=world["admin"])
    assert blocked.status_code == 409
    assert "pending" in blocked.json()["detail"]

    # another customer cannot answer for this one
    assert client.patch(f"/customer/maintenance-services/{service_id}/reject",
                        headers=world["other"]).status_code == 403

    # customer rejects: queue empties, rejected cost is not billed, work can start
    rejected = client.patch(f"/customer/maintenance-services/{service_id}/reject",
                            headers=world["customer"])
    assert rejected.status_code == 200 and rejected.json()["approval"] == "REJECTED"
    assert client.patch(f"/customer/maintenance-services/{service_id}/approve",
                        headers=world["customer"]).status_code == 409

    assert client.get("/admin/maintenance-requests/awaiting-approval",
                      headers=world["admin"]).json() == []
    # answered but not yet moved on: it is the workshop's turn, not the customer's
    dash = client.get("/admin/dashboard", headers=world["admin"]).json()
    assert dash["awaiting_customer_approval"]["count"] == 0
    assert dash["pending_work"]["count"] == 1
    assert dash["pending_work"]["items"][0]["status"] == "AWAITING_APPROVAL"

    detail = client.get(f"/admin/maintenance-requests/{rid}", headers=world["admin"]).json()
    assert detail["approvals"] == {"pending": 0, "approved": 0, "rejected": 1}
    assert Decimal(detail["total_cost"]) == Decimal("8000")

    _advance(client, world, "IN_PROGRESS", "COMPLETED")
    done = client.get(f"/admin/maintenance-requests/{rid}", headers=world["admin"]).json()
    assert done["status"] == "COMPLETED" and done["completed_at"] is not None


def test_approved_additional_service_counts_and_unblocks(client, world):
    _advance(client, world, "ACCEPTED", "INSPECTING")
    service_id = _add_service(client, world, additional=True, cost="40000").json()["maintenance_service_id"]

    assert client.patch(f"/customer/maintenance-services/{service_id}/approve",
                        headers=world["customer"]).status_code == 200
    _advance(client, world, "IN_PROGRESS")

    detail = client.get(f"/admin/maintenance-requests/{world['request_id']}",
                        headers=world["admin"]).json()
    assert detail["approvals"]["approved"] == 1
    assert Decimal(detail["total_cost"]) == Decimal("40000")


def test_customer_cannot_reject_regular_service(client, world):
    service_id = _add_service(client, world, additional=False).json()["maintenance_service_id"]
    response = client.patch(f"/customer/maintenance-services/{service_id}/reject",
                            headers=world["customer"])
    assert response.status_code == 409


def test_next_service_date(client, world):
    response = client.patch(
        f"/admin/maintenance-requests/{world['request_id']}/next-service-date",
        params={"next_service_date": "2027-03-01"}, headers=world["admin"])
    assert response.status_code == 200 and response.json()["next_service_date"] == "2027-03-01"


# ------------------------------------------------------------------- images

def _upload(client, world, content, category="BEFORE", name="photo.png", mime="image/png"):
    return client.post(
        "/admin/maintenance-images/upload",
        data={"maintenance_request_id": world["request_id"], "category": category},
        files={"file": (name, content, mime)}, headers=world["admin"],
    )


def test_upload_categorize_view_and_customer_access(client, world, tmp_path):
    uploaded = _upload(client, world, PNG)
    assert uploaded.status_code == 201
    image = uploaded.json()
    assert image["category"] == "BEFORE"
    assert image["image_url"].startswith("http://testserver/uploads/maintenance_images/")
    assert image["image_url"].endswith(".png")
    assert len(list((tmp_path / "maintenance_images").iterdir())) == 1

    _upload(client, world, JPEG, category="AFTER", name="after.jpg", mime="image/jpeg")
    rid = world["request_id"]

    admin_view = client.get(f"/maintenance-requests/{rid}/images", headers=world["admin"]).json()
    assert [i["category"] for i in admin_view] == ["BEFORE", "AFTER"]

    # the owning customer sees the same photos, a stranger does not
    customer_view = client.get(f"/maintenance-requests/{rid}/images", headers=world["customer"])
    assert customer_view.status_code == 200 and len(customer_view.json()) == 2
    assert client.get(f"/maintenance-requests/{rid}/images", headers=world["other"]).status_code == 403
    assert client.get(f"/maintenance-requests/{rid}/images").status_code == 401

    only_after = client.get(f"/maintenance-requests/{rid}/images",
                            params={"category": "AFTER"}, headers=world["customer"]).json()
    assert len(only_after) == 1

    recategorized = client.patch(f"/admin/maintenance-images/{image['id']}/category",
                                 json={"category": "DAMAGE_PART"}, headers=world["admin"])
    assert recategorized.status_code == 200 and recategorized.json()["category"] == "DAMAGE_PART"

    detail = client.get(f"/admin/maintenance-requests/{rid}", headers=world["admin"]).json()
    assert len(detail["images"]) == 2


def test_uploaded_file_is_actually_served(client, world):
    url = _upload(client, world, PNG).json()["image_url"]
    path = url.replace("http://testserver", "")
    # main.py mounted /uploads at import time, before this test redirected the dir,
    # so re-point the static mount at the test directory for this check.
    from fastapi.staticfiles import StaticFiles
    for route in fastapi_app.routes:
        if getattr(route, "path", None) == "/uploads":
            route.app = StaticFiles(directory=settings.upload_dir)
    assert client.get(path).content == PNG


def test_upload_rejects_bad_files(client, world, monkeypatch):
    fake = _upload(client, world, b"<html>not an image</html>", name="evil.png", mime="image/png")
    assert fake.status_code == 415

    assert _upload(client, world, b"").status_code == 400

    monkeypatch.setattr(settings, "max_image_bytes", 100)
    assert _upload(client, world, PNG + b"\x00" * 200).status_code == 413

    missing = client.post(
        "/admin/maintenance-images/upload",
        data={"maintenance_request_id": str(uuid4()), "category": "BEFORE"},
        files={"file": ("p.png", PNG, "image/png")}, headers=world["admin"])
    assert missing.status_code == 404


def test_url_based_upload_still_works(client, world):
    response = client.post(
        "/admin/maintenance-images",
        json={"maintenance_request_id": world["request_id"],
              "image_url": "https://cdn.example.com/a.jpg", "category": "REMOVED_PART"},
        headers=world["admin"])
    assert response.status_code == 200


# ------------------------------------------------------------- notifications

def test_notification_problems_listed_and_retried(client, world, monkeypatch):
    _advance(client, world, "ACCEPTED", "INSPECTING")

    def boom(*args, **kwargs):
        raise RuntimeError("mail provider down")

    monkeypatch.setattr(EmailService, "send_additional_maintenance_email", boom)
    added = _add_service(client, world, additional=True)
    assert added.json()["email_sent"] is False

    problems = client.get("/admin/email-notifications", headers=world["admin"]).json()
    assert len(problems) == 1
    assert problems[0]["status"] == "FAILED" and problems[0]["recipient_email"] == "cust@mail.com"
    assert client.get("/admin/email-notifications", params={"status": "SENT"},
                      headers=world["admin"]).json() == []

    dashboard = client.get("/admin/dashboard", headers=world["admin"]).json()
    assert dashboard["notification_problems"]["failed_count"] == 1

    retried = client.post(f"/admin/email-notifications/{problems[0]['id']}/retry",
                          headers=world["admin"])
    assert retried.status_code == 200 and retried.json()["status"] == "SENT"
    assert retried.json()["sent_at"] is not None

    again = client.post(f"/admin/email-notifications/{problems[0]['id']}/retry",
                        headers=world["admin"])
    assert again.status_code == 409
    assert client.post(f"/admin/email-notifications/{uuid4()}/retry",
                       headers=world["admin"]).status_code == 404


def test_retry_failed_in_bulk(client, world, engine):
    with Session(engine, expire_on_commit=False) as session:
        for _ in range(2):
            session.add(EmailNotification(
                user_id=world["customer_user"].id, maintenance_request_id=UUID(world["request_id"]),
                title="t", subject="s", message="m", status=EmailStatus.FAILED))
        session.commit()

    assert client.post("/admin/email-notifications/retry-failed",
                       headers=world["admin"]).json() == {"sent": 2, "still_failed": 0}
    assert client.get("/admin/email-notifications", headers=world["admin"]).json() == []


# ----------------------------------------------------------- administrators

def test_list_and_add_administrators_never_expose_passwords(client, world):
    listing = client.get("/admin/admins", headers=world["admin"])
    assert listing.status_code == 200
    assert [a["email"] for a in listing.json()] == ["admin@shop.com"]
    assert "password" not in listing.json()[0]

    payload = {"first_name": "Bola", "last_name": "Ade", "email": "BOLA@shop.com",
               "password": "AnotherPass123", "phone": "08099999999"}
    created = client.post("/admin/admins", json=payload, headers=world["admin"])
    assert created.status_code == 200
    assert created.json()["email"] == "bola@shop.com" and created.json()["role"] == "WORKSHOP_ADMIN"
    assert "password" not in created.json()

    assert client.post("/admin/admins", json=payload, headers=world["admin"]).status_code == 400
    assert len(client.get("/admin/admins", headers=world["admin"]).json()) == 2


# ----------------------------------------------------------------- payments

def test_payment_review_and_resolve(client, world, engine):
    with Session(engine, expire_on_commit=False) as session:
        session.add(PaymentTransaction(
            reference="PSK-1", user_id=world["customer_user"].id,
            maintenance_request_id=UUID(world["request_id"]), maintenance_service_id=uuid4(),
            amount=Decimal("5000"), status=PaymentTransactionStatus.NEEDS_REVIEW))
        session.commit()
    # (FK enforcement is off in SQLite, so the dummy service id is fine here)

    queue = client.get("/admin/payment-transactions", headers=world["admin"]).json()
    assert [t["reference"] for t in queue] == ["PSK-1"]
    assert client.get("/admin/dashboard", headers=world["admin"]).json()[
        "payments_needing_review"]["count"] == 1

    assert client.patch("/admin/payment-transactions/PSK-1/resolve",
                        headers=world["admin"]).json()["status"] == "RESOLVED"
    assert client.get("/admin/payment-transactions", headers=world["admin"]).json() == []
    assert client.get("/admin/dashboard", headers=world["admin"]).json()[
        "payments_needing_review"]["count"] == 0


# ---------------------------------------------------------------- dashboard

def test_dashboard_sections(client, world):
    rid = world["request_id"]
    empty = client.get("/admin/dashboard", headers=world["admin"]).json()
    assert empty["statistics"]["total_requests"] == 1
    assert empty["statistics"]["by_status"]["PENDING"] == 1
    assert empty["pending_work"]["count"] == 1
    assert empty["pending_work"]["items"][0]["customer_name"] == "Chidi User"
    assert empty["pending_work"]["items"][0]["plate_number"] == "ABC-123"
    assert empty["awaiting_customer_approval"]["count"] == 0
    assert empty["recent_activity"][0]["request_id"] == rid

    _advance(client, world, "ACCEPTED", "INSPECTING")
    _add_service(client, world, additional=True)

    busy = client.get("/admin/dashboard", headers=world["admin"]).json()
    assert busy["statistics"]["by_status"]["AWAITING_APPROVAL"] == 1
    assert busy["awaiting_customer_approval"]["count"] == 1
    assert busy["awaiting_customer_approval"]["items"][0]["pending_approval_count"] == 1
    assert busy["pending_work"]["count"] == 0  # awaiting approval is not "pending work"
    assert busy["recent_activity"][0]["status"] == "AWAITING_APPROVAL"


def test_dashboard_statistics_after_completion_and_revenue(client, world):
    _advance(client, world, "ACCEPTED", "INSPECTING", "IN_PROGRESS", "COMPLETED")
    data = client.get("/admin/dashboard", headers=world["admin"]).json()["statistics"]
    assert data["by_status"]["COMPLETED"] == 1
    assert data["completed_last_30_days"] == 1 and data["created_last_30_days"] == 1
    assert Decimal(str(data["total_revenue"])) == Decimal("0")
