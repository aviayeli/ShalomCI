from unittest.mock import AsyncMock

import pytest

from src.sdk import ShalomCI_SDK
from src.services.digikey_api import DigiKeyClient
from src.services.mouser_api import MouserClient
from src.services.octopart_api import OctopartClient


@pytest.fixture
async def sdk(tmp_path, monkeypatch):
    monkeypatch.delenv("MOUSER_API_KEY", raising=False)
    monkeypatch.delenv("DIGIKEY_CLIENT_ID", raising=False)
    monkeypatch.delenv("DIGIKEY_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("OCTOPART_CLIENT_ID", raising=False)
    monkeypatch.delenv("OCTOPART_CLIENT_SECRET", raising=False)
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


async def test_enrich_components_fills_extra_field_defaults_without_client(sdk):
    """ללא קליינט Mouser מחובר, השדות המורחבים (מלאי, זמן אספקה וכו') מקבלים ברירת מחדל תקינה."""
    await sdk.initialize()
    components = [{"mpn": "NE555"}]

    await sdk.enrich_components(components)

    assert components[0]["mouser_stock_qty"] is None
    assert components[0]["lead_time"] == "זמן אספקה: לא ידוע"
    assert components[0]["suggested_replacement"] == "אין"


async def test_evaluate_risks_translates_lifecycle_status_after_scoring(sdk):
    """מוודא שה-risk_score מחושב לפי הטקסט האנגלי המקורי, ורק לאחר מכן lifecycle_status מתורגם לעברית."""
    await sdk.initialize()
    components = [{"mpn": "NE555", "lifecycle_status": "Obsolete"}]

    result = await sdk.evaluate_risks(components)

    assert result["components"][0]["risk_score"] == 1
    assert result["components"][0]["lifecycle_status"] == "מיושן"


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


def test_sdk_has_no_digikey_client_without_env_keys(sdk):
    """ללא DIGIKEY_CLIENT_ID/SECRET בסביבה, ה-SDK לא אמור להקים קליינט DigiKey (fallback לברירות מחדל)."""
    assert sdk.cross_ref.digikey_client is None


async def test_sdk_builds_digikey_client_from_env_keys(tmp_path, monkeypatch):
    """כאשר DIGIKEY_CLIENT_ID/SECRET מוגדרים בסביבה, ה-SDK אמור להקים DigiKeyClient דרך ה-Gatekeeper אוטומטית."""
    monkeypatch.setenv("DIGIKEY_CLIENT_ID", "fake_id_from_env")
    monkeypatch.setenv("DIGIKEY_CLIENT_SECRET", "fake_secret_from_env")
    db_file = tmp_path / "test_cases.db"

    instance = ShalomCI_SDK(db_path=str(db_file))
    try:
        assert isinstance(instance.cross_ref.digikey_client, DigiKeyClient)
        assert instance.cross_ref.digikey_client.client_id == "fake_id_from_env"
        assert instance.cross_ref.digikey_client.gatekeeper is instance.gatekeeper
    finally:
        await instance.close()


async def test_sdk_explicit_digikey_client_overrides_env(tmp_path, monkeypatch):
    """אם מוזרק digikey_client ידנית, הוא גובר על בניית ברירת המחדל מהסביבה."""
    monkeypatch.setenv("DIGIKEY_CLIENT_ID", "fake_id_from_env")
    monkeypatch.setenv("DIGIKEY_CLIENT_SECRET", "fake_secret_from_env")
    db_file = tmp_path / "test_cases.db"
    injected_client = AsyncMock()

    instance = ShalomCI_SDK(db_path=str(db_file), digikey_client=injected_client)
    try:
        assert instance.cross_ref.digikey_client is injected_client
    finally:
        await instance.close()


async def test_enrich_components_merges_digikey_fields_alongside_mouser(sdk):
    """מוודא ש-enrich_components ממזג את שדות ה-DigiKey (side-by-side) גם ללא קליינט Mouser."""
    await sdk.initialize()
    sdk.cross_ref.get_digikey_data = AsyncMock(return_value={
        "digikey_lifecycle": "פעיל",
        "digikey_inventory": "DigiKey: 500",
        "digikey_lead_time": "זמן אספקה: 2 שבועות",
        "digikey_price_per_unit": "$0.42",
    })
    components = [{"mpn": "NE555"}]

    await sdk.enrich_components(components)

    assert components[0]["digikey_lifecycle"] == "פעיל"
    assert components[0]["digikey_inventory"] == "DigiKey: 500"
    assert components[0]["digikey_price_per_unit"] == "$0.42"
    sdk.cross_ref.get_digikey_data.assert_awaited_once_with("NE555")


def test_sdk_has_no_octopart_client_without_env_keys(sdk):
    """ללא OCTOPART_CLIENT_ID/SECRET בסביבה, ה-SDK לא אמור להקים קליינט Octopart (fallback לברירות מחדל)."""
    assert sdk.cross_ref.octopart_client is None


async def test_sdk_builds_octopart_client_from_env_keys(tmp_path, monkeypatch):
    """כאשר OCTOPART_CLIENT_ID/SECRET מוגדרים בסביבה, ה-SDK אמור להקים OctopartClient דרך ה-Gatekeeper אוטומטית."""
    monkeypatch.setenv("OCTOPART_CLIENT_ID", "fake_id_from_env")
    monkeypatch.setenv("OCTOPART_CLIENT_SECRET", "fake_secret_from_env")
    db_file = tmp_path / "test_cases.db"

    instance = ShalomCI_SDK(db_path=str(db_file))
    try:
        assert isinstance(instance.cross_ref.octopart_client, OctopartClient)
        assert instance.cross_ref.octopart_client.client_id == "fake_id_from_env"
        assert instance.cross_ref.octopart_client.gatekeeper is instance.gatekeeper
    finally:
        await instance.close()


async def test_sdk_explicit_octopart_client_overrides_env(tmp_path, monkeypatch):
    """אם מוזרק octopart_client ידנית, הוא גובר על בניית ברירת המחדל מהסביבה."""
    monkeypatch.setenv("OCTOPART_CLIENT_ID", "fake_id_from_env")
    monkeypatch.setenv("OCTOPART_CLIENT_SECRET", "fake_secret_from_env")
    db_file = tmp_path / "test_cases.db"
    injected_client = AsyncMock()

    instance = ShalomCI_SDK(db_path=str(db_file), octopart_client=injected_client)
    try:
        assert instance.cross_ref.octopart_client is injected_client
    finally:
        await instance.close()


async def test_enrich_components_merges_octopart_fields_alongside_others(sdk):
    """מוודא ש-enrich_components ממזג גם את שדות ה-Octopart (side-by-side) לצד Mouser/DigiKey."""
    await sdk.initialize()
    sdk.cross_ref.get_octopart_data = AsyncMock(return_value={
        "octopart_lifecycle": "פעיל",
        "octopart_inventory": "Octopart: 900",
        "octopart_lead_time": "זמן אספקה: 12 ימים",
        "octopart_price_per_unit": "$0.77",
    })
    components = [{"mpn": "NE555"}]

    await sdk.enrich_components(components)

    assert components[0]["octopart_lifecycle"] == "פעיל"
    assert components[0]["octopart_inventory"] == "Octopart: 900"
    assert components[0]["octopart_price_per_unit"] == "$0.77"
    sdk.cross_ref.get_octopart_data.assert_awaited_once_with("NE555")
