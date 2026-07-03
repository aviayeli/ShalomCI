from unittest.mock import AsyncMock, patch

import pytest

from src.gui.app import run_analysis


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
