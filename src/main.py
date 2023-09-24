import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.api.v1 import base, user_api, health_api, file_api
from src.core.config import app_settings

app = FastAPI(
    # The name of the project to be displayed in the documentation
    title=app_settings.app_title,
    # Address where the interactive API documentation will be available
    docs_url=app_settings.docs_url,
    # Address where the raw OpenAPI JSON schema will be available
    openapi_url=app_settings.openapi_url,
    # If the JSON-serializer is not explicitly specified in the response,
    # the faster 'ORJSONResponse' will be used instead of the standard 'JSONResponse'
    default_response_class=ORJSONResponse,
)

app.include_router(base.router)
app.include_router(user_api.router, prefix=app_settings.prefix)
app.include_router(health_api.router, prefix=app_settings.prefix)
app.include_router(file_api.router, prefix=app_settings.prefix + '/files')

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=app_settings.project_host,
        port=app_settings.project_port,
        reload=True,
    )
