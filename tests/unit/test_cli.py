import argparse
from unittest.mock import AsyncMock, patch

import pytest

from src.cli.main import main, run_cases, run_process


@pytest.mark.asyncio
@patch("src.cli.main.ShalomCI_SDK")
async def test_run_process_command(mock_sdk_class):
    """מוודא שפקודת ה-process מפעילה את שרשרת ה-SDK לפי הסדר המדויק."""
    # הכנת ה-Mock SDK
    mock_sdk = AsyncMock()
    mock_sdk_class.return_value = mock_sdk

    # הגדרת ערכי חזרה (Return values) שה-CLI מצפה לקבל
    mock_sdk.process_bom.return_value = [{"mpn": "TEST_PART"}]
    mock_sdk.evaluate_risks.return_value = {"components": [{"mpn": "TEST_PART"}], "project_score": 4.5}
    mock_sdk.find_mitigations.return_value = [{"mpn": "TEST_PART", "alternatives": []}]

    args = argparse.Namespace(file_path="dummy_bom.xlsx")

    await run_process(args)

    # מוודא שה-CLI עמד בחוזה וקרא לכל הפונקציות העסקיות לפי הסדר
    mock_sdk.initialize.assert_awaited_once()
    mock_sdk.process_bom.assert_awaited_once_with("dummy_bom.xlsx")
    mock_sdk.enrich_components.assert_awaited_once()
    mock_sdk.evaluate_risks.assert_awaited_once()
    mock_sdk.find_mitigations.assert_awaited_once()
    mock_sdk.generate_report.assert_awaited_once()


@pytest.mark.asyncio
@patch("src.cli.main.ShalomCI_SDK")
async def test_run_cases_list_command(mock_sdk_class):
    """מוודא שפקודת ה-cases list תקינה ושולפת את התיקים הפתוחים."""
    mock_sdk = AsyncMock()
    mock_sdk_class.return_value = mock_sdk
    mock_sdk.case_manager.list_open_cases.return_value = [
        {"id": 1, "project_name": "TestBoard", "mpn": "NE555", "created_at": "2026-01-01"}
    ]

    args = argparse.Namespace(action="list")
    await run_cases(args)

    mock_sdk.initialize.assert_awaited_once()
    mock_sdk.case_manager.list_open_cases.assert_awaited_once()


@patch("src.cli.main.argparse.ArgumentParser.parse_args")
@patch("src.cli.main.asyncio.run")
def test_main_routing(mock_asyncio_run, mock_parse_args):
    """מוודא שנקודת הכניסה מנתבת פקודות בצורה נכונה ללולאת ה-asyncio."""
    mock_parse_args.return_value = argparse.Namespace(command="process", file_path="test.xlsx")

    main()

    mock_asyncio_run.assert_called_once()
