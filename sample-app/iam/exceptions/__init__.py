import traceback
import keystoneauth1.exceptions.http
from starlette import status as http_status

KNOWN_EXCEPTIONS = [
    keystoneauth1.exceptions.http.HTTPClientError,
]

def ignore_trace(cls):
    KNOWN_EXCEPTIONS.append(cls)
    return cls

def parse_exception(e):
    status_code = http_status.HTTP_500_INTERNAL_SERVER_ERROR
    message = str(e)
    tb = None

    ignore_trace = next((et for et in KNOWN_EXCEPTIONS if isinstance(e, et)), None)
    if ignore_trace: ...
    else:
        tb = ' '.join([l.strip() for l in traceback.format_exc().splitlines() if l.strip()])
    
    if isinstance(e, keystoneauth1.exceptions.http.HTTPClientError):
        status_code = getattr(e, 'http_status', status_code)

    return {
        "status_code": status_code,
        "message": message,
        "trace": tb,
    }

@ignore_trace
class KeystoneAuthException(Exception):
    """Generic error class to identify and catch keystone auth errors."""
