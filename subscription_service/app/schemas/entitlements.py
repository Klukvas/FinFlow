from __future__ import annotations

from pydantic import BaseModel
from typing import Dict, Optional


class EntitlementsOut(BaseModel):
    user_id: str
    plan_code: str
    version: int
    entitlements: Dict[str, Dict[str, Optional[int]]]  # { feature_code: { enabled, limit_value } }


