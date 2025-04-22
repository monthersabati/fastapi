from fastapi import Request

from iam import conf
from iam.api import models
from iam.api import routes
from iam.core import keystone
from iam.core import utils
from iam.api.models import ResponseModel

TAGS = ['base']


@routes.v1_pr.post("/login", tags=TAGS, response_model=ResponseModel)
@utils.handle_response(sensitive_fields=["password"])
async def login(request: Request, inputs: models.LoginModel):
    """
    Retrieve a scoped and unscoped token.

    - **Auth Required**: No
    - **Request Body**:
        ```
        username: (optional) The username of user.
        password: (optional) The password of user.
        unscoped_token: (optional) The unscoped token with user info.
        project: (optional) The scope of token.
        ```
    - **Returns**: An scope and unscope token.
    """
    return await keystone.authenticate(**inputs.model_dump())

@routes.v1_pr.post("/token-validation", tags=TAGS, response_model=ResponseModel)
@utils.handle_response(sensitive_fields=["token"])
async def validate_token(request: Request, inputs: models.TokenValidationModel):
    """
    Validate auth token.

    - **Auth Required**: No
    - **Request Body**:
        ```
        token: The auth token.
        ```
    - **Returns**: Token info.
    """
    return await keystone.token_validate(inputs.token)
