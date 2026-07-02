import pandas as pd
import pytest

from src.gui.table_controls import available_statuses, filter_and_sort, sort_options


@pytest.fixture
def sample_df():
    return pd.DataFrame([
        {"מק\"ט": "NE555", "יצרן": "TI", "סטטוס": "✅ Active", "ציון סיכון": 5,
         "מחיר ליחידה": "₪1.85", "זמן אספקה": "זמן אספקה: 63 ימים"},
        {"מק\"ט": "PART_EOL", "יצרן": "Infineon", "סטטוס": "⛔ Obsolete", "ציון סיכון": 1,
         "מחיר ליחידה": "₪12.40", "זמן אספקה": "זמן אספקה: 200 ימים"},
        {"מק\"ט": "PART_NRND", "יצרן": "TI", "סטטוס": "⚠️ NRND", "ציון סיכון": 3,
         "מחיר ליחידה": "לא זמין", "זמן אספקה": "זמן אספקה: לא ידוע"},
    ])


def test_sort_options_returns_all_dataframe_columns_dynamically(sample_df):
    """אפשרויות המיון חייבות להיגזר מכל עמודות ה-DataFrame בפועל, כדי שעמודה חדשה תופיע אוטומטית."""
    assert sort_options(sample_df) == list(sample_df.columns)


def test_sort_options_reflects_added_column(sample_df):
    """הוספת עמודה חדשה ל-DataFrame (למשל בעתיד) אמורה להופיע מיידית באפשרויות המיון, ללא רשימה קבועה."""
    extended_df = sample_df.assign(**{"עמודה חדשה": ["א", "ב", "ג"]})
    assert "עמודה חדשה" in sort_options(extended_df)


def test_available_statuses_strips_accessibility_icon(sample_df):
    """מוודא שרשימת הסטטוסים לתפריט הסינון לא כוללת את אייקון הנגישות, רק את הטקסט."""
    assert available_statuses(sample_df) == ["Active", "NRND", "Obsolete"]


def test_filter_by_search_matches_mpn_or_manufacturer(sample_df):
    """חיפוש חופשי אמור להתאים גם למק\"ט וגם ליצרן, ללא תלות ברישיות."""
    result = filter_and_sort(sample_df, "infineon", [], None, True)
    assert list(result["מק\"ט"]) == ["PART_EOL"]

    result = filter_and_sort(sample_df, "ne555", [], None, True)
    assert list(result["מק\"ט"]) == ["NE555"]


def test_filter_by_status_multiselect(sample_df):
    """סינון לפי סטטוס מחזור חיים אמור להשאיר רק שורות שסטטוסן נבחר."""
    result = filter_and_sort(sample_df, "", ["Obsolete", "NRND"], None, True)
    assert set(result["מק\"ט"]) == {"PART_EOL", "PART_NRND"}


def test_sort_by_risk_score_numeric(sample_df):
    """מיון לפי עמודה מספרית (ציון סיכון) אמור לפעול כרגיל, עולה ויורד."""
    ascending = filter_and_sort(sample_df, "", [], "ציון סיכון", True)
    assert list(ascending["ציון סיכון"]) == [1, 3, 5]

    descending = filter_and_sort(sample_df, "", [], "ציון סיכון", False)
    assert list(descending["ציון סיכון"]) == [5, 3, 1]


def test_sort_by_price_extracts_numeric_value_from_formatted_text(sample_df):
    """מחיר מאוחסן כטקסט מפורמט ("₪1.85") - המיון חייב לפרש אותו כמספר, לא לקסיקוגרפית."""
    result = filter_and_sort(sample_df, "", [], "מחיר ליחידה", True)
    assert list(result["מק\"ט"]) == ["NE555", "PART_EOL", "PART_NRND"]


def test_sort_by_lead_time_puts_unknown_values_last_regardless_of_order(sample_df):
    """ערך זמן אספקה לא ידוע לא אמור "לזכות" במיון יורד - הוא תמיד נדחק לסוף."""
    ascending = filter_and_sort(sample_df, "", [], "זמן אספקה", True)
    assert list(ascending["מק\"ט"])[-1] == "PART_NRND"

    descending = filter_and_sort(sample_df, "", [], "זמן אספקה", False)
    assert list(descending["מק\"ט"])[-1] == "PART_NRND"


def test_no_filters_or_sort_returns_original_rows(sample_df):
    """ללא חיפוש, סינון או מיון, כל השורות המקוריות אמורות לחזור כפי שהן."""
    result = filter_and_sort(sample_df, "", [], None, True)
    assert list(result["מק\"ט"]) == list(sample_df["מק\"ט"])
