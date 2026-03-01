from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from shared.geoip.reader import geoip_reader
from shared.logging.logging_utils import country_code_var


def _extract_client_ip(request: Request) -> str | None:
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return None


class GeoIPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        ip = _extract_client_ip(request)
        country_code = geoip_reader.lookup(ip) if ip else None
        token = country_code_var.set(country_code)
        request.state.country_code = country_code
        try:
            response = await call_next(request)
        finally:
            country_code_var.reset(token)
        return response
