import logging
import logging.config
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status as http_status
from fastapi.openapi.utils import get_openapi

from iam import conf
from iam.api import routes
from iam.api import models
from iam import middlewares

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "[%(asctime)s] %(levelname)s %(name)s [%(message)s]",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        }
    },

    "loggers": {
        # 👇 Your custom logger
        conf.APP_NAME: {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        # 👇 Override uvicorn.access to suppress it
        "uvicorn.access": {
            "handlers": [],
            "level": "WARNING",  # or "CRITICAL" to fully hide it
            "propagate": False,
        },
        # Optional: Keep uvicorn.error
        "uvicorn.error": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)

app = FastAPI(swagger_ui_parameters={
    'deepLinking': True,
    'persistAuthorization': True,
    'displayOperationId': False,
    'defaultModelsExpandDepth': -1,
    'defaultModelExpandDepth': 3,
    'defaultModelRendering': 'model',
    'displayRequestDuration': True,
    'docExpansion': 'none',
    'filter': True,
    'showExtensions': True,
    'showCommonExtensions': True,
})

app.add_middleware(middlewares.RequestIDMiddleware)
app.add_middleware(middlewares.LoggingMiddleware)

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=models.ResponseModel(
            success=False,
            message=str(exc),
        ).model_dump()
    )

# v1
app.include_router(routes.v1_pr)
app.include_router(routes.v1_r)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="IAM",
        version="1.0.0",
        description="",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "AuthToken": {
            "type": "apiKey",
            "in": "header",
            "name": conf.AUTHENTICATION_HEADER
        },
        "Identity": {
            "type": "apiKey",
            "in": "header",
            "name": conf.IDENTITY_HEADER
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"AbrimentToken": []}, {"Identity": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == '__main__':
    # Run from the root of project 
    import os
    def get_import_string(app_variable_name: str = "app") -> str:
        current_path = os.path.abspath(__file__)
        project_root_path = os.path.join(current_path, '..', '..')
        rel_path = os.path.relpath(current_path, project_root_path)
        module_path = rel_path.replace(".py", "").replace(os.sep, ".")
        return f"{module_path}:{app_variable_name}"
    uvicorn.run(
        app=get_import_string("app"),
        host=conf.APP_HOST, port=conf.APP_PORT,
        reload=conf.DEBUG, workers=conf.WORKERS,
        access_log=False,
    )
