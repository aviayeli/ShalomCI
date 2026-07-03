from unittest.mock import AsyncMock

import httpx
import pytest

from src.services.digikey_api import DigiKeyClient
from src.services.gatekeeper import ApiGatekeeper
from src.services.mouser_api import MouserClient
from src.services.octopart_api import OctopartClient


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


def test_parse_extra_fields_extracts_and_translates_full_part():
    """בדיקה שהחילוץ מתוך מבנה חלק מלא של Mouser מתרגם ומעצב את כל השדות הנדרשים."""
    part = {
        "Availability": "24,755 In Stock",
        "LeadTime": "63 Days",
        "PriceBreaks": [
            {"Quantity": 10, "Price": "₪1.50"},
            {"Quantity": 1, "Price": "₪1.85"},
        ],
        "SuggestedReplacement": "NE555DR-ALT",
        "ROHSStatus": "RoHS Compliant",
        "ProductAttributes": [
            {"AttributeName": "Package", "AttributeValue": "SOIC-8"},
            {"AttributeName": "Packaging", "AttributeValue": "Cut Tape"},
        ],
    }

    extra = MouserClient.parse_extra_fields(part)

    assert extra["inventory"] == "Mouser: 24,755 במלאי"
    assert extra["lead_time"] == "זמן אספקה: 63 ימים"
    assert extra["price_per_unit"] == "₪1.85"
    assert extra["suggested_replacement"] == "NE555DR-ALT"
    assert extra["rohs_status"] == "תואם RoHS"
    assert extra["packaging"] == "Cut Tape"


def test_parse_extra_fields_defaults_for_missing_data():
    """מוודא שערכים חסרים (למשל אין PriceBreaks/חלופה מוצעת) מקבלים ברירות מחדל בעברית."""
    extra = MouserClient.parse_extra_fields({})

    assert extra["price_per_unit"] == "לא זמין"
    assert extra["suggested_replacement"] == "אין"
    assert extra["packaging"] == "לא ידוע"
    assert extra["inventory"] == "Mouser: לא ידוע"


def test_digikey_client_missing_credentials(gatekeeper):
    """מוודא חסימה בהקמת קליינט DigiKey ללא Client ID/Secret."""
    with pytest.raises(ValueError, match="DigiKey client ID and secret are required"):
        DigiKeyClient(client_id="", client_secret="secret", gatekeeper=gatekeeper)
    with pytest.raises(ValueError, match="DigiKey client ID and secret are required"):
        DigiKeyClient(client_id="id", client_secret="", gatekeeper=gatekeeper)


async def test_digikey_client_fetches_and_caches_access_token(gatekeeper, monkeypatch):
    """מוודא שהטוקן נשלף פעם אחת מ-OAuth2 Client Credentials וממוחזר בקריאה השנייה."""
    client = DigiKeyClient(client_id="fake_id", client_secret="fake_secret", gatekeeper=gatekeeper)

    token_response = MockResponse({"access_token": "abc123", "expires_in": 600})
    part_response = MockResponse({"Product": {"ManufacturerLeadWeeks": None}})
    mock_request = AsyncMock(side_effect=[token_response, part_response, part_response])
    monkeypatch.setattr(gatekeeper.client, "request", mock_request)

    await client.search_part("NE555")
    await client.search_part("NE555")

    # קריאה אחת בלבד לטוקן (POST) ושתי קריאות ל-productdetails (GET) - הטוקן ממוחזר
    assert mock_request.call_count == 3
    token_call_args, token_call_kwargs = mock_request.call_args_list[0]
    assert token_call_args[0] == "POST"
    assert token_call_args[1] == DigiKeyClient.TOKEN_URL
    search_call_args, search_call_kwargs = mock_request.call_args_list[1]
    assert search_call_args[0] == "GET"
    assert "NE555" in search_call_args[1]
    assert search_call_kwargs["headers"]["Authorization"] == "Bearer abc123"


def test_digikey_parse_extra_fields_extracts_and_translates_full_product():
    """בדיקה שהחילוץ מתוך מבנה ProductDetails מלא של DigiKey מתרגם ומעצב את כל השדות."""
    payload = {
        "Product": {
            "ProductStatus": {"Status": "Active"},
            "QuantityAvailable": 24755,
            "UnitPrice": 1.85,
            "ManufacturerLeadWeeks": "9 Weeks",
        }
    }

    extra = DigiKeyClient.parse_extra_fields(payload)

    assert extra["digikey_lifecycle"] == "פעיל"
    assert extra["digikey_inventory"] == "DigiKey: 24,755"
    assert extra["digikey_lead_time"] == "זמן אספקה: 9 שבועות"
    assert extra["digikey_price_per_unit"] == "$1.85"


def test_digikey_parse_extra_fields_defaults_for_missing_data():
    """מוודא שתגובת DigiKey ריקה (למשל מק"ט לא נמצא) מקבלת ברירות מחדל בעברית ולא קורסת."""
    extra = DigiKeyClient.parse_extra_fields({})

    assert extra["digikey_lifecycle"] == "לא ידוע"
    assert extra["digikey_inventory"] == "DigiKey: לא ידוע"
    assert extra["digikey_lead_time"] == "זמן אספקה: לא ידוע"
    assert extra["digikey_price_per_unit"] == "לא זמין"


