from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FileBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    path_dir: str | None
    size: int


class FileCreate(FileBase):
    user_id: UUID


class FileInDB(FileBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_downloadable: bool
    user_id: UUID


class FileOut(FileBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_downloadable: bool


class FileUpdateSize(BaseModel):
    size: int


class FileIn(BaseModel):
    name: str
    path_dir: str
    user_id: UUID


class FileID(BaseModel):
    id: UUID


class FileInfo(BaseModel):
    user_id: UUID
    files: list[FileOut]
