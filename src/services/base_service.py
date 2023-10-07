import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.base import Base


class Repository(ABC):
    @abstractmethod
    async def check_db_health(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def create(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def create_multi(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def get(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def get_multi(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def update(self, *args, **kwargs):
        raise NotImplementedError


ModelType = TypeVar('ModelType', bound=Base)
DBFieldsType = TypeVar('DBFieldsType', bound=BaseModel)
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)


class SQLAlchemyRepository(Repository, Generic[ModelType, DBFieldsType, CreateSchemaType, UpdateSchemaType]):
    model = None

    async def check_db_health(self, db: AsyncSession) -> bool:
        try:
            stmt = select(self.model)
            result = await db.execute(statement=stmt)
            return bool(result)
        except Exception as e:
            logging.error(e)
            return False

    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def create_multi(self, db: AsyncSession, obj_in_list: List[CreateSchemaType]) -> List[ModelType]:
        obj_data = jsonable_encoder(obj_in_list)
        db_objs = [self.model(**obj) for obj in obj_data]
        db.add_all(db_objs)
        await db.commit()
        for obj in db_objs:
            await db.refresh(obj)
        return db_objs

    async def get(self, db: AsyncSession, db_obj: DBFieldsType) -> Optional[ModelType]:
        db_obj = db_obj.model_dump()
        conditions = [getattr(self.model, k) == v for k, v in db_obj.items()]
        stmt = select(self.model).where(and_(*conditions))
        result = await db.execute(statement=stmt)
        return result.scalar_one_or_none()

    async def get_multi(self, db: AsyncSession, obj: dict, limit: int, offset: int) -> list[ModelType]:
        conditions = [getattr(self.model, k) == v for k, v in obj.items()]
        stmt = select(self.model).where(and_(*conditions)).offset(offset).limit(limit)
        results = await db.execute(statement=stmt)
        return results.scalars().all()

    async def update(self, db: AsyncSession, db_obj: ModelType, obj_in: UpdateSchemaType | Dict[str, Any]
                     ) -> Optional[ModelType]:
        obj_in = obj_in.model_dump()
        stmt = update(self.model).where(self.model.id == str(db_obj.id)).values(**obj_in)
        await db.execute(stmt)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
