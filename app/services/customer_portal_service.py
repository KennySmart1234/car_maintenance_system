"""Read-side helpers for the customer app: my requests, my payments,
what I still owe, and car details/photo."""

from decimal import Decimal
from uuid import UUID

from sqlmodel import Session

from app.enums.approval_status import ApprovalStatus
from app.enums.maintenance_status import MaintenanceStatus
from app.enums.payment_transaction_status import PaymentTransactionStatus
from app.exceptions.app_exception import AppException
from app.models.car import Car
from app.repositories.car_repository import CarRepository
from app.repositories.maintenance_request_repository import MaintenanceRequestRepository
from app.repositories.maintenance_service_repository import MaintenanceServiceRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.payment_transaction_repository import PaymentTransactionRepository
from app.schemas.customer_schema import (
    CustomerCarDetailResponse,
    CustomerCarSummary,
    CustomerPaymentItem,
    CustomerRequestResponse,
    PaymentSummaryResponse,
    UnpaidService,
)
from app.services import image_storage
from app.services.admin_view_service import billable_total

ZERO = Decimal("0.00")
# Failed / pending / under-review online attempts that have no recorded payment.
VISIBLE_TRANSACTION_STATUSES = (
    PaymentTransactionStatus.PENDING,
    PaymentTransactionStatus.FAILED,
    PaymentTransactionStatus.NEEDS_REVIEW,
)


class CustomerPortalService:
    def __init__(self, session: Session):
        self.car_repository = CarRepository(session)
        self.request_repository = MaintenanceRequestRepository(session)
        self.service_repository = MaintenanceServiceRepository(session)
        self.payment_repository = PaymentRepository(session)
        self.transaction_repository = PaymentTransactionRepository(session)

    # ---- requests ------------------------------------------------------

    def _request_response(self, request, car: Car) -> CustomerRequestResponse:
        services = self.service_repository.find_by_request_id(request.id)
        payments = self.payment_repository.find_by_request_id(request.id) or []
        total = billable_total(services)
        paid = sum((p.amount for p in payments), ZERO)

        return CustomerRequestResponse(
            id=request.id,
            description=request.description,
            request_date=request.request_date,
            status=request.status,
            updated_at=request.updated_at,
            completed_at=request.completed_at,
            next_service_date=request.next_service_date,
            car=CustomerCarSummary(
                id=car.id, make=car.make, model=car.model,
                year=car.year, plate_number=car.plate_number,
            ),
            total_cost=total,
            total_paid=paid,
            balance=max(total - paid, ZERO),
            pending_approval_count=sum(
                1 for s in services
                if s.is_additional and s.approval == ApprovalStatus.PENDING
            ),
        )

    def list_requests(self, customer_id: UUID) -> list[CustomerRequestResponse]:
        cars = {c.id: c for c in self.car_repository.find_by_customer_id(customer_id) or []}
        return [
            self._request_response(r, cars[r.car_id])
            for r in self.request_repository.find_by_customer_id(customer_id)
            if r.car_id in cars
        ]

    def get_car_detail(self, car: Car) -> CustomerCarDetailResponse:
        requests = [r for r in self.list_requests(car.customer_id) if r.car.id == car.id]

        return CustomerCarDetailResponse(
            id=car.id, make=car.make, model=car.model, year=car.year,
            color=car.color, plate_number=car.plate_number, vin=car.vin,
            image_url=car.image_url, created_at=car.created_at, requests=requests,
        )

    def set_car_photo(self, car: Car, content: bytes) -> Car:
        new_url = image_storage.save_image(content)
        old_url = car.image_url
        car.image_url = new_url
        try:
            car = self.car_repository.update(car)
        except Exception:
            image_storage.delete_image_file(new_url)
            raise

        if old_url:
            image_storage.delete_image_file(old_url)

        return car

    # ---- payments ------------------------------------------------------

    def list_payments(self, customer_id: UUID) -> list[CustomerPaymentItem]:
        descriptions = {
            r.id: r.description for r in self.request_repository.find_by_customer_id(customer_id)
        }
        payments = self.payment_repository.find_for_customer(customer_id)
        recorded = {p.reference for p in payments}

        items = [
            CustomerPaymentItem(
                reference=p.reference,
                maintenance_request_id=p.maintenance_request_id,
                request_description=descriptions.get(p.maintenance_request_id, ""),
                amount=p.amount, date=p.payment_date, status="SUCCESS", method=p.method,
            )
            for p in payments
        ]

        for t in self.transaction_repository.find_for_user(customer_id):
            if t.status in VISIBLE_TRANSACTION_STATUSES and t.reference not in recorded:
                items.append(
                    CustomerPaymentItem(
                        reference=t.reference,
                        maintenance_request_id=t.maintenance_request_id,
                        request_description=descriptions.get(t.maintenance_request_id, ""),
                        amount=t.amount, date=t.paid_at or t.created_at,
                        status=t.status.value,
                    )
                )

        return sorted(items, key=lambda i: i.date, reverse=True)

    def payment_summary(self, customer_id: UUID) -> PaymentSummaryResponse:
        billed = paid_total = ZERO
        unpaid: list[UnpaidService] = []

        for request in self.request_repository.find_by_customer_id(customer_id):
            if request.status == MaintenanceStatus.CANCELED:
                continue

            payments = self.payment_repository.find_by_request_id(request.id) or []
            paid_by_service: dict[UUID, Decimal] = {}

            for p in payments:
                paid_total += p.amount
                if p.maintenance_service_id:
                    paid_by_service[p.maintenance_service_id] = (
                        paid_by_service.get(p.maintenance_service_id, ZERO) + p.amount
                    )

            for service in self.service_repository.find_by_request_id(request.id):
                if service.is_additional and service.approval != ApprovalStatus.APPROVED:
                    continue

                billed += service.cost
                balance = service.cost - paid_by_service.get(service.id, ZERO)

                if balance > 0:
                    unpaid.append(
                        UnpaidService(
                            service_id=service.id, maintenance_request_id=request.id,
                            name=service.name, balance=balance,
                        )
                    )

        return PaymentSummaryResponse(
            total_billed=billed, total_paid=paid_total,
            outstanding_balance=sum((u.balance for u in unpaid), ZERO),
            unpaid_services=unpaid,
        )
