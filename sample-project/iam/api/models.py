from enum import Enum
from pydantic import BaseModel
from typing import Optional, Generic, TypeVar

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    success: bool = True
    status_code: int = 200
    error_code: int = 0
    message: str = None
    data: Optional[T] = None


class LoginModel(BaseModel):
    username: str = None
    password: str = None
    unscoped_token: str = None
    project: str = None


class TokenValidationModel(BaseModel):
    token: str


class CreateProjectModel(BaseModel):
    name: str
    description: str = None
    enabled: bool = True


class UpdateProjectModel(BaseModel):
    name: str = None
    description: str = None
    enabled: bool = None


class CreateUserModel(BaseModel):
    name: str
    password: str
    email: str = None
    description: str = None
    enabled: bool = True


class UpdateUserModel(BaseModel):
    name: str = None
    password: str = None
    email: str = None
    description: str = None
    enabled: bool = True


class CreateGroupModel(BaseModel):
    name: str
    description: str = None


class UpdateGroupModel(BaseModel):
    name: str = None
    description: str = None


class UpdateGroupUsersModel(BaseModel):
    class UpdateGroupUsersAction(str, Enum):
        add = "add"
        remove = "remove"
    action: UpdateGroupUsersAction = UpdateGroupUsersAction.add
    user: str


class CreateRoleModel(BaseModel):
    name: str


class UpdateRoleModel(BaseModel):
    name: str = None


class AssignRoleModel(BaseModel):
    role: str
    user: str = None
    group: str = None
    project: str


class UnassignRoleModel(AssignRoleModel): ...
