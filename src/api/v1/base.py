from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from src.core.config import app_settings

router = APIRouter()

TAG_SERVICE = 'Service'
TAG_LINK = 'Link'
TAG_USER = 'User'
TAG_AUTH = 'Auth'
TAG_FILE = 'File'


@router.get('/', description='Redirect to doc page', tags=[TAG_SERVICE])
async def root_handler():
    return RedirectResponse(app_settings.docs_url)
