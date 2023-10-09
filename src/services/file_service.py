import logging
from typing import Type, Any
from uuid import UUID

from aiopath import AsyncPath
from fastapi import UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import PaginationParams, app_settings
from src.exceptions import FileNotFoundException, ValidationException
from src.models.file_model import File as FileModel
from src.schemas.file_schema import FileCreate, FileUpdateSize, FileIn, FileInDB, FileID
from src.schemas.user_schema import UserInDB
from src.services.base_service import SQLAlchemyRepository, Repository
from src.services.utils import get_absolute_file_path, write_file, file_chunk_generator


class FileRepository(SQLAlchemyRepository):
    model = FileModel


class FileService:
    def __init__(self, repo: Type[Repository]):
        self.repo = repo()

    async def upload_file_(self, db: AsyncSession, user: UserInDB, file: UploadFile, path_dir: str | None) -> FileModel:
        path_dir = path_dir or ''
        file_path: AsyncPath = await get_absolute_file_path(user.username, file.filename, path_dir)
        is_file_path_exists = await file_path.exists()
        # If the file exists, it will be overwritten
        await write_file(file, file_path, is_file_path_exists)

        if is_file_path_exists:
            db_obj = FileIn(name=file.filename, path_dir=path_dir, user_id=user.id)
            file_obj = await self.repo.get(db=db, db_obj=db_obj)
            if file_obj:
                updated_file_model_obj = await self._update_file(db, file_obj)
                logging.info(f'"{file.filename}" updated')
                return updated_file_model_obj
            logging.warning(f'"{file.filename}" is in storage, but there is no record about it in the database')

        new_file_model_obj = await self._create_file(db, user, path_dir, file)
        logging.info(f'"{file.filename}" created')

        return new_file_model_obj

    async def download_file(self, db: AsyncSession,
                            user: UserInDB,
                            filename: str | None,
                            path_dir: str | None,
                            file_id: str | None
                            ) -> Any:
        if file_id:
            try:
                db_obj = FileID(id=file_id)
            except Exception as e:
                raise ValidationException(f'file_id:\n{e}')
            file_obj = await self.repo.get(db=db, db_obj=db_obj)
            filename = file_obj.name
            path_dir = file_obj.path_dir

        file_path = await get_absolute_file_path(user.username, filename, path_dir)

        if not await file_path.exists():
            raise FileNotFoundException

        file_stat = await file_path.stat()
        file_size = file_stat.st_size

        if file_size < app_settings.large_file_size:
            logging.info(f'FileResponse for {filename} (size:{file_size})')
            return FileResponse(file_path, filename=filename)

        logging.info(f'StreamingResponse for {filename} (size:{file_size})')
        headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
        return StreamingResponse(content=file_chunk_generator(file_path),
                                 media_type="application/octet-stream",
                                 headers=headers)

    async def get_list_info(self, db: AsyncSession, user_id: UUID, page_params: PaginationParams) -> dict[str, Any]:
        file_list = await self.repo.get_multi(db=db,
                                              obj=dict(user_id=user_id),
                                              limit=page_params.limit,
                                              offset=page_params.offset)
        file_dict = {'user_id': user_id, 'files': [FileInDB.model_validate(file).model_dump() for file in file_list]}
        return file_dict

    async def _update_file(self, db: AsyncSession, file_obj: FileModel) -> FileModel:
        """Change values of the fields (size and updated_at) for overwritten file"""

        obj_in = FileUpdateSize(size=file_obj.size)
        file_model_obj = await self.repo.update(db=db, db_obj=file_obj, obj_in=obj_in)

        return file_model_obj

    async def _create_file(self, db: AsyncSession, user: UserInDB, path_dir: str, file: UploadFile) -> FileModel:
        file_obj = FileCreate(name=file.filename, path_dir=path_dir, size=file.size, user_id=user.id)
        file_model_obj = await self.repo.create(db=db, obj_in=file_obj)
        return file_model_obj


file_service = FileService(FileRepository)
