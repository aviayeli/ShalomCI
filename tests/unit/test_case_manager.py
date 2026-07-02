import pytest

from src.data.case_manager import CaseManager


# משתמשים ב-tmp_path כדי לייצר קובץ זמני אמיתי שנמחק בסוף הטסט
@pytest.fixture
def case_manager(tmp_path):
    db_file = tmp_path / "test_cases.db"
    return CaseManager(db_path=str(db_file))


async def test_init_db_and_open_case(case_manager):
    await case_manager.init_db()
    case_id = await case_manager.open_case(mpn="NE555P", project_name="TestBoard_v1")

    assert case_id == 1, "התיק הראשון אמור לקבל מזהה 1"


async def test_list_and_close_cases(case_manager):
    await case_manager.init_db()
    await case_manager.open_case(mpn="LM324", project_name="SensorHub")

    cases = await case_manager.list_open_cases()
    assert len(cases) == 1, "אמור להיות תיק פתוח אחד"
    assert cases[0]["mpn"] == "LM324"

    await case_manager.close_case(cases[0]["id"])
    open_cases_after = await case_manager.list_open_cases()
    assert len(open_cases_after) == 0, "לא אמורים להיות תיקים פתוחים לאחר סגירה"
