"""Tests for app/routers/webhook.py - Monobank webhook endpoints."""

import pytest
from fastapi.testclient import TestClient
from fastapi import status


class TestMonobankWebhookVerify:
    """Tests for GET /webhook/monobank"""

    def test_webhook_verify_returns_ok(self, client: TestClient):
        response = client.get("/webhook/monobank")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "ok"


class TestMonobankWebhookReceive:
    """Tests for POST /webhook/monobank"""

    def test_valid_webhook_payload(self, client: TestClient):
        payload = {
            "type": "StatementItem",
            "data": {
                "account": "acc123",
                "statementItem": {
                    "id": "tx1",
                    "time": 1700000000,
                    "description": "Payment",
                    "mcc": 5411,
                    "amount": -5000,
                    "operationAmount": -5000,
                    "currencyCode": 980,
                    "balance": 95000,
                },
            },
        }
        response = client.post("/webhook/monobank", json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "received"

    def test_invalid_payload_returns_invalid(self, client: TestClient):
        response = client.post(
            "/webhook/monobank",
            json={"invalid": "data"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "invalid"

    def test_empty_payload_returns_invalid(self, client: TestClient):
        response = client.post(
            "/webhook/monobank",
            content=b"{}",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "invalid"

    def test_non_json_payload_returns_invalid(self, client: TestClient):
        response = client.post(
            "/webhook/monobank",
            content=b"not json at all",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "invalid"

    def test_payload_missing_data_field(self, client: TestClient):
        response = client.post(
            "/webhook/monobank",
            json={"type": "StatementItem"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "invalid"

    def test_payload_missing_type_field(self, client: TestClient):
        response = client.post(
            "/webhook/monobank",
            json={"data": {"key": "value"}},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "invalid"

    def test_valid_minimal_payload(self, client: TestClient):
        payload = {"type": "SomeType", "data": {}}
        response = client.post("/webhook/monobank", json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "received"
