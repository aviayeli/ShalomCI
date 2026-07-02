from unittest.mock import AsyncMock

import pytest

from src.sdk import ShalomCI_SDK
from src.services.mouser_api import MouserClient


@pytest.fixture
async def sdk(tmp_path, monkeypatch):
    monkeypatch.delenv("MOUSER_API_KEY", raising=False)
    db_file = tmp_path / "test_cases.db"
    instance = ShalomCI_SDK(db_path=str(db_file))
    yield instance
    await instance.close()


async def test_sdk_initialization(sdk):
    assert sdk.is_initialized is False, "ה-SDK לא אמור להיות מאותחל ברירת מחדל"

    await sdk.initialize()

    assert sdk.is_initialized is True, "ה-SDK לא התאתחל כראוי"

    # נוודא שניתן לגשת למנהל התיקים דרך ה-SDK
    cases = await sdk.case_manager.list_open_cases()
    assert isinstance(cases, list), "מנהל התיקים לא הוגדר נכון דרך ה-SDK"


async def test_find_mitigations_and_case_opening(sdk):
    """מוודא שה-SDK פותח אוטומטית תיק טיפול לרכיב בסיכון קריטי ללא חלופות."""
    await sdk.initialize()

    # מוקקים את מנוע ה-CrossRef שיחזיר תמיד רשימה ריקה
    sdk.cross_ref.find_alternatives = AsyncMock(return_value=[])

    components = [
        {"mpn": "DANGEROUS_PART", "risk_score": 1},
        {"mpn": "SAFE_PART", "risk_score": 5}
    ]

    result = await sdk.find_mitigations(components, project_name="TestProject")

    # נוודא ששום חלופה לא נוספה
    assert result[0]["alternatives"] == []

    # הלוגיקה העסקית אמורה הייתה לפתוח תיק. נבדוק את מסד הנתונים:
    open_cases = await sdk.case_manager.list_open_cases()
    assert len(open_cases) == 1, "תיק טיפול היה חייב להיפתח עבור ציון 1 ללא חלופות"
    assert open_cases[0]["mpn"] == "DANGEROUS_PART"


def test_sdk_has_no_default_client_without_env_key(sdk):
    """ללא MOUSER_API_KEY בסביבה, ה-SDK לא אמור להקים קליינט ברירת מחדל (fallback ל-N/A)."""
    assert sdk.cross_ref.api_client is None


async def test_sdk_builds_mouser_client_from_env_key(tmp_path, monkeypatch):
    """כאשר MOUSER_API_KEY מוגדר בסביבה, ה-SDK אמור להקים MouserClient דרך ה-Gatekeeper אוטומטית."""
    monkeypatch.setenv("MOUSER_API_KEY", "fake_key_from_env")
    db_file = tmp_path / "test_cases.db"

    instance = ShalomCI_SDK(db_path=str(db_file))
    try:
        assert isinstance(instance.cross_ref.api_client, MouserClient)
        assert instance.cross_ref.api_client.api_key == "fake_key_from_env"
        assert instance.cross_ref.api_client.gatekeeper is instance.gatekeeper
    finally:
        await instance.close()


async def test_sdk_explicit_api_client_overrides_env(tmp_path, monkeypatch):
    """אם מוזרק api_client ידנית, הוא גובר על בניית ברירת המחדל מהסביבה."""
    monkeypatch.setenv("MOUSER_API_KEY", "fake_key_from_env")
    db_file = tmp_path / "test_cases.db"
    injected_client = AsyncMock()

    instance = ShalomCI_SDK(db_path=str(db_file), api_client=injected_client)
    try:
        assert instance.cross_ref.api_client is injected_client
    finally:
        await instance.close()
