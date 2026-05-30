from sqlalchemy.orm import Session

from app.modules.admin.models import AdminAuditLog


class AdminRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_audit_log(self, audit_log: AdminAuditLog) -> AdminAuditLog:
        self.session.add(audit_log)
        self.session.flush()
        return audit_log
