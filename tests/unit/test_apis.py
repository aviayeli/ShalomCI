import asyncio
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
    def __init__(self, json_data, status_code=200, text=None):
        self._json_data = json_data
        self.status_code = status_code
        self.text = text if text is not None else str(json_data)

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


async def test_gatekeeper_fails_fast_on_400_client_error_no_retry(gatekeeper, monkeypatch):
    """מוודא ששגיאת 400 (Bad Request) נכשלת מיידית ולא נכנסת ללולאת Retry/Backoff -
    זו הייתה תקלה שחסמה באופן סינכרוני את כל תור העשרת ה-BOM לדקות ארוכות."""
    mock_request = AsyncMock(return_value=MockResponse({"errors": "bad query"}, status_code=400))
    monkeypatch.setattr(gatekeeper.client, "request", mock_request)
    sleep_mock = AsyncMock()
    monkeypatch.setattr("src.services.gatekeeper.asyncio.sleep", sleep_mock)

    with pytest.raises(httpx.HTTPStatusError):
        await gatekeeper.request("octopart", "POST", "http://test.com", retries=3)

    mock_request.assert_called_once()
    sleep_mock.assert_not_awaited()


async def test_gatekeeper_retries_on_500_server_error(gatekeeper, monkeypatch):
    """מוודא ששגיאת שרת (5xx) עדיין נכנסת ל-Retry עם Exponential Backoff, בניגוד ל-4xx."""
    responses = [
        MockResponse({}, status_code=503),
        MockResponse({"success": True}, status_code=200),
    ]
    mock_request = AsyncMock(side_effect=responses)
    monkeypatch.setattr(gatekeeper.client, "request", mock_request)
    monkeypatch.setattr("src.services.gatekeeper.asyncio.sleep", AsyncMock())

    response = await gatekeeper.request("octopart", "POST", "http://test.com", retries=3)

    assert response.status_code == 200
    assert mock_request.call_count == 2


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

    assert extra["mouser_stock_qty"] == 24755.0
    assert extra["lead_time"] == "זמן אספקה: 63 ימים"
    assert extra["mouser_price_value"] == 1.85
    assert extra["suggested_replacement"] == "NE555DR-ALT"
    assert extra["rohs_status"] == "תואם RoHS"
    assert extra["packaging"] == "Cut Tape"


def test_parse_extra_fields_defaults_for_missing_data():
    """מוודא שערכים חסרים (למשל אין PriceBreaks/חלופה מוצעת) מקבלים ברירות מחדל תקינות."""
    extra = MouserClient.parse_extra_fields({})

    assert extra["mouser_price_value"] is None
    assert extra["mouser_stock_qty"] is None
    assert extra["suggested_replacement"] == "אין"
    assert extra["packaging"] == "לא ידוע"


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

    assert extra["digikey_stock_qty"] == 24755.0
    assert extra["digikey_lead_time"] == "זמן אספקה: 9 שבועות"
    assert extra["digikey_price_value"] == 1.85


def test_digikey_parse_extra_fields_defaults_for_missing_data():
    """מוודא שתגובת DigiKey ריקה (למשל מק"ט לא נמצא) מקבלת ברירות מחדל תקינות ולא קורסת."""
    extra = DigiKeyClient.parse_extra_fields({})

    assert extra["digikey_stock_qty"] is None
    assert extra["digikey_price_value"] is None
    assert extra["digikey_lead_time"] == "זמן אספקה: לא ידוע"


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


async def test_octopart_token_request_logs_and_reraises_on_400(gatekeeper, monkeypatch, caplog):
    """מוודא ששגיאת 400 בשלב שליפת הטוקן עצמו (client_id/secret שגויים) גם היא נרשמת ונזרקת הלאה."""
    client = OctopartClient(client_id="bad_id", client_secret="bad_secret", gatekeeper=gatekeeper)
    error_body = '{"error":"invalid_client"}'
    mock_request = AsyncMock(return_value=MockResponse({}, status_code=400, text=error_body))
    monkeypatch.setattr(gatekeeper.client, "request", mock_request)

    with caplog.at_level("ERROR"):
        with pytest.raises(httpx.HTTPStatusError):
            await client.search_part("NE555")

    assert "invalid_client" in caplog.text


