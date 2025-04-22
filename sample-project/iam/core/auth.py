import json
import base64
from async_lru import alru_cache
from fastapi import Request, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader

from iam import conf
from iam.core.keystone import token_validate


class User:
    def __init__(self, token_info, **kwargs):
        self.id = token_info.get('user', {}).get('id')
        self.username = token_info.get('user', {}).get('name')
        self.project_id = token_info.get('project', {}).get('id')
        self.project_name = token_info.get('project', {}).get('name')
        self.roles = token_info.get('roles', [])
        self.token = token_info.get('token')

    @property
    def is_authenticated(self) -> bool:
        return True
    
    def to_dict(self):
        return {
            "user": {
                'id': self.id,
                'name': self.username,
            },
            "project": {
                'id': self.project_id,
                'name': self.project_name,
            },
            "roles": self.roles,
            "token": self.token,
            "is_authenticated": self.is_authenticated
        }


async def validate_token(
        request: Request,
        token: str = Depends(APIKeyHeader(name=conf.AUTHENTICATION_HEADER, auto_error=False)),
        identity: str = Depends(APIKeyHeader(name=conf.IDENTITY_HEADER, auto_error=False)),
):
    token_info = None
    try:
        token_info = json.loads(base64.b64decode(identity.encode()))
    except:
        token_info = await token_validate(token)
    if not token_info:
        raise HTTPException(status_code=401, detail=f"Invalid or missing {conf.AUTHENTICATION_HEADER}")
    request.state.user = User(token_info)
    return token_info
