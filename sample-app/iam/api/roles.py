from fastapi import Request

from iam import conf
from iam.api import models
from iam.api import routes
from iam.core import utils
from iam.core import keystone
from iam.api.models import ResponseModel

TAGS = ['roles']


@routes.v1_r.get("/roles", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def get_roles(request: Request):
    """
    Retrieve a list of roles.

    - **Auth Required**: Yes
    """
    roles = await keystone.role_list(request)
    return [x.to_dict() for x in roles]

@routes.v1_r.post("/roles", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def create_role(request: Request, inputs: models.CreateRoleModel):
    """
    Create a role.

    - **Auth Required**: Yes
    - **Request Body**:
        ```
        name: The name of role.
        ```
    - **Returns**: The created role.
    """
    role = await keystone.role_create(request, **inputs.model_dump())
    return role.to_dict()

@routes.v1_r.get("/roles/{role_id}", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def get_role(request: Request, role_id: str):
    """
    Retrieve a role.

    - **Auth Required**: Yes
    - **Request Path Args**:
        ```
        role_id: The id of role.
        ```
    - **Returns**: The information of given role.
    """
    role = await keystone.role_get(request, role_id)
    return role.to_dict()

@routes.v1_r.post("/roles/{role_id}", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def update_role(request: Request, role_id: str, inputs: models.UpdateRoleModel):
    """
    Update a role.

    - **Auth Required**: Yes
    - **Request Path Args**:
        ```
        role_id: The id of role.
        ```
    - **Request Body**:
        ```
        name: (optional) The name of role.
        ```
    """
    await keystone.role_update(request, role_id, **inputs.model_dump())

@routes.v1_r.delete("/roles/{role_id}", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def delete_role(request: Request, role_id: str):
    """
    Delete a role.

    - **Auth Required**: Yes
    - **Request Path Args**:
        ```
        role_id: The id of role.
        ```
    """
    await keystone.role_delete(request, role_id)

@routes.v1_r.get("/role-assignments", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def get_role_assignments(request: Request):
    """
    Retrieve a list of role assignments.

    - **Auth Required**: Yes
    """
    roles = await keystone.role_assignments_list(request, include_subtree=False)
    return [x.to_dict() for x in roles]

@routes.v1_r.post("/role-assignments", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def assign_role(request: Request, inputs: models.AssignRoleModel):
    """
    Assign a role to a user/group in a project.

    - **Auth Required**: Yes
    - **Request Body**:
        ```
        role: The id of role.
        user: (optional) The id of user.
        group: (optional) The id of group.
        project: The id of project.
        ```
    """
    await keystone.role_assignment_create(request, **inputs.model_dump())

@routes.v1_r.post("/role-assignments/delete", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def unassign_role(request: Request, inputs: models.UnassignRoleModel):
    """
    Unassign a role to a user/group in a project.

    - **Auth Required**: Yes
    - **Request Body**:
        ```
        role: The id of role.
        user: (optional) The id of user.
        group: (optional) The id of group.
        project: The id of project.
        ```
    """
    await keystone.role_assignment_delete(request, **inputs.model_dump())
    