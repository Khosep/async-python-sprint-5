from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.db import get_session
from src.services.health_service import health_service
from .base import TAG_SERVICE

router = APIRouter()


@router.get('/ping', tags=[TAG_SERVICE])
async def get_ping(
        *,
        db: Annotated[AsyncSession, Depends(get_session)],
) -> ORJSONResponse:
    """Database health check"""
    data: dict[str, str] = await health_service.get_ping(db=db)
    is_time = data['info'][0].isdigit()
    status_code = status.HTTP_200_OK if is_time else status.HTTP_503_SERVICE_UNAVAILABLE
    return ORJSONResponse(content=data, status_code=status_code)
