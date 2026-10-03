from sqlalchemy.orm import Session

from app.models.maintenance_service import MaintenanceService
from app.exceptions.app_exception import AppException
from app.repositories.maintenance_service_repository import MaintenanceServiceRepository



class MaintenanceServiceService:

    def __init__(self, session: Session):
        self.maintenance_service_repository = MaintenanceServiceRepository(session)

    def create_service(self, maintenance_service: MaintenanceService):
        return self.maintenance_service_repository.create(maintenance_service)


    def get_service_by_id(self, service_id):
        service = self.maintenance_service_repository.find_by_id(service_id)

        if service is None:
            raise AppException("Maintenance service not found")

        return service

    def get_services_by_request_id(self, request_id):
        return self.maintenance_service_repository.find_by_request_id(request_id)

    def update_service(self, maintenance_service: MaintenanceService):
        existing_service = self.maintenance_service_repository.find_by_id(
            maintenance_service.id
        )

        if existing_service is None:
            raise AppException("Maintenance service not found")

        return self.maintenance_service_repository.update(maintenance_service)

