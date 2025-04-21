from fastapi import Request

from iam import conf
from iam.api import models
from iam.api import routes
from iam.core import utils
from iam.core import keystone
from iam.api.models import ResponseModel

TAGS = ['groups']


@routes.v1_r.get("/groups", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def get_groups(request: Request):
    """
    Retrieve a list of groups.

    - **Auth Required**: Yes
    """
    groups = await keystone.group_list(request)
    return [x.to_dict() for x in groups]

@routes.v1_r.post("/groups", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def create_group(request: Request, inputs: models.CreateGroupModel):
    """
    Create a group.

    - **Auth Required**: Yes
    - **Request Body**:
        ```
        name: The name of group.
        description: (optional) The description of group.
        ```
    - **Returns**: The created group.
    """
    group = await keystone.group_create(request, **inputs.model_dump())
    return group.to_dict()

@routes.v1_r.get("/groups/{group_id}", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def get_group(request: Request, group_id: str):
    """
    Retrieve a group.

    - **Auth Required**: Yes
    - **Request Path Args**:
        ```
        group_id: The id of group.
        ```
    - **Returns**: The information of given group.
    """
    group = await keystone.group_get(request, group_id)
    return group.to_dict()

@routes.v1_r.post("/groups/{group_id}", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def update_group(request: Request, group_id: str, inputs: models.UpdateGroupModel):
    """
    Update a group.

    - **Auth Required**: Yes
    - **Request Path Args**:
        ```
        group_id: The id of group.
        ```
    - **Request Body**:
        ```
        name: (optional) The name of group.
        description: (optional) The description of group.
        ```
    """
    await keystone.group_update(request, group_id, **inputs.model_dump())

@routes.v1_r.delete("/groups/{group_id}", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def delete_group(request: Request, group_id: str):
    """
    Delete a group.

    - **Auth Required**: Yes
    - **Request Path Args**:
        ```
        group_id: The id of group.
        ```
    """
    await keystone.group_delete(request, group_id)

@routes.v1_r.get("/groups/{group_id}/users", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def get_group_users(request: Request, group_id: str):
    """
    Retrieve a group.

    - **Auth Required**: Yes
    - **Request Path Args**:
        ```
        group_id: The id of group.
        ```
    - **Returns**: A list of users of the given group.
    """
    group_users = await keystone.user_list(request, group=group_id)
    return [x.to_dict() for x in group_users]

@routes.v1_r.post("/groups/{group_id}/users", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def update_group_users(request: Request, group_id: str, inputs: models.UpdateGroupUsersModel):
    """
    Update a group.

    - **Auth Required**: Yes
    - **Request Path Args**:
        ```
        group_id: The id of group.
        ```
    - **Request Body**:
        ```
        action: (optional) add/remove.
        user: The description of group.
        ```
    """
    if inputs.action == 'add':
        await keystone.group_add_user(request, group_id, inputs.user)
    elif inputs.action == 'remove':
        await keystone.group_remove_user(request, group_id, inputs.user)
