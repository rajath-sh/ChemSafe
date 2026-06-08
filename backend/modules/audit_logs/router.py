from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from core.dependencies import get_db, require_role
from core.enums import Role
from core.schemas import CurrentUser
from modules.audit_logs.schemas import AuditLogOut
from modules.audit_logs.repository import get_audit_log_repository
from modules.audit_logs.service import AuditLogService

router = APIRouter()

def get_audit_log_service(db=Depends(get_db)) -> AuditLogService:
    repo = get_audit_log_repository(db)
    return AuditLogService(repo)

@router.get("", response_model=List[AuditLogOut])
def list_audit_logs(
    entity_type: Optional[str] = None,
    user_id: Optional[str] = None,
    service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    """
    Retrieve read-only system audit logs.
    Restricted to Admins only.
    """
    return service.list_logs(entity_type, user_id)
