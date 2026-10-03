from uuid import UUID

from sqlmodel import Session, select

from app.models.pending_registration import PendingRegistration


class PendingRegistrationRepository:

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        registration: PendingRegistration,
    ) -> PendingRegistration:
        self.session.add(registration)
        self.session.commit()
        self.session.refresh(registration)
        return registration

    def find_by_email(
        self,
        email: str,
    ) -> PendingRegistration | None:
        statement = select(PendingRegistration).where(
            PendingRegistration.email == email
        )
        return self.session.exec(statement).first()

    def find_by_token(
        self,
        token: str,
    ) -> PendingRegistration | None:
        statement = select(PendingRegistration).where(
            PendingRegistration.verification_token == token
        )
        return self.session.exec(statement).first()

    def find_by_id(
        self,
        registration_id: UUID,
    ) -> PendingRegistration | None:
        statement = select(PendingRegistration).where(
            PendingRegistration.id == registration_id
        )
        return self.session.exec(statement).first()

    def delete(
        self,
        registration: PendingRegistration,
    ) -> None:
        self.session.delete(registration)
        self.session.commit()