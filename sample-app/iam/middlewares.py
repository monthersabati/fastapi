import time
import json
import uuid
import logging
from fastapi import Request
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware

from iam import conf

logger = logging.getLogger(conf.APP_NAME)

def mask_sensitive_fields(data, sensitive_fields=[]):
    if isinstance(data, dict):
        return {
            k: "*" if k.lower() in sensitive_fields else mask_sensitive_fields(v, sensitive_fields)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [mask_sensitive_fields(item, sensitive_fields) for item in data]
    return data

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Extract request details
        client_ip = request.headers.get("x-forwarded-for", request.client.host).split(",")[0].strip()
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        try:
            body = await request.json()
        except:
            body = None
        
        # Process request
        response = await call_next(request)

        route: APIRoute = request.scope.get("route")
        handler = getattr(route, "endpoint", None)

        handler_name = getattr(handler, '__name__') if handler else None
        handler_path = getattr(handler, '__module__') if handler else None
        body = mask_sensitive_fields(body, getattr(request.state, "sensitive_fields", set()))
        
        # Response info
        duration = round((time.time() - start_time) * 1000)  # in ms
        status_code = response.status_code

        user = getattr(request.state, 'user', None)
        log_data = {
            "request_id": getattr(request.state, 'request_id', None),
            "request": {
                "client_ip": client_ip,
                "method": method,
                "path": path,
                "query_params": query_params,
                "body": body,
            },
            "resposne": {
                "status_code": status_code,
                "duration_ms": duration,
            },
            "handler": {"name": handler_name, "path": handler_path},
            "user_id": getattr(user, "id", None),
            "project_id": getattr(user, "project_id", None),
        }

        logger.info(json.dumps(log_data))

        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Check if client passed a request ID, else generate one
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        
        # Save to request.state so it's accessible anywhere
        request.state.request_id = request_id

        # Add it to the response headers too (optional but awesome)
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response
