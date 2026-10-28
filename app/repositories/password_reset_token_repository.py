from uuid import UUID

from sqlmodel import Session, select

from app.models.password_reset_token import PasswordResetToken


class PasswordResetTokenRepository:

    def __init__(self, session: Session):
        self.session = session

    def create(self, token: PasswordResetToken) -> PasswordResetToken:
        self.session.add(token)
        self.session.commit()
        self.session.refresh(token)

        return token

    def find_by_token(self, token: str) -> PasswordResetToken | None:
        statement = select(PasswordResetToken).where(
            PasswordResetToken.token == token
        )
        return self.session.exec(statement).first()

    def find_by_user_id(self, user_id: UUID) -> list[PasswordResetToken]:
        statement = select(PasswordResetToken).where(
            PasswordResetToken.user_id == user_id
        )
        return list(self.session.exec(statement).all())

    def update(self, token: PasswordResetToken) -> PasswordResetToken:
        self.session.add(token)
        self.session.commit()
        self.session.refresh(token)

        return token
