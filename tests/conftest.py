import asyncio
import io
import logging
import random
import shutil
from pathlib import Path
from typing import AsyncGenerator

import asyncpg
import factory
import pytest
from asyncpg import InvalidCatalogNameError
from fastapi import UploadFile
from httpx import AsyncClient
from sqlalchemy import UUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from src.core.config import app_settings
from src.db.db import get_session
from src.main import app
from src.models.base import Base
from src.models.file_model import File as FileModel
from src.models.user_model import User as UserModel
from tests.settings import test_settings

TEST_URL = f'http://test'
TEST_STORAGE = 'test_storage'
TEST_CLIENT = dict(username='Yoda', password='Pa123ssword!', email='Yoda@example.com')


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def ac() -> AsyncGenerator[AsyncClient, None]:
    base_url = TEST_URL
    async with AsyncClient(app=app, base_url=base_url, follow_redirects=False) as async_client:
        yield async_client


class Prepare:
    def __init__(self, test_database_url=test_settings.dsn):
        self.test_dsn_connect = test_database_url.replace('ql+asyncpg', '')
        self.engine = create_async_engine(test_database_url)

    async def async_session(self) -> sessionmaker:
        # Create async session SQLAlchemy
        async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        logging.info('TEST async_session created')
        return async_session

    async def session(self) -> AsyncSession:
        async_session = await self.async_session()
        async with async_session() as session:
            def override_get_session():
                return session

            app.dependency_overrides[get_session] = override_get_session
            logging.info('TEST final session created')

            return session

    async def create_db(self) -> None:
        # connect to system db_name 'postgres' to somehow connect (in order to create test db)
        app_dsn_connect = app_settings.database_dsn.replace('ql+asyncpg', '')
        conn = await asyncpg.connect(app_dsn_connect)
        await conn.execute(f'CREATE DATABASE {test_settings.test_db_name};')
        logging.info(f'Database {test_settings.test_db_name} created')
        await conn.close()

    async def create_tables(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def is_database_exists(self) -> bool:
        try:
            conn = await asyncpg.connect(self.test_dsn_connect)

        except InvalidCatalogNameError:
            logging.error('InvalidCatalogNameError')
            return False
        except Exception as e:
            logging.error(e)
            return False
        else:
            await conn.close()
            logging.info(f'Database {test_settings.test_db_name} exists')
            return True


@pytest.fixture(autouse=True, scope='session')
async def db() -> AsyncGenerator[AsyncSession, None]:
    p = Prepare()
    try:
        if not await p.is_database_exists():
            logging.error('Database does not exist')
            await p.create_db()
        await p.drop_tables()
        await p.create_tables()
        session = await p.session()
        yield session
    finally:
        await p.engine.dispose()


@pytest.fixture(scope='session')
async def auth_ac(ac: AsyncClient, db: AsyncSession) -> None:
    user_in = TEST_CLIENT
    await ac.post(app.url_path_for('register_user'), json=user_in)
    user_in.pop('email')
    response = await ac.post(app.url_path_for('login_for_access_token'), data=user_in)
    data = response.json()
    access_token = data['access_token']
    ac.headers = {'Authorization': f'Bearer {access_token}'}
    yield ac


@pytest.fixture
async def get_user_id_test_client(db: AsyncSession) -> UUID:
    stmt = select(UserModel).where(UserModel.username == TEST_CLIENT['username'])
    result = await db.execute(statement=stmt)
    user_db = result.scalar_one_or_none()
    return user_db.id


@pytest.fixture(scope='session', autouse=True)
async def create_storage_path():
    storage_path = Path('tests/test_storage')
    storage_path.mkdir(exist_ok=True)

    yield storage_path

    shutil.rmtree(storage_path)


@pytest.fixture
async def test_file() -> UploadFile:
    content = b'Test file content'
    file_like = io.BytesIO(content)
    yield UploadFile(file=file_like, filename='test_file.txt')


@pytest.fixture
async def mock_storage_path(monkeypatch: pytest.MonkeyPatch) -> str:
    current_path = Path(__file__).parent.resolve()
    mock_test_storage_path = Path(current_path, TEST_STORAGE)
    mock_test_storage_path.mkdir(exist_ok=True)
    monkeypatch.setattr(app_settings, 'storage_path', mock_test_storage_path)
    yield mock_test_storage_path


class UserFactory(factory.Factory):
    class Meta:
        model = dict

    username = factory.Faker('user_name')
    email = factory.Faker('email')
    hashed_password = factory.Faker('password')


class FileFactory(factory.Factory):
    class Meta:
        model = dict

    name = factory.Faker('file_name')
    path_dir = factory.Faker('file_path')
    size = factory.Sequence(lambda n: random.randint(1, 1000000))


def random_user_data():
    return UserFactory()


def random_file_data():
    return FileFactory()


@pytest.fixture
async def user_rows_in_db(db: AsyncSession) -> list:
    user_ids = []
    for _ in range(3):
        user_data = random_user_data()
        db_obj = UserModel(**user_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        user_ids.append(db_obj.id)
    return user_ids


@pytest.fixture
async def file_rows_in_db(db: AsyncSession, user_rows_in_db: list, get_user_id_test_client):
    # create file rows for quantity
    for user_id in user_rows_in_db:
        file_data = random_file_data() | {'user_id': user_id}
        db_obj = FileModel(**file_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
    # create file rows for retrieving
    user_id = get_user_id_test_client
    for i in range(5):
        file_data = random_file_data() | {'user_id': user_id}
        file_data['name'] = 'test' + str(i) + '.txt'
        db_obj = FileModel(**file_data)
        db.add(db_obj)
        await db.commit()
