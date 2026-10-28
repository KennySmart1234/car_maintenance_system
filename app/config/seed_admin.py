from app.config.settings import settings
from app.enums.user_role import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.config.password import hash_password


def seed_admin(session):
    user_repository = UserRepository(session)

    existing_admin = user_repository.find_by_email(settings.admin_email)

    if existing_admin is not None:
        return

    admin = User(
        first_name=settings.admin_first_name,
        last_name=settings.admin_last_name,
        email=settings.admin_email,
        phone="",
        password=hash_password(settings.admin_password),
        role=UserRole.WORKSHOP_ADMIN,
        email_verified=True,
    )

    user_repository.create(admin)