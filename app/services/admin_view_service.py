"""Read-only views for the admin: request details, customer/vehicle lookups,
the customer-approval monitor and the dashboard."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlmodel import Session

from app.enums.approval_status import ApprovalStatus
from app.enums.email_status import EmailStatus
from app.enums.maintenance_status import MaintenanceStatus
from app.enums.payment_transaction_status import PaymentTransactionStatus
from app.exceptions.app_exception import AppException
from app.models.car import Car
from app.models.maintenance_request import MaintenanceRequest
from app.models.maintenance_service import MaintenanceService
from app.models.user import User
from app.repositories.car_repository import CarRepository
from app.repositories.email_notification_repository import EmailNotificationRepository
from app.repositories.maintenance_image_repository import MaintenanceImageRepository
from app.repositories.maintenance_request_repository import MaintenanceRequestRepository
from app.repositories.maintenance_service_repository import MaintenanceServiceRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.payment_transaction_repository import PaymentTransactionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin_maintenance_request_schema import (
    AdminApprovalSummary,
    AdminAwaitingApprovalResponse,
    AdminCustomerDetailResponse,
    AdminCustomerResponse,
    AdminMaintenanceRequestDetailResponse,
    AdminMaintenanceRequestResponse,
    AdminPaymentResponse,
    AdminVehicleDetailResponse,
    AdminVehicleResponse,
)
from app.schemas.admin_schema import (
    AdminDashboardResponse,
    DashboardActivityItem,
    DashboardNotificationsSection,
    DashboardPaymentsSection,
    DashboardRequestItem,
    DashboardSection,
    DashboardStatistics,
)
from app.schemas.maintenance_image_schema import MaintenanceImageResponse
from app.schemas.maintenance_service_schema import MaintenanceServiceResponse
from app.schemas.payment_schema import PaymentTransactionResponse

DASHBOARD_LIST_SIZE = 10

PENDING_WORK_STATUSES = [
    MaintenanceStatus.PENDING,
    MaintenanceStatus.ACCEPTED,
    MaintenanceStatus.INSPECTING,
    MaintenanceStatus.IN_PROGRESS,
]


def customer_response(customer: User) -> AdminCustomerResponse:
    return AdminCustomerResponse(
        id=customer.id,
        first_name=customer.first_name,
        last_name=customer.last_name,
        email=customer.email,
        phone=customer.phone,
    )


def vehicle_response(vehicle: Car) -> AdminVehicleResponse:
    return AdminVehicleResponse(
        id=vehicle.id,
        make=vehicle.make,
        model=vehicle.model,
        year=vehicle.year,
        color=vehicle.color,
        plate_number=vehicle.plate_number,
        vin=vehicle.vin,
    )


def request_fields(request: MaintenanceRequest) -> dict:
    return dict(
        id=request.id,
        description=request.description,
        request_date=request.request_date,
        status=request.status,
        created_at=request.created_at,
        updated_at=request.updated_at,
        completed_at=request.completed_at,
        next_service_date=request.next_service_date,
        inspection_notes=request.inspection_notes,
        inspected_at=request.inspected_at,
    )


def build_admin_request_response(
    request: MaintenanceRequest, vehicle: Car, customer: User
) -> AdminMaintenanceRequestResponse:
    return AdminMaintenanceRequestResponse(
        **request_fields(request),
        customer=customer_response(customer),
        vehicle=vehicle_response(vehicle),
    )


def approval_summary(services: list[MaintenanceService]) -> AdminApprovalSummary:
    additional = [service for service in services if service.is_additional]

    def count(status: ApprovalStatus) -> int:
        return sum(1 for service in additional if service.approval == status)

    return AdminApprovalSummary(
        pending=count(ApprovalStatus.PENDING),
        approved=count(ApprovalStatus.APPROVED),
        rejected=count(ApprovalStatus.REJECTED),
    )


def billable_total(services: list[MaintenanceService]) -> Decimal:
    """Regular services plus APPROVED additional ones (same rule as the
    customer-facing cost calculation)."""
    total = Decimal("0.00")

    for service in services:
        if not service.is_additional or service.approval == ApprovalStatus.APPROVED:
            total += service.cost

    return total


class AdminViewService:
    def __init__(self, session: Session):
        self.request_repository = MaintenanceRequestRepository(session)
        self.car_repository = CarRepository(session)
        self.user_repository = UserRepository(session)
        self.service_repository = MaintenanceServiceRepository(session)
        self.image_repository = MaintenanceImageRepository(session)
        self.payment_repository = PaymentRepository(session)
        self.transaction_repository = PaymentTransactionRepository(session)
        self.notification_repository = EmailNotificationRepository(session)

    # ---- helpers -------------------------------------------------------

    def _vehicle_and_customer(self, request: MaintenanceRequest) -> tuple[Car, User]:
        vehicle = self.car_repository.find_by_id(request.car_id)

        if vehicle is None:
            raise AppException("Vehicle not found", status_code=404)

        customer = self.user_repository.find_by_id(vehicle.customer_id)

        if customer is None:
            raise AppException("Customer not found", status_code=404)

        return vehicle, customer

    def _summary(self, request: MaintenanceRequest):
        vehicle, customer = self._vehicle_and_customer(request)
        return vehicle, customer, build_admin_request_response(
            request, vehicle, customer
        )

    # ---- request / customer / vehicle ---------------------------------

    def get_request_detail(
        self, request_id: UUID
    ) -> AdminMaintenanceRequestDetailResponse:
        request = self.request_repository.find_by_id(request_id)

        if request is None:
            raise AppException("Maintenance request not found", status_code=404)

        vehicle, customer = self._vehicle_and_customer(request)
        services = self.service_repository.find_by_request_id(request_id)
        images = self.image_repository.find_by_request_id(request_id)
        payments = self.payment_repository.find_by_request_id(request_id) or []

        total_cost = billable_total(services)
        total_paid = sum((p.amount for p in payments), Decimal("0.00"))

        return AdminMaintenanceRequestDetailResponse(
            **request_fields(request),
            customer=customer_response(customer),
            vehicle=vehicle_response(vehicle),
            services=[
                MaintenanceServiceResponse.model_validate(s, from_attributes=True)
                for s in services
            ],
            images=[
                MaintenanceImageResponse.model_validate(i, from_attributes=True)
                for i in images
            ],
            payments=[
                AdminPaymentResponse.model_validate(p, from_attributes=True)
                for p in payments
            ],
            approvals=approval_summary(services),
            total_cost=total_cost,
            total_paid=total_paid,
            balance=total_cost - total_paid,
        )

    def get_customer(self, customer_id: UUID) -> AdminCustomerDetailResponse:
        customer = self.user_repository.find_by_id(customer_id)

        if customer is None:
            raise AppException("Customer not found", status_code=404)

        cars = self.car_repository.find_by_customer_id(customer_id) or []

        return AdminCustomerDetailResponse(
            customer=customer_response(customer),
            vehicles=[vehicle_response(car) for car in cars],
        )

    def get_vehicle(self, car_id: UUID) -> AdminVehicleDetailResponse:
        vehicle = self.car_repository.find_by_id(car_id)

        if vehicle is None:
            raise AppException("Vehicle not found", status_code=404)

        owner = self.user_repository.find_by_id(vehicle.customer_id)

        if owner is None:
            raise AppException("Customer not found", status_code=404)

        requests = self.request_repository.find_by_car_id(car_id) or []

        return AdminVehicleDetailResponse(
            vehicle=vehicle_response(vehicle),
            owner=customer_response(owner),
            request_count=len(requests),
        )

    # ---- customer approval monitor -------------------------------------

    def get_awaiting_approval(self) -> list[AdminAwaitingApprovalResponse]:
        results = []

        for request in self.request_repository.find_awaiting_customer_approval():
            _, _, summary = self._summary(request)
            services = self.service_repository.find_by_request_id(request.id)

            results.append(
                AdminAwaitingApprovalResponse(
                    request=summary,
                    pending_services=[
                        MaintenanceServiceResponse.model_validate(
                            s, from_attributes=True
                        )
                        for s in services
                        if s.is_additional and s.approval == ApprovalStatus.PENDING
                    ],
                    approvals=approval_summary(services),
                )
            )

        return results

    # ---- dashboard -------------------------------------------------------

    def _dashboard_item(self, request: MaintenanceRequest) -> DashboardRequestItem:
        vehicle, customer = self._vehicle_and_customer(request)
        services = self.service_repository.find_by_request_id(request.id)

        return DashboardRequestItem(
            id=request.id,
            description=request.description,
            status=request.status,
            request_date=request.request_date,
            updated_at=request.updated_at,
            customer_name=f"{customer.first_name} {customer.last_name}",
            plate_number=vehicle.plate_number,
            vehicle=f"{vehicle.year} {vehicle.make} {vehicle.model}",
            pending_approval_count=approval_summary(services).pending,
        )

    def _safe_items(self, requests: list[MaintenanceRequest]) -> list[DashboardRequestItem]:
        items = []

        for request in requests:
            try:
                items.append(self._dashboard_item(request))
            except AppException:
                continue  # orphaned request: skip rather than break the dashboard

        return items

    def get_dashboard(self) -> AdminDashboardResponse:
        now = datetime.now(timezone.utc)
        month_ago = now - timedelta(days=30)

        by_status = self.request_repository.count_by_status()

        statistics = DashboardStatistics(
            total_requests=sum(by_status.values()),
            by_status={
                status.value: by_status.get(status, 0) for status in MaintenanceStatus
            },
            created_last_30_days=self.request_repository.count_created_since(month_ago),
            completed_last_30_days=self.request_repository.count_completed_since(
                month_ago
            ),
            total_revenue=self.payment_repository.total_received(),
        )

        awaiting = self.request_repository.find_awaiting_customer_approval()
        awaiting_ids = {request.id for request in awaiting}

        # Work the workshop must act on: new/active requests, plus requests
        # whose extra services the customer has already answered (they sit in
        # AWAITING_APPROVAL until the admin moves them on).
        answered = [
            request
            for request in self.request_repository.find_by_statuses(
                [MaintenanceStatus.AWAITING_APPROVAL]
            )
            if request.id not in awaiting_ids
        ]
        active = self.request_repository.find_by_statuses(
            PENDING_WORK_STATUSES, oldest_first=True
        )
        pending_work = sorted(active + answered, key=lambda r: r.created_at)

        pending_count = len(pending_work)
        pending_items = self._safe_items(pending_work[:DASHBOARD_LIST_SIZE])

        awaiting_items = self._safe_items(awaiting[:DASHBOARD_LIST_SIZE])

        review = PaymentTransactionStatus.NEEDS_REVIEW
        review_items = self.transaction_repository.find_by_status(
            review, limit=DASHBOARD_LIST_SIZE
        )

        activity = []
        for request in self.request_repository.find_recently_updated(
            DASHBOARD_LIST_SIZE
        ):
            try:
                vehicle, customer = self._vehicle_and_customer(request)
            except AppException:
                continue

            activity.append(
                DashboardActivityItem(
                    request_id=request.id,
                    status=request.status,
                    description=request.description,
                    customer_name=f"{customer.first_name} {customer.last_name}",
                    plate_number=vehicle.plate_number,
                    occurred_at=request.updated_at,
                )
            )

        return AdminDashboardResponse(
            statistics=statistics,
            pending_work=DashboardSection(count=pending_count, items=pending_items),
            awaiting_customer_approval=DashboardSection(
                count=len(awaiting), items=awaiting_items
            ),
            payments_needing_review=DashboardPaymentsSection(
                count=self.transaction_repository.count_by_status(review),
                items=[
                    PaymentTransactionResponse.model_validate(t, from_attributes=True)
                    for t in review_items
                ],
            ),
            notification_problems=DashboardNotificationsSection(
                failed_count=self.notification_repository.count_by_status(
                    EmailStatus.FAILED
                )
            ),
            recent_activity=activity,
        )
