from typing import Type

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.base_service import SQLAlchemyRepository, Repository
from src.services.utils import form_message, execution_time


class HealthRepository(SQLAlchemyRepository):
    model = None


class HealthService:
    def __init__(self, repo: Type[Repository]):
        self.repo = repo()

    async def get_ping(self, db: AsyncSession) -> dict[str, str]:
        service = 'db'
        result, execution_time = await self._get_status_db(db=db)
        if result:
            return form_message(service=service, status='success', info=f'{execution_time:.4f} s')
        return form_message(service=service, status='error', info='Database is currently unavailable')

    @execution_time
    async def _get_status_db(self, db: AsyncSession) -> bool:
        result = await self.repo.check_db_health(db=db)
        return result


health_service = HealthService(HealthRepository)
