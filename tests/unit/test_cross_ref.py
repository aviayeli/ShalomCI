from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from src.core.cross_ref import (
    DIGIKEY_FIELD_DEFAULTS,
    NETWORK_ERROR_STATUS,
    OCTOPART_FIELD_DEFAULTS,
    CrossReferenceEngine,
)
from src.services.gatekeeper import ApiGatekeeper
from src.services.mouser_api import MouserClient


@pytest.mark.asyncio
async def test_find_alternatives_success():
    """בדיקה שהמנוע מחלץ חלופות מתוך עץ ה-GraphQL בצורה תקינה."""
    mock_client = AsyncMock()
    mock_client.search_cross_reference.return_value = {
        "data": {
            "supSearch": {
                "results": [{"part": {"similarParts": [{"mpn": "NE555_ALT"}]}}]
            }
        }
    }

    engine = CrossReferenceEngine(api_client=mock_client)
    alts = await engine.find_alternatives("NE555")

    assert len(alts) == 1
    assert alts[0]["mpn"] == "NE555_ALT"


@pytest.mark.asyncio
async def test_find_alternatives_empty_or_fail():
    """בדיקה שהמנוע שורד מבנים ריקים או שגיאות."""
    mock_client = AsyncMock()
    mock_client.search_cross_reference.return_value = {"data": {}}
    engine = CrossReferenceEngine(api_client=mock_client)

    alts = await engine.find_alternatives("BAD_PART")
    assert alts == []


@pytest.mark.asyncio
async def test_find_alternatives_unsupported_client_returns_empty():
    """מוודא שקליינט ללא יכולת קרוס-רפרנס (כמו Mouser) לא זורק שגיאה אלא מחזיר רשימה ריקה."""
    mouser_like_client = Mock(spec=["search_part"])
    engine = CrossReferenceEngine(api_client=mouser_like_client)

    alts = await engine.find_alternatives("NE555")
    assert alts == []


@pytest.mark.asyncio
async def test_get_part_data_mouser_shape_active():
    """בדיקה שהמנוע מפרש נכון את מבנה תגובת ה-REST של Mouser (SearchResults.Parts)."""
    mock_client = AsyncMock()
    mock_client.search_part.return_value = {
        "SearchResults": {
            "Parts": [{"Manufacturer": "Texas Instruments", "LifecycleStatus": "Active"}]
        }
    }

    engine = CrossReferenceEngine(api_client=mock_client)
    data = await engine.get_part_data("NE555")

    assert data["manufacturer"] == "Texas Instruments"
    assert data["lifecycle"] == "Active"
    assert data["risk_score"] == 5


@pytest.mark.asyncio
async def test_get_part_data_mouser_shape_no_results():
    """בדיקה שמבנה תגובה ריק (מק"ט לא נמצא ב-Mouser) מוחזר כ-Unknown ולא כשגיאה."""
    mock_client = AsyncMock()
    mock_client.search_part.return_value = {"SearchResults": {"Parts": []}}

    engine = CrossReferenceEngine(api_client=mock_client)
    data = await engine.get_part_data("UNKNOWN_MPN")

    assert data == {"manufacturer": "Unknown", "lifecycle": "Unknown", "risk_score": 5}


@pytest.mark.asyncio
async def test_get_part_data_mouser_error_response_search_results_is_none():
    """שחזור תרחיש אמיתי: Mouser מחזירה SearchResults=None (למשל בעת מפתח API לא תקין)."""
    mock_client = AsyncMock()
    mock_client.search_part.return_value = {
        "Errors": [{"Code": "Invalid", "Message": "Invalid unique identifier.", "PropertyName": "API Key"}],
        "SearchResults": None
    }

    engine = CrossReferenceEngine(api_client=mock_client)
    data = await engine.get_part_data("NE555")

    assert data == {"manufacturer": "Unknown", "lifecycle": "Unknown", "risk_score": 5}


@pytest.mark.asyncio
async def test_get_part_data_merges_mouser_extra_fields():
    """מוודא שכאשר הקליינט הוא MouserClient אמיתי, השדות המורחבים (מלאי, זמן אספקה וכו')
    ממוזגים לתוך תוצאת get_part_data - ולא רק manufacturer/lifecycle/risk_score."""
    client = MouserClient(api_key="fake_key", gatekeeper=ApiGatekeeper())
    client.search_part = AsyncMock(return_value={
        "SearchResults": {
            "Parts": [{
                "Manufacturer": "Texas Instruments",
                "LifecycleStatus": "Active",
                "Availability": "5,000 In Stock",
                "LeadTime": "10 Days",
            }]
        }
    })

    engine = CrossReferenceEngine(api_client=client)
    data = await engine.get_part_data("NE555")

    assert data["inventory"] == "Mouser: 5,000 במלאי"
    assert data["lead_time"] == "זמן אספקה: 10 ימים"
    await client.gatekeeper.close()


@pytest.mark.asyncio
async def test_get_part_data_network_error_marks_distinct_status():
    """מוודא שכשל רשת (אחרי שה-Gatekeeper מיצה Retries) מסומן בסטטוס ייעודי, לא כ'Unknown' רגיל."""
    mock_client = AsyncMock()
    mock_client.search_part.side_effect = httpx.ConnectError("Connection refused")

    engine = CrossReferenceEngine(api_client=mock_client)
    data = await engine.get_part_data("NE555")

    assert data == {"manufacturer": NETWORK_ERROR_STATUS, "lifecycle": NETWORK_ERROR_STATUS, "risk_score": 0}


@pytest.mark.asyncio
async def test_get_part_data_http_status_error_marks_distinct_status():
    """מוודא ששגיאת HTTP (למשל 500 שחזרה מ-raise_for_status) מטופלת כשגיאת רשת ולא כ'Error' כללי."""
    mock_client = AsyncMock()
    mock_client.search_part.side_effect = httpx.HTTPStatusError("Server Error", request=None, response=None)

    engine = CrossReferenceEngine(api_client=mock_client)
    data = await engine.get_part_data("NE555")

    assert data == {"manufacturer": NETWORK_ERROR_STATUS, "lifecycle": NETWORK_ERROR_STATUS, "risk_score": 0}


@pytest.mark.asyncio
async def test_get_digikey_data_no_client_returns_defaults():
    """ללא קליינט DigiKey מחובר, מוחזרות ברירות המחדל בעברית ולא נזרקת שגיאה."""
    engine = CrossReferenceEngine(api_client=None, digikey_client=None)

    data = await engine.get_digikey_data("NE555")

    assert data == DIGIKEY_FIELD_DEFAULTS


@pytest.mark.asyncio
async def test_get_digikey_data_merges_parsed_fields():
    """מוודא שכאשר קליינט DigiKey מחובר, השדות מחולצים דרך DigiKeyClient.parse_extra_fields."""
    mock_client = AsyncMock()
    mock_client.search_part.return_value = {
        "Product": {
            "ProductStatus": {"Status": "Active"},
            "QuantityAvailable": 100,
            "UnitPrice": 2.5,
            "ManufacturerLeadWeeks": "4 Weeks",
        }
    }

    engine = CrossReferenceEngine(digikey_client=mock_client)
    data = await engine.get_digikey_data("NE555")

    assert data["digikey_lifecycle"] == "פעיל"
    assert data["digikey_inventory"] == "DigiKey: 100"
    assert data["digikey_price_per_unit"] == "$2.50"
    mock_client.search_part.assert_awaited_once_with("NE555")


@pytest.mark.asyncio
async def test_get_digikey_data_network_error_returns_defaults():
    """מוודא שכשל רשת מול DigiKey (לאחר Retries של ה-Gatekeeper) חוזר לברירות מחדל ולא קורס."""
    mock_client = AsyncMock()
    mock_client.search_part.side_effect = httpx.ConnectError("Connection refused")

    engine = CrossReferenceEngine(digikey_client=mock_client)
    data = await engine.get_digikey_data("NE555")

    assert data == DIGIKEY_FIELD_DEFAULTS


@pytest.mark.asyncio
async def test_get_digikey_data_generic_error_returns_defaults():
    """מוודא ששגיאה כללית בלתי צפויה מ-DigiKey חוזרת לברירות מחדל ולא קורסת."""
    mock_client = AsyncMock()
    mock_client.search_part.side_effect = RuntimeError("boom")

    engine = CrossReferenceEngine(digikey_client=mock_client)
    data = await engine.get_digikey_data("NE555")

    assert data == DIGIKEY_FIELD_DEFAULTS


@pytest.mark.asyncio
async def test_get_octopart_data_no_client_returns_defaults():
    """ללא קליינט Octopart מחובר, מוחזרות ברירות המחדל בעברית ולא נזרקת שגיאה."""
    engine = CrossReferenceEngine(octopart_client=None)

    data = await engine.get_octopart_data("NE555")

    assert data == OCTOPART_FIELD_DEFAULTS


@pytest.mark.asyncio
async def test_get_octopart_data_merges_parsed_fields():
    """מוודא שכאשר קליינט Octopart מחובר, השדות מחולצים דרך OctopartClient.parse_extra_fields."""
    mock_client = AsyncMock()
    mock_client.search_part.return_value = {
        "data": {"supSearch": {"results": [{"part": {
            "lifecycleStatus": "Active",
            "sellers": [{"offers": [{"inventoryLevel": 500, "factoryLeadDays": 5, "prices": [{"price": 0.3, "quantity": 1}]}]}],
        }}]}}
    }

    engine = CrossReferenceEngine(octopart_client=mock_client)
    data = await engine.get_octopart_data("NE555")

    assert data["octopart_lifecycle"] == "פעיל"
    assert data["octopart_inventory"] == "Octopart: 500"
    assert data["octopart_price_per_unit"] == "$0.30"
    mock_client.search_part.assert_awaited_once_with("NE555")


@pytest.mark.asyncio
async def test_get_octopart_data_network_error_returns_defaults():
    """מוודא שכשל רשת מול Octopart (לאחר Retries של ה-Gatekeeper) חוזר לברירות מחדל ולא קורס."""
    mock_client = AsyncMock()
    mock_client.search_part.side_effect = httpx.ConnectError("Connection refused")

    engine = CrossReferenceEngine(octopart_client=mock_client)
    data = await engine.get_octopart_data("NE555")

    assert data == OCTOPART_FIELD_DEFAULTS


@pytest.mark.asyncio
async def test_get_octopart_data_generic_error_returns_defaults():
    """מוודא ששגיאה כללית בלתי צפויה מ-Octopart חוזרת לברירות מחדל ולא קורסת."""
    mock_client = AsyncMock()
    mock_client.search_part.side_effect = RuntimeError("boom")

    engine = CrossReferenceEngine(octopart_client=mock_client)
    data = await engine.get_octopart_data("NE555")

    assert data == OCTOPART_FIELD_DEFAULTS


@pytest.mark.asyncio
async def test_find_alternatives_prefers_octopart_client_over_api_client():
    """מוודא ש-find_alternatives פונה לקליינט Octopart הייעודי, ולא ל-api_client הראשי (Mouser), כשקיימים שניהם."""
    mouser_like_client = AsyncMock()
    octopart_client = AsyncMock()
    octopart_client.search_cross_reference.return_value = {
        "data": {"supSearch": {"results": [{"part": {"similarParts": [{"mpn": "OCTOPART_ALT"}]}}]}}
    }

    engine = CrossReferenceEngine(api_client=mouser_like_client, octopart_client=octopart_client)
    alts = await engine.find_alternatives("NE555")

    assert alts == [{"mpn": "OCTOPART_ALT"}]
    octopart_client.search_cross_reference.assert_awaited_once_with("NE555")
    mouser_like_client.search_cross_reference.assert_not_called()
