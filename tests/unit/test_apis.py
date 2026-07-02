from unittest.mock import AsyncMock

import httpx
import pytest

from src.services.gatekeeper import ApiGatekeeper
from src.services.mouser_api import MouserClient


@pytest.fixture
async def gatekeeper():
    gk = ApiGatekeeper()
    yield gk
    await gk.close()


class MockResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("Mock Error", request=None, response=self)


async def test_gatekeeper_success_request(gatekeeper, monkeypatch):
    """בדיקת קריאה תקינה דרך שומר הסף."""
    mock_request = AsyncMock(return_value=MockResponse({"status": "ok"}))
    monkeypatch.setattr(gatekeeper.client, "request", mock_request)

    response = await gatekeeper.request("mouser", "GET", "http://test.com")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    mock_request.assert_called_once()


async def test_gatekeeper_retries_on_429(gatekeeper, monkeypatch):
    """בדיקה ששומר הסף מבצע ניסיון חוזר (Retry) כשהוא נתקל בשגיאת 429."""
    # מחזיר פעמיים שגיאת 429 ובפעם השלישית מצליח
    responses = [
        MockResponse({}, status_code=429),
        MockResponse({}, status_code=429),
        MockResponse({"success": True}, status_code=200)
    ]
    mock_request = AsyncMock(side_effect=responses)
    monkeypatch.setattr(gatekeeper.client, "request", mock_request)

    # אנו ממקנפגים את פונקציית השינה לא לעשות כלום כדי שהטסט ירוץ מיידית
    monkeypatch.setattr("src.services.gatekeeper.asyncio.sleep", AsyncMock())

    response = await gatekeeper.request("mouser", "GET", "http://test.com", retries=3)

    assert response.status_code == 200
    assert mock_request.call_count == 3


async def test_mouser_client_valid_search(gatekeeper, monkeypatch):
    """מוודא שהקליינט בונה את הבקשה כראוי ומעביר אותה ל-Gatekeeper."""
    client = MouserClient(api_key="fake_key", gatekeeper=gatekeeper)

    expected_data = {"SearchResults": {"Parts": [{"ManufacturerPartNumber": "NE555"}]}}
    mock_request = AsyncMock(return_value=MockResponse(expected_data))
    monkeypatch.setattr(gatekeeper.client, "request", mock_request)

    result = await client.search_part("NE555")

    assert result == expected_data
    mock_request.assert_called_once()
    # וידוא שהקריאה נותבה לספק הנכון עם מתודה נכונה
    args, kwargs = mock_request.call_args
    assert args[0] == "POST"
    assert "apiKey=fake_key" in args[1]


def test_mouser_client_missing_key(gatekeeper):
    """מוודא חסימה בהקמת קליינט ללא מפתח API."""
    with pytest.raises(ValueError, match="Mouser API key is required"):
        MouserClient(api_key="", gatekeeper=gatekeeper)
