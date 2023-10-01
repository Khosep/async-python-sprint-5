from pathlib import Path

import pytest
from fastapi import status
from httpx import AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


from src.core.config import app_settings
from src.main import app
from src.models.file_model import File as FileModel
from src.models.user_model import User as UserModel
from src.schemas.file_schema import FileOut, FileInfo
from src.schemas.token_schema import Token
from src.schemas.user_schema import UserOut


@pytest.mark.asyncio
async def test_get_ping(ac: AsyncClient) -> None:
    """GET /ping"""
    response = await ac.get(app.url_path_for('get_ping'))
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(data, dict)
    assert 'info' in data


@pytest.mark.asyncio
async def test_register_user(ac: AsyncClient, db: AsyncSession) -> None:
    """POST /register"""
    user_in = dict(username='Darth', email='Darth@example.com', password='Pa1234ssword!')
    response = await ac.post(app.url_path_for('register_user'), json=user_in)
    data = response.json()

    result = await db.execute(select(UserModel).where(UserModel.username == user_in['username']))
    user_obj = result.scalar_one_or_none()

    assert response.status_code == status.HTTP_201_CREATED, f'Wrong status: {response.status_code}'
    assert 'hashed_password' not in data, 'There is field <hashed_password> in the response'
    assert data['username'] == user_in['username'], 'There is no field <username> in the response OR wrong value'
    assert data['email'] == user_in['email'].lower(), 'There is no field <email> in the response OR wrong value'
    assert user_obj.username == user_in['username']
    assert user_obj.email == user_in['email'].lower()
    assert len(data) == len(UserOut.model_fields), 'Invalid message len'


@pytest.mark.asyncio
async def test_login_for_access_token(ac: AsyncClient, db: AsyncSession) -> None:
    """POST /auth"""
    login_in = dict(username='Darth', password='Pa1234ssword!')
    response = await ac.post(app.url_path_for('login_for_access_token'), data=login_in)
    data = response.json()

    result = await db.execute(select(UserModel).where(UserModel.username == login_in['username']))
    user_obj = result.scalar_one_or_none()

    access_token = data['access_token']
    payload = jwt.decode(access_token, app_settings.token_secret_key,
                         algorithms=app_settings.token_jwt_algorithm)
    username_from_token = payload.get("sub")

    assert response.status_code == status.HTTP_200_OK, f'Wrong status: {response.status_code}'
    assert user_obj.username == username_from_token
    assert 'access_token' in data, 'There is no field <access_token> in the response'
    assert data['token_type'] == 'bearer', 'There is no field <token_type> in the response OR wrong value'
    assert username_from_token == login_in['username'], 'Wrong username'
    assert len(data) == len(Token.model_fields), 'Invalid message len'


@pytest.mark.asyncio
async def test_upload_new_file(auth_ac: AsyncClient, db: AsyncSession, test_file, mock_storage_path) -> None:
    """POST /files/upload"""
    file_in = {'file': (test_file.filename, test_file.file)}
    params = {'path_dir': 'test_dir1/test_dir2'}
    filename = test_file.filename

    response = await auth_ac.post(app.url_path_for('upload_file'), files=file_in, params=params)
    data = response.json()

    _, token = auth_ac.headers['authorization'].split()
    payload = jwt.decode(token, app_settings.token_secret_key,
                         algorithms=app_settings.token_jwt_algorithm)
    username_from_token = payload.get("sub")
    file_path = Path(mock_storage_path, username_from_token, params['path_dir'], filename)
    result = await db.execute(select(FileModel).where(FileModel.name == filename))
    file_obj = result.scalar_one_or_none()

    global test_file_id  # for tests below
    test_file_id = file_obj.id

    assert response.status_code == status.HTTP_201_CREATED, f'Wrong status: {response.status_code}'
    assert file_path.exists(), 'There is no such path'
    assert 'updated_at' in data, 'There is no field <updated_at> in the response'
    assert data['name'] == filename, 'There is no field <name> in the response OR wrong value'
    assert file_obj.name == test_file.filename
    assert len(data) == len(FileOut.model_fields), 'Invalid message len'


@pytest.mark.asyncio
async def test_upload_existing_file(auth_ac: AsyncClient, db: AsyncSession, test_file,
                                    mock_storage_path) -> None:
    """POST /files/upload for existing file"""
    file_in = {'file': (test_file.filename, test_file.file)}
    params = {'path_dir': 'test_dir1/test_dir2'}
    filename = test_file.filename

    response = await auth_ac.post(app.url_path_for('upload_file'), files=file_in, params=params)
    data = response.json()

    _, token = auth_ac.headers['authorization'].split()
    payload = jwt.decode(token, app_settings.token_secret_key,
                         algorithms=app_settings.token_jwt_algorithm)
    username_from_token = payload.get("sub")
    file_path = Path(mock_storage_path, username_from_token, params['path_dir'], filename)
    result = await db.execute(select(FileModel).where(FileModel.name == filename))
    file_obj = result.scalar_one_or_none()

    assert response.status_code == status.HTTP_201_CREATED, f'Wrong status: {response.status_code}'
    assert file_path.exists(), 'There is no such path'
    assert 'updated_at' in data, 'There is no field <updated_at> in the response'
    assert data['name'] == filename, 'There is no field <name> in the response OR wrong value'
    assert file_obj.name == test_file.filename
    assert len(data) == len(FileOut.model_fields), 'Invalid message len'
    assert file_obj.updated_at > file_obj.created_at


@pytest.mark.asyncio
async def test_download_file_by_path(auth_ac: AsyncClient, test_file, mock_storage_path) -> None:
    """GET /files/download by filename (and path_dir - optional)"""
    file_original_content = test_file.file.read().decode('utf-8')
    filename = test_file.filename
    params = {'filename': filename, 'path_dir': 'test_dir1/test_dir2'}

    response = await auth_ac.get(app.url_path_for('download_file'), params=params)

    assert response.status_code == status.HTTP_200_OK, f'Wrong status: {response.status_code}'
    assert file_original_content == response.text


@pytest.mark.asyncio
async def test_download_file_by_file_id(auth_ac: AsyncClient, test_file, mock_storage_path) -> None:
    """GET /files/download by file_id"""
    file_original_content = test_file.file.read().decode('utf-8')
    params = {'file_id': test_file_id}

    response = await auth_ac.get(app.url_path_for('download_file'), params=params)

    assert response.status_code == status.HTTP_200_OK, f'Wrong status: {response.status_code}'
    assert file_original_content == response.text


@pytest.mark.asyncio
async def test_download_file_by_invalid_file_id(auth_ac: AsyncClient, test_file, mock_storage_path) -> None:
    """GET /files/download by file_id"""
    params = {'file_id': f'{test_file_id}00000'}

    response = await auth_ac.get(app.url_path_for('download_file'), params=params)
    data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST, f'Wrong status: {response.status_code}'
    assert data['detail'][:15] == 'Invalid file_id'


@pytest.mark.asyncio
async def test_get_info(auth_ac: AsyncClient, file_rows_in_db) -> None:
    """GET /files/"""
    response = await auth_ac.get(app.url_path_for('get_info'))
    data = response.json()

    assert response.status_code == status.HTTP_200_OK, f'Wrong status: {response.status_code}'
    assert len(data) == len(FileInfo.model_fields), 'Invalid message len'
    assert isinstance(data['files'], list)
    assert len(data['files']) == 6