def test_octopart_client_missing_credentials(gatekeeper):
    """מוודא חסימה בהקמת קליינט Octopart ללא Client ID/Secret."""
    with pytest.raises(ValueError, match="Octopart client ID and secret are required"):
        OctopartClient(client_id="", client_secret="secret", gatekeeper=gatekeeper)
    with pytest.raises(ValueError, match="Octopart client ID and secret are required"):
        OctopartClient(client_id="id", client_secret="", gatekeeper=gatekeeper)


async def test_octopart_client_fetches_and_caches_access_token(gatekeeper, monkeypatch):
    """מוודא שהטוקן נשלף פעם אחת מ-OAuth2 Client Credentials מול Nexar וממוחזר בקריאה השנייה."""
    client = OctopartClient(client_id="fake_id", client_secret="fake_secret", gatekeeper=gatekeeper)

    token_response = MockResponse({"access_token": "abc123", "expires_in": 3600})
    graphql_response = MockResponse({"data": {"supSearch": {"results": []}}})
    mock_request = AsyncMock(side_effect=[token_response, graphql_response, graphql_response])
    monkeypatch.setattr(gatekeeper.client, "request", mock_request)

    await client.search_part("NE555")
    await client.search_part("NE555")

    # קריאה אחת בלבד לטוקן (POST) ושתי קריאות GraphQL - הטוקן ממוחזר
    assert mock_request.call_count == 3
    token_call_args, _ = mock_request.call_args_list[0]
    assert token_call_args[0] == "POST"
    assert token_call_args[1] == OctopartClient.TOKEN_URL
    graphql_call_args, graphql_call_kwargs = mock_request.call_args_list[1]
    assert graphql_call_args[1] == OctopartClient.GRAPHQL_URL
    assert graphql_call_kwargs["headers"]["Authorization"] == "Bearer abc123"
    assert "NE555" in graphql_call_kwargs["json"]["variables"]["mpn"]


async def test_octopart_search_cross_reference_is_same_query_as_search_part(gatekeeper, monkeypatch):
    """מוודא ש-search_cross_reference (המשמש ל-FFF) משתמש באותה שאילתה בדיוק כמו search_part."""
    client = OctopartClient(client_id="fake_id", client_secret="fake_secret", gatekeeper=gatekeeper)

    token_response = MockResponse({"access_token": "abc123", "expires_in": 3600})
    graphql_response = MockResponse({"data": {"supSearch": {"results": []}}})
    mock_request = AsyncMock(side_effect=[token_response, graphql_response])
    monkeypatch.setattr(gatekeeper.client, "request", mock_request)

    result = await client.search_cross_reference("NE555")

    assert result == {"data": {"supSearch": {"results": []}}}


def test_octopart_parse_extra_fields_extracts_and_translates_full_result():
    """בדיקה שהחילוץ מתוך מבנה תגובת GraphQL מלא של Octopart מתרגם ומעצב את כל השדות."""
    payload = {
        "data": {
            "supSearch": {
                "results": [{
                    "part": {
                        "mpn": "NE555",
                        "lifecycleStatus": "Active",
                        "sellers": [{
                            "company": {"name": "Newark"},
                            "offers": [{
                                "inventoryLevel": 3400,
                                "factoryLeadDays": 12,
                                "prices": [
                                    {"price": 1.10, "currency": "USD", "quantity": 10},
                                    {"price": 0.95, "currency": "USD", "quantity": 1},
                                ],
                            }],
                        }],
                    }
                }]
            }
        }
    }

    extra = OctopartClient.parse_extra_fields(payload)

    assert extra["octopart_lifecycle"] == "פעיל"
    assert extra["octopart_inventory"] == "Octopart: 3,400"
    assert extra["octopart_lead_time"] == "זמן אספקה: 12 ימים"
    assert extra["octopart_price_per_unit"] == "$0.95"


def test_octopart_parse_extra_fields_falls_back_to_first_price_tier_without_quantity_one():
    """אם אין מדרגת מחיר לכמות 1 בודדת, יש ליפול חזרה למדרגת המחיר הראשונה שקיימת."""
    payload = {
        "data": {"supSearch": {"results": [{"part": {
            "lifecycleStatus": "Active",
            "sellers": [{"offers": [{
                "inventoryLevel": 10,
                "prices": [{"price": 2.5, "quantity": 100}, {"price": 2.2, "quantity": 500}],
            }]}],
        }}]}}
    }

    extra = OctopartClient.parse_extra_fields(payload)

    assert extra["octopart_price_per_unit"] == "$2.50"


def test_octopart_parse_extra_fields_defaults_for_missing_data():
    """מוודא שתגובת Octopart ריקה (למשל מק"ט לא נמצא) מקבלת ברירות מחדל בעברית ולא קורסת."""
    extra = OctopartClient.parse_extra_fields({"data": {"supSearch": {"results": []}}})

    assert extra["octopart_lifecycle"] == "לא ידוע"
    assert extra["octopart_inventory"] == "Octopart: לא ידוע"
    assert extra["octopart_lead_time"] == "זמן אספקה: לא ידוע"
    assert extra["octopart_price_per_unit"] == "לא זמין"
