import uuid

from sqlalchemy import Column, String, Boolean, UUID
from sqlalchemy_utils import EmailType

from .base import Base


class User(Base):
    __tablename__ = 'user'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(35), unique=True, nullable=False)
    hashed_password = Column(String(100), unique=True, nullable=False)
    email = Column(EmailType, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f'User({self.id} {self.username} {self.email}: {self.is_active})'
