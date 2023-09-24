from typing import Any, Annotated, Type

from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from src.core.config import PaginationParams
from src.db.db import get_session
from src.models.file_model import File as FileModel
from src.schemas.file_schema import FileOut, FileInfo
from src.schemas.user_schema import UserInDB
from src.services.auth import get_current_active_user
from src.services.file_service import file_service
from .base import TAG_FILE

router = APIRouter()


@router.post('/upload', response_model=FileOut, status_code=status.HTTP_201_CREATED, tags=[TAG_FILE])
async def upload_file(
        *,
        db: AsyncSession = Depends(get_session),
        current_user: Annotated[UserInDB, Depends(get_current_active_user)],
        file: UploadFile = File(...),
        path_dir: str | None = None
) -> FileModel:
    file_model_obj = await file_service.upload_file_(db=db, user=current_user, file=file, path_dir=path_dir)
    return file_model_obj


@router.get('/download', tags=[TAG_FILE])
async def download_file(
        *,
        db: AsyncSession = Depends(get_session),
        current_user: Annotated[UserInDB, Depends(get_current_active_user)],
        filename: Annotated[str | None, Query(min_length=1)] = None,
        path_dir: str | None = None,
        file_id: str | None = None
) -> Type[Response]:
    if not filename and not file_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='No path or file_id provided')
    response = await file_service.download_file(db=db,
                                                user=current_user,
                                                filename=filename,
                                                path_dir=path_dir,
                                                file_id=file_id
                                                )
    return response


@router.get('/', response_model=FileInfo, tags=[TAG_FILE])
async def get_info(
        *,
        db: AsyncSession = Depends(get_session),
        current_user: Annotated[UserInDB, Depends(get_current_active_user)],
        page_params: Annotated[PaginationParams, Depends(PaginationParams)],
) -> dict[str, Any]:
    file_list = await file_service.get_list_info(db=db, user_id=current_user.id, page_params=page_params)
    return file_list
