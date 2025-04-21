from fastapi import Request

from iam import conf
from iam.api import models
from iam.api import routes
from iam.core import utils
from iam.core import keystone
from iam.api.models import ResponseModel

TAGS = ['users']


@routes.v1_r.get("/users", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def get_users(request: Request):
    """
    Retrieve a list of users.

    - **Auth Required**: Yes
    """
    users = await keystone.user_list(request)
    return [x.to_dict() for x in users]

@routes.v1_r.post("/users", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def create_user(request: Request, inputs: models.CreateUserModel):
    """
    Create a user.

    - **Auth Required**: Yes
    - **Request Body**:
        ```
        name: The name of user.
        password: The password of user.
        email: (optional) The email of user.
        description: (optional) The description of user.
        enabled: (optional) To enable/disable the user.
        ```
    - **Returns**: The created user.
    """
    user = await keystone.user_create(request, **inputs.model_dump())
    return user.to_dict()

@routes.v1_r.get("/users/{user_id}", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def get_user(request: Request, user_id: str):
    """
    Retrieve a user.

    - **Auth Required**: Yes
    - **Request Path Args**:
        ```
        user_id: The id of user.
        ```
    - **Returns**: The information of given user.
    """
    user = await keystone.user_get(request, user_id)
    return user.to_dict()

@routes.v1_r.post("/users/{user_id}", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def update_user(request: Request, user_id: str, inputs: models.UpdateUserModel):
    """
    Update a user.

    - **Auth Required**: Yes
    - **Request Path Args**:
        ```
        user_id: The id of user.
        ```
    - **Request Body**:
        ```
        name: (optional) The name of user.
        password: (optional) The password of user.
        email: (optional) The email of user.
        description: (optional) The description of user.
        enabled: (optional) To enable/disable the user.
        ```
    """
    await keystone.user_update(request, user_id, **inputs.model_dump())

@routes.v1_r.delete("/users/{user_id}", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def delete_user(request: Request, user_id: str):
    """
    Delete a user.

    - **Auth Required**: Yes
    - **Request Path Args**:
        ```
        user_id: The id of user.
        ```
    """
    await keystone.user_delete(request, user_id)
