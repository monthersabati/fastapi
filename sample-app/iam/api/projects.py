from fastapi import Request

from iam import conf
from iam.api import models
from iam.api import routes
from iam.core import utils
from iam.core import keystone
from iam.api.models import ResponseModel

TAGS = ['projects']


@routes.v1_r.get("/projects", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def get_projects(request: Request):
    """
    Retrieve a list of projects.

    - **Auth Required**: Yes
    """
    projects = await keystone.tenant_list(request)
    return [x.to_dict() for x in projects]

@routes.v1_r.post("/projects", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def create_project(request: Request, inputs: models.CreateProjectModel):
    """
    Create a project.

    - **Auth Required**: Yes
    - **Request Body**:
        ```
        name: The name of project.
        description: (optional) The description of project.
        enabled: (optional) To enable/disable the project.
        ```
    - **Returns**: The created project.
    """
    project = await keystone.tenant_create(request, **inputs.model_dump())
    return project.to_dict()

@routes.v1_r.get("/projects/{project_id}", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def get_project(request: Request, project_id: str):
    """
    Retrieve a project.

    - **Auth Required**: Yes
    - **Request Path Args**:
        ```
        project_id: The id of project.
        ```
    - **Returns**: The information of given project.
    """
    project = await keystone.tenant_get(request, project_id)
    return project.to_dict()

@routes.v1_r.post("/projects/{project_id}", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def update_project(request: Request, project_id: str, inputs: models.UpdateProjectModel):
    """
    Update a project.

    - **Auth Required**: Yes
    - **Request Path Args**:
        ```
        project_id: The id of project.
        ```
    - **Request Body**:
        ```
        name: (optional) The name of project.
        description: (optional) The description of project.
        enabled: (optional) To enable/disable the project.
        ```
    """
    await keystone.tenant_update(request, project_id, **inputs.model_dump())

@routes.v1_r.delete("/projects/{project_id}", tags=TAGS, response_model=ResponseModel)
@utils.handle_response()
async def delete_project(request: Request, project_id: str):
    """
    Delete a project.

    - **Auth Required**: Yes
    - **Request Path Args**:
        ```
        project_id: The id of project.
        ```
    """
    await keystone.tenant_delete(request, project_id)
