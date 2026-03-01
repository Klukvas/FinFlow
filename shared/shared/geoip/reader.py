import os
import logging
import threading
from typing import Optional

import geoip2.database
from geoip2.errors import AddressNotFoundError

logger = logging.getLogger(__name__)

GEOIP_DB_PATH = os.getenv("GEOIP_DB_PATH", "/app/data/GeoLite2-Country.mmdb")


class GeoIPReader:
    def __init__(self) -> None:
        self._reader: Optional[geoip2.database.Reader] = None
        self._init_attempted: bool = False
        self._lock = threading.Lock()

    def open(self, db_path: Optional[str] = None) -> None:
        path = db_path or GEOIP_DB_PATH
        self._init_attempted = True
        if not os.path.isfile(path):
            logger.warning("GeoIP database not found at %s — country detection disabled", path)
            return
        try:
            self._reader = geoip2.database.Reader(path)
            logger.info("GeoIP database loaded from %s", path)
        except Exception:
            logger.exception("Failed to open GeoIP database at %s", path)

    def lookup(self, ip: str) -> Optional[str]:
        if not self._init_attempted:
            with self._lock:
                if not self._init_attempted:
                    self.open()
        if not self._reader:
            return None
        try:
            response = self._reader.country(ip)
            return response.country.iso_code
        except (AddressNotFoundError, ValueError):
            return None

    def close(self) -> None:
        with self._lock:
            if self._reader:
                self._reader.close()
                self._reader = None


geoip_reader = GeoIPReader()
