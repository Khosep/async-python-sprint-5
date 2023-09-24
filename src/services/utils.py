import time
from functools import lru_cache

import bcrypt
from aiopath import AsyncPath
from fastapi import UploadFile

from src.core.config import AppSettings, app_settings


async def create_hashed_password(password: str) -> str:
    hashed_password_b: bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    hashed_password: str = hashed_password_b.decode('utf-8')
    return hashed_password


async def check_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def form_message(*, info: str, status: str, service: str | None = None) -> dict:
    if service is None:
        return dict(status=status, info=info)
    return dict(service=service, status=status, info=info)


async def create_dir_if_not_exists(path: AsyncPath) -> None:
    await path.parent.mkdir(parents=True, exist_ok=True)


async def get_absolute_file_path(username: str, filename: str, path_dir: str | None) -> AsyncPath:
    storage_path = app_settings.storage_path
    if path_dir:
        file_path = AsyncPath(storage_path, username, path_dir, filename)
    else:
        file_path = AsyncPath(storage_path, username, filename)
    return file_path


async def write_file(file: UploadFile, file_path: AsyncPath, is_file_path_exists: bool):
    if not is_file_path_exists:
        await create_dir_if_not_exists(file_path)
    async with file_path.open(mode='wb') as f:
        content = await file.read()
        await f.write(content)


async def file_chunk_generator(file_path: AsyncPath):
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(200 * 1024)
            if not chunk:
                break
            yield chunk


def execution_time(func):
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return result, execution_time

    return wrapper


# TODO to use or not to use?
@lru_cache()
def get_settings():
    return AppSettings()