@pytest.mark.parametrize("client_factory, token_url, search_payload", [
    (
        lambda gk: DigiKeyClient(client_id="id", client_secret="secret", gatekeeper=gk),
        DigiKeyClient.TOKEN_URL,
        {"Product": {"ManufacturerLeadWeeks": None}},
    ),
    (
        lambda gk: OctopartClient(client_id="id", client_secret="secret", gatekeeper=gk),
        OctopartClient.TOKEN_URL,
        {"data": {"supSearch": {"results": []}}},
    ),
])
async def test_token_single_flight_fetches_token_exactly_once(
    gatekeeper, monkeypatch, client_factory, token_url, search_payload
):
    """מוודא נעילת single-flight: שתי קריאות search_part מקבילות מפעילות בקשת טוקן אחת בלבד -
    בקשת הטוקן איטית (yield מלאכותי) כדי ששני הקורוטינים יחפפו על הנעילה, ורק אחד יבצע POST."""
    client = client_factory(gatekeeper)
    token_calls = 0

    async def fake_request(method, url, **kwargs):
        nonlocal token_calls
        if url == token_url:
            token_calls += 1
            # השהיה מלאכותית: מוותרת על השליטה כדי ששתי הפניות יגיעו לנעילה בו-זמנית
            for _ in range(3):
                await asyncio.sleep(0)
            return MockResponse({"access_token": "abc123", "expires_in": 600})
        return MockResponse(search_payload)

    monkeypatch.setattr(gatekeeper.client, "request", fake_request)

    await asyncio.gather(client.search_part("PART_A"), client.search_part("PART_B"))

    assert token_calls == 1, "נקודת הטוקן נקראה יותר מפעם אחת - נעילת single-flight נכשלה"


async def test_octopart_search_cross_reference_is_same_query_as_search_part(gatekeeper, monkeypatch):
    """מוודא ש-search_cross_reference (המשמש ל-FFF) משתמש באותה שאילתה בדיוק כמו search_part."""
    client = OctopartClient(client_id="fake_id", client_secret="fake_secret", gatekeeper=gatekeeper)

    token_response = MockResponse({"access_token": "abc123", "expires_in": 3600})
    graphql_response = MockResponse({"data": {"supSearch": {"results": []}}})
    mock_request = AsyncMock(side_effect=[token_response, graphql_response])
    monkeypatch.setattr(gatekeeper.client, "request", mock_request)

    result = await client.search_cross_reference("NE555")

    assert result == {"data": {"supSearch": {"results": []}}}


async def test_octopart_search_part_logs_response_body_and_reraises_on_400(gatekeeper, monkeypatch, caplog):
    """מוודא שתגובת שגיאת 400 מ-Nexar (GraphQL) נרשמת ללוג עם גוף התגובה המדויק, ואז נזרקת הלאה
    (לא נבלעת) כדי ש-CrossReferenceEngine.get_octopart_data ידע ליפול חזרה לברירות מחדל."""
    client = OctopartClient(client_id="fake_id", client_secret="fake_secret", gatekeeper=gatekeeper)

    token_response = MockResponse({"access_token": "abc123", "expires_in": 3600})
    error_body = '{"errors":[{"message":"Cannot query field \\"supSearch\\" on type Query."}]}'
    bad_response = MockResponse({}, status_code=400, text=error_body)
    mock_request = AsyncMock(side_effect=[token_response, bad_response])
    monkeypatch.setattr(gatekeeper.client, "request", mock_request)

    with caplog.at_level("ERROR"):
        with pytest.raises(httpx.HTTPStatusError):
            await client.search_part("NE555")

    assert "supSearch" in caplog.text
    assert "400" in caplog.text


