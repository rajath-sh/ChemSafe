from fastapi import APIRouter, Depends
from typing import List

from core.dependencies import get_db, require_role
from core.enums import Role
from core.schemas import CurrentUser
from modules.users.schemas import UserCreate, UserUpdate, UserOut
from modules.users.repository import get_user_repository
from modules.users.service import UserService

router = APIRouter()

def get_user_service(db=Depends(get_db)) -> UserService:
    repo = get_user_repository(db)
    return UserService(repo)

@router.post("", response_model=UserOut)
def create_user(
    data: UserCreate, 
    service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    return service.create_user(data)

@router.get("", response_model=List[UserOut])
def list_users(
    service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    return service.list_users()

@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN, Role.STAFF, Role.VIEWER))
):
    return service.get_user(user_id)

@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    data: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    return service.update_user(user_id, data)
