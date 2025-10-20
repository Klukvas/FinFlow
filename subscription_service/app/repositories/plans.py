from __future__ import annotations

from sqlalchemy.orm import Session
from typing import List

from ..models import Plan


class PlanRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_active(self) -> List[Plan]:
        return self.db.query(Plan).filter(Plan.is_active.is_(True)).order_by(Plan.code.asc()).all()

    def get_by_code(self, code: str) -> Plan | None:
        return self.db.query(Plan).filter(Plan.code == code).first()


