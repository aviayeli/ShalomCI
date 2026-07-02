from unittest.mock import AsyncMock, patch

import pytest

from src.gui.app import build_rows, run_analysis, status_icon


@pytest.mark.parametrize("score,expected", [
    (1, "⛔"),
    (2, "⚠️"),
    (3, "⚠️"),
    (4, "✅"),
    (5, "✅"),
    (0, "❓"),
    (99, "❓"),
])
def test_status_icon(score, expected):
    """מוודא שכל ציון סיכון ממופה לאייקון הנגישות התואם, כולל ציון לא ידוע."""
    assert status_icon(score) == expected


def test_build_rows_prefixes_status_with_matching_icon():
    """מוודא שהעמודה 'סטטוס' תמיד כוללת גם אייקון וגם טקסט (לא צבע בלבד)."""
    components = [
        {"mpn": "PART_EOL", "manufacturer": "TI", "lifecycle_status": "Obsolete", "risk_score": 1, "alternatives": []},
        {"mpn": "PART_NRND", "manufacturer": "TI", "lifecycle_status": "NRND", "risk_score": 3,
         "alternatives": [{"mpn": "ALT1"}]},
        {"mpn": "PART_GOOD", "manufacturer": "TI", "lifecycle_status": "Active", "risk_score": 5, "alternatives": []},
    ]

    rows = build_rows(components)

    assert rows[0]["סטטוס"] == "⛔ Obsolete"
    assert rows[1]["סטטוס"] == "⚠️ NRND"
    assert rows[1]["חלופות"] == "ALT1"
    assert rows[2]["סטטוס"] == "✅ Active"
    assert rows[2]["חלופות"] == "אין"


def test_build_rows_defaults_for_missing_fields():
    """מוודא שרכיב ללא נתונים (למשל כשלון העשרה) מקבל ברירות מחדל תקינות."""
    rows = build_rows([{}])

    assert rows[0]["מק\"ט"] == "N/A"
    assert rows[0]["יצרן"] == "N/A"
    assert rows[0]["סטטוס"] == "❓ N/A"
    assert rows[0]["ציון סיכון"] == 0
    assert rows[0]["מלאי"] == "לא ידוע"
    assert rows[0]["חלופה מוצעת (Mouser)"] == "אין"


def test_build_rows_includes_extended_mouser_fields():
    """מוודא שהעמודות המורחבות (מלאי, זמן אספקה, מחיר, חלופה, RoHS, אריזה) מוצגות כראוי."""
    components = [{
        "mpn": "NE555", "manufacturer": "TI", "lifecycle_status": "פעיל", "risk_score": 5,
        "inventory": "Mouser: 24,755 במלאי",
        "lead_time": "זמן אספקה: 63 ימים",
        "price_per_unit": "₪1.85",
        "suggested_replacement": "NE555DR-ALT",
        "rohs_status": "תואם RoHS",
        "packaging": "Cut Tape",
    }]

    rows = build_rows(components)

    assert rows[0]["מלאי"] == "Mouser: 24,755 במלאי"
    assert rows[0]["זמן אספקה"] == "זמן אספקה: 63 ימים"
    assert rows[0]["מחיר ליחידה"] == "₪1.85"
    assert rows[0]["חלופה מוצעת (Mouser)"] == "NE555DR-ALT"
    assert rows[0]["תאימות RoHS"] == "תואם RoHS"
    assert rows[0]["צורת אריזה"] == "Cut Tape"


@pytest.mark.asyncio
@patch("src.gui.app.ShalomCI_SDK")
async def test_run_analysis_orchestrates_sdk_and_closes(mock_sdk_class):
    """מוודא ש-run_analysis קורא לכל שלבי ה-SDK לפי הסדר, ותמיד סוגר את החיבור בסיום."""
    mock_sdk = AsyncMock()
    mock_sdk_class.return_value = mock_sdk
    mock_sdk.process_bom.return_value = [{"mpn": "TEST_PART"}]
    mock_sdk.evaluate_risks.return_value = {"components": [{"mpn": "TEST_PART"}], "project_score": 4.5}
    mock_sdk.find_mitigations.return_value = [{"mpn": "TEST_PART", "alternatives": []}]

    score, data = await run_analysis("dummy.xlsx", "dummy.xlsx")

    assert score == 4.5
    assert data == [{"mpn": "TEST_PART", "alternatives": []}]
    mock_sdk.initialize.assert_awaited_once()
    mock_sdk.process_bom.assert_awaited_once_with("dummy.xlsx")
    mock_sdk.close.assert_awaited_once()


@pytest.mark.asyncio
@patch("src.gui.app.ShalomCI_SDK")
async def test_run_analysis_closes_sdk_even_on_failure(mock_sdk_class):
    """מוודא שגם כשלון באמצע התהליך לא מונע סגירת חיבורי הרשת (Gatekeeper)."""
    mock_sdk = AsyncMock()
    mock_sdk_class.return_value = mock_sdk
    mock_sdk.process_bom.side_effect = ValueError("bad file")

    with pytest.raises(ValueError):
        await run_analysis("dummy.xlsx", "dummy.xlsx")

    mock_sdk.close.assert_awaited_once()
