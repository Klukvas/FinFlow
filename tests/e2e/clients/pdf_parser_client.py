"""API client for pdf_parser_service (port 8007)."""
from __future__ import annotations

import httpx
from typing import Optional
from tests.e2e.clients.base_client import BaseApiClient
from tests.e2e.models.responses import ApiResponse


class PdfParserApiClient(BaseApiClient):

    def __init__(self, base_url: str = "http://localhost:8007") -> None:
        super().__init__(base_url)

    async def get_supported_banks(self) -> ApiResponse:
        resp = await self._get("/pdf/supported-banks")
        return self._parse(resp)

    async def get_languages(self, bank_name: str) -> ApiResponse:
        resp = await self._get(f"/pdf/languages/{bank_name}")
        return self._parse(resp)

    async def pdf_health(self) -> ApiResponse:
        resp = await self._get("/pdf/health")
        return self._parse(resp)

    async def parse_pdf(
        self,
        file_content: bytes,
        filename: str = "test.pdf",
        content_type: str = "application/pdf",
        bank_type: Optional[str] = None,
        language: str = "en",
    ) -> ApiResponse:
        """Upload and parse a PDF/XLSX/CSV file."""
        headers = self._build_headers()
        # Remove Content-Type — httpx sets multipart boundary automatically
        headers.pop("Content-Type", None)

        files = {"file": (filename, file_content, content_type)}
        data: dict[str, str] = {"language": language}
        if bank_type:
            data["bank_type"] = bank_type

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{self._base_url}/pdf/parse",
                files=files,
                data=data,
                headers=headers,
            )
        return self._parse(resp)