def test_octopart_parse_extra_fields_extracts_and_translates_full_result():
    """בדיקה שהחילוץ מתוך מבנה תגובת GraphQL מלא של Octopart מתרגם ומעצב את כל השדות.
    lifecycleStatus אינו נשלף מ-Octopart בכוונה (אינו קיים על SupPart בסכימת Nexar בפועל -
    ראו _PART_QUERY) - Mouser הוא המקור היחיד למחזור חיים, לכן העמודה תמיד "לא ידוע"."""
    payload = {
        "data": {
            "supSearch": {
                "results": [{
                    "part": {
                        "mpn": "NE555",
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

    assert "octopart_lifecycle" not in extra
    assert extra["octopart_stock_qty"] == 3400.0
    assert extra["octopart_lead_time"] == "זמן אספקה: 12 ימים"
    assert extra["octopart_price_value"] == 0.95


def test_octopart_parse_extra_fields_falls_back_to_first_price_tier_without_quantity_one():
    """אם אין מדרגת מחיר לכמות 1 בודדת, יש ליפול חזרה למדרגת המחיר הראשונה שקיימת."""
    payload = {
        "data": {"supSearch": {"results": [{"part": {
            "sellers": [{"offers": [{
                "inventoryLevel": 10,
                "prices": [{"price": 2.5, "quantity": 100}, {"price": 2.2, "quantity": 500}],
            }]}],
        }}]}}
    }

    extra = OctopartClient.parse_extra_fields(payload)

    assert extra["octopart_price_value"] == 2.5


def test_octopart_parse_extra_fields_defaults_for_missing_data():
    """מוודא שתגובת Octopart ריקה (למשל מק"ט לא נמצא) מקבלת ברירות מחדל תקינות ולא קורסת."""
    extra = OctopartClient.parse_extra_fields({"data": {"supSearch": {"results": []}}})

    assert extra["octopart_stock_qty"] is None
    assert extra["octopart_price_value"] is None
    assert extra["octopart_lead_time"] == "זמן אספקה: לא ידוע"


@pytest.mark.parametrize("payload", [
    {"data": None},
    {"data": {"supSearch": None}},
    {"data": {"supSearch": {"results": None}}},
    {"data": {"supSearch": {"results": [None]}}},
    {"data": {"supSearch": {"results": [{"part": None}]}}},
    {"data": {"supSearch": {"results": [{"part": {"sellers": None}}]}}},
    {"data": {"supSearch": {"results": [{"part": {"sellers": [None]}}]}}},
    {"data": {"supSearch": {"results": [{"part": {"sellers": [{"offers": None}]}}]}}},
    {"data": {"supSearch": {"results": [{"part": {"sellers": [{"offers": [None]}]}}]}}},
    {"data": {"supSearch": {"results": [{"part": {"sellers": [{"offers": [{"prices": None}]}]}}]}}},
    {"data": {"supSearch": {"results": [{"part": {"sellers": [{"offers": [{"prices": [None]}]}]}}]}}},
])
def test_octopart_parse_extra_fields_survives_explicit_nulls_at_every_level(payload):
    """מוודא ש-null מפורש (לא רק מפתח חסר) בכל שלב במבנה - data/supSearch/results/part/
    sellers/offers/prices, כולל איברים בודדים בתוך רשימה - לא גורם ל-AttributeError
    ('NoneType' object has no attribute 'get'), כפי שNexar מחזיר בפועל לרכיבים חסרי מידע."""
    extra = OctopartClient.parse_extra_fields(payload)

    assert extra["octopart_stock_qty"] is None
    assert extra["octopart_lead_time"] == "זמן אספקה: לא ידוע"
    assert extra["octopart_price_value"] is None


def test_octopart_parse_extra_fields_skips_null_offer_to_find_valid_one():
    """מוודא שאיבר null בודד בתוך רשימת offers (למשל [null, {...}]) לא עוצר את החיפוש -
    ה-offer התקין הבא ברשימה עדיין נמצא ומשמש לחילוץ הנתונים."""
    payload = {
        "data": {"supSearch": {"results": [{"part": {
            "sellers": [{"offers": [None, {"inventoryLevel": 42, "prices": [{"price": 1.0, "quantity": 1}]}]}],
        }}]}}
    }

    extra = OctopartClient.parse_extra_fields(payload)

    assert extra["octopart_stock_qty"] == 42.0
    assert extra["octopart_price_value"] == 1.0
