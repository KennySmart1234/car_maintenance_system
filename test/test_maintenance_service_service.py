import pytest
from unittest.mock import Mock
from uuid import uuid4

from app.enums.maintenance_status import MaintenanceStatus
from app.exceptions.app_exception import AppException
from app.models.maintenance_service import MaintenanceService
from app.repositories.maintenance_service_repository import MaintenanceServiceRepository
from app.services.maintenance_service_service import MaintenanceServiceService


def test_create_maintenance_service_successfully():
    repository = Mock(spec=MaintenanceServiceRepository)

    service = MaintenanceServiceService.__new__(MaintenanceServiceService)
    service.maintenance_service_repository = repository

    maintenance_service = MaintenanceService(
        maintenance_request_id=uuid4(),
        name="Oil Change",
        description="Engine oil replacement",
        cost=50000,
        is_additional=False,
    )

    repository.create.return_value = maintenance_service

    result = service.create_service(maintenance_service)

    assert result == maintenance_service
    repository.create.assert_called_once_with(maintenance_service)


def test_create_additional_maintenance_service_successfully():
    repository = Mock(spec=MaintenanceServiceRepository)

    service = MaintenanceServiceService.__new__(MaintenanceServiceService)
    service.maintenance_service_repository = repository

    maintenance_service = MaintenanceService(
        maintenance_request_id=uuid4(),
        name="Brake Pad Replacement",
        description="Replace worn front brake pads",
        cost=75000,
        is_additional=True,
    )

    repository.create.return_value = maintenance_service

    result = service.create_service(maintenance_service)

    assert result == maintenance_service
    assert result.is_additional is True
    repository.create.assert_called_once_with(maintenance_service)



def test_get_service_by_id_successfully():
    repository = Mock(spec=MaintenanceServiceRepository)

    service = MaintenanceServiceService.__new__(MaintenanceServiceService)
    service.maintenance_service_repository = repository

    service_id = uuid4()

    maintenance_service = MaintenanceService(
        id=service_id,
        maintenance_request_id=uuid4(),
        name="Oil Change",
        description="Engine oil replacement",
        cost=50000,
        is_additional=False,
    )

    repository.find_by_id.return_value = maintenance_service

    result = service.get_service_by_id(service_id)

    assert result == maintenance_service
    repository.find_by_id.assert_called_once_with(service_id)



def test_get_service_by_id_raises_error_when_service_not_found():
    repository = Mock(spec=MaintenanceServiceRepository)

    service = MaintenanceServiceService.__new__(MaintenanceServiceService)
    service.maintenance_service_repository = repository

    service_id = uuid4()

    repository.find_by_id.return_value = None

    with pytest.raises(AppException, match="Maintenance service not found"):
        service.get_service_by_id(service_id)

    repository.find_by_id.assert_called_once_with(service_id)


def test_get_services_by_request_id_successfully():
    repository = Mock(spec=MaintenanceServiceRepository)

    service = MaintenanceServiceService.__new__(MaintenanceServiceService)
    service.maintenance_service_repository = repository

    request_id = uuid4()

    services = [
        MaintenanceService(
            maintenance_request_id=request_id,
            name="Oil Change",
            description="Engine oil replacement",
            cost=50000,
            is_additional=False,
        ),
        MaintenanceService(
            maintenance_request_id=request_id,
            name="Brake Pad Replacement",
            description="Replace worn brake pads",
            cost=75000,
            is_additional=True,
        ),
    ]

    repository.find_by_request_id.return_value = services

    result = service.get_services_by_request_id(request_id)

    assert result == services
    repository.find_by_request_id.assert_called_once_with(request_id)



def test_update_maintenance_service_successfully():
    repository = Mock(spec=MaintenanceServiceRepository)

    service = MaintenanceServiceService.__new__(MaintenanceServiceService)
    service.maintenance_service_repository = repository

    maintenance_service = MaintenanceService(
        id=uuid4(),
        maintenance_request_id=uuid4(),
        name="Brake Pad Replacement",
        description="Replace worn brake pads",
        cost=75000,
        is_additional=True,
    )

    repository.update.return_value = maintenance_service

    result = service.update_service(maintenance_service)

    assert result == maintenance_service
    repository.update.assert_called_once_with(maintenance_service)


def test_update_service_raises_error_when_service_not_found():
    repository = Mock(spec=MaintenanceServiceRepository)

    service = MaintenanceServiceService.__new__(MaintenanceServiceService)
    service.maintenance_service_repository = repository

    maintenance_service = MaintenanceService(
        id=uuid4(),
        maintenance_request_id=uuid4(),
        name="Brake Pad Replacement",
        description="Replace worn brake pads",
        cost=75000,
        is_additional=True,
    )

    repository.find_by_id.return_value = None

    with pytest.raises(AppException, match="Maintenance service not found"):
        service.update_service(maintenance_service)

    repository.find_by_id.assert_called_once_with(maintenance_service.id)


def test_get_services_by_request_id_returns_empty_list_when_no_services():
    repository = Mock(spec=MaintenanceServiceRepository)

    service = MaintenanceServiceService.__new__(MaintenanceServiceService)
    service.maintenance_service_repository = repository

    request_id = uuid4()

    repository.find_by_request_id.return_value = []

    result = service.get_services_by_request_id(request_id)

    assert result == []
    repository.find_by_request_id.assert_called_once_with(request_id)



def test_update_service_updates_service_details_successfully():
    repository = Mock(spec=MaintenanceServiceRepository)

    service = MaintenanceServiceService.__new__(MaintenanceServiceService)
    service.maintenance_service_repository = repository

    service_id = uuid4()

    existing_service = MaintenanceService(
        id=service_id,
        maintenance_request_id=uuid4(),
        name="Brake Pad Replacement",
        description="Replace worn brake pads",
        cost=75000,
        is_additional=True,
    )

    updated_service = MaintenanceService(
        id=service_id,
        maintenance_request_id=existing_service.maintenance_request_id,
        name="Brake Pad Replacement",
        description="Replace front and rear brake pads",
        cost=100000,
        is_additional=True,
    )

    repository.find_by_id.return_value = existing_service
    repository.update.return_value = updated_service

    result = service.update_service(updated_service)

    assert result == updated_service
    assert result.description == "Replace front and rear brake pads"
    assert result.cost == 100000
    repository.find_by_id.assert_called_once_with(service_id)
    repository.update.assert_called_once_with(updated_service)


