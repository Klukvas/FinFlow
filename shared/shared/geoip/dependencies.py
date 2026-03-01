from typing import Optional

from fastapi import Request


def get_country_code(request: Request) -> Optional[str]:
    return getattr(request.state, "country_code", None)
