from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

from app.schemas.maintenance_request_schema import MaintenanceRequestCreate
from app.services.maintenance_request_service import MaintenanceRequestService


def test_create_request_returns_created_request():
    session = Mock()
    car_repository = Mock()
    maintenance_request_repository = Mock()

    service = MaintenanceRequestService(session)

    service.car_repository = car_repository
    service.maintenance_request_repository = maintenance_request_repository

    car_id = uuid4()

    request_data = MaintenanceRequestCreate(
        car_id=car_id,
        description="Oil change and brake inspection",
        request_date=datetime.now(timezone.utc),
    )

    car_repository.find_by_id.return_value = Mock()

    created_request = Mock()
    maintenance_request_repository.create.return_value = created_request

    result = service.create_request(request_data)

    assert result == created_request