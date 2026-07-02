from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from src.core.cross_ref import NETWORK_ERROR_STATUS, CrossReferenceEngine


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
