import uuid

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UUID, UniqueConstraint, func

from .base import Base
from .user_model import User


class File(Base):
    __tablename__ = 'file'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    path_dir = Column(String(200), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    size = Column(Integer, nullable=False)
    is_downloadable = Column(Boolean, default=True, nullable=False)
    user_id = Column(UUID, ForeignKey(User.id, ondelete='CASCADE'), nullable=False, )

    UniqueConstraint(name, path_dir, user_id, name='user_file_path')

    def __repr__(self):
        return f'File({str(self.id)[:5]}|{self.name}|{self.updated_at}|{self.size}|user:{str(self.user_id)[:5]})'
