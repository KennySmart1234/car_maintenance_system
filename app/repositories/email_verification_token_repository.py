
from uuid import UUID
from sqlmodel import Session, select

from app.models.email_verification_token import EmailVerificationToken


class EmailVerificationTokenRepository:

    def __init__(self, session: Session):
        self.session = session

    def create(self, token: EmailVerificationToken) -> EmailVerificationToken:
        self.session.add(token)
        self.session.commit()
        self.session.refresh(token)

        return token


    def find_by_token(self, token: str) -> EmailVerificationToken | None:
        statement = select(EmailVerificationToken).where(EmailVerificationToken.token == token)
        return self.session.exec(statement).first()


    def find_by_user_id(self, user_id: UUID) -> list[EmailVerificationToken]:
        statement = select(EmailVerificationToken).where(EmailVerificationToken.user_id == user_id)
        return list(self.session.exec(statement).all())


    def update(self, token: EmailVerificationToken) -> EmailVerificationToken:
        self.session.add(token)
        self.session.commit()
        self.session.refresh(token)

        return token