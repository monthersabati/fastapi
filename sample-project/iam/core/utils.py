import json
import logging
from fastapi import Request
from functools import wraps
from fastapi.responses import JSONResponse

from iam import conf
from iam import exceptions
from iam.api.models import ResponseModel

logger = logging.getLogger(conf.APP_NAME)


def handle_response(**dkwargs):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                request: Request = next(
                    (arg for arg in args if isinstance(arg, Request)), 
                    kwargs.get("request", None)
                )

                if request:
                    if dkwargs.get("sensitive_fields"):
                        request.state.sensitive_fields = set(map(str.lower, dkwargs["sensitive_fields"]))
                
                data = await func(*args, **kwargs)
                response = ResponseModel(data=data)
            except Exception as e:
                parsed_exception = exceptions.parse_exception(e)
                log_data = {
                    'request_id': getattr(getattr(request, 'state', None), 'request_id', None),
                    'exception': str(e),
                    'traceback': parsed_exception.get("trace"),
                }
                logger.error(json.dumps(log_data))
                status_code = parsed_exception.get('status_code', 500)
                response = JSONResponse(
                    status_code=status_code,
                    content=ResponseModel(
                        success=False,
                        status_code=status_code,
                        message=parsed_exception.get('message'),
                    ).model_dump()
                )

            return response
        return wrapper
    return decorator
