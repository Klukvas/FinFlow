from __future__ import annotations

from typing import Dict, Any
import redis

from ..config import settings


def enrich_jwt_claims(base_claims: Dict[str, Any], *, plan_code: str, expires_at_iso: str | None, version: int) -> Dict[str, Any]:
    claims = dict(base_claims)
    claims["sub_level"] = plan_code
    if expires_at_iso:
        claims["sub_exp"] = expires_at_iso
    claims["ents_version"] = version
    return claims


class JtiDenyList:
    def __init__(self) -> None:
        self.redis = redis.from_url(settings.redis_url, decode_responses=True)

    def deny(self, jti: str, ttl_seconds: int) -> None:
        # store a marker for JTI, expiring after ttl
        self.redis.setex(f"denylist:jti:{jti}", ttl_seconds, "1")

    def is_denied(self, jti: str) -> bool:
        return self.redis.get(f"denylist:jti:{jti}") == "1"


