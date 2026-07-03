import pytest

from src.gui.table_rows import build_rows, status_icon


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
    """מוודא שרכיב ללא נתונים (למשל כשלון העשרה) מקבל ברירות מחדל תקינות, כולל DigiKey/Octopart."""
    rows = build_rows([{}])

    assert rows[0]["מק\"ט"] == "N/A"
    assert rows[0]["יצרן"] == "N/A"
    assert rows[0]["סטטוס"] == "❓ N/A"
    assert rows[0]["ציון סיכון"] == 0
    assert rows[0]["מלאי"] == "לא ידוע"
    assert rows[0]["חלופה מוצעת (Mouser)"] == "אין"
    assert rows[0]["מחזור חיים (DigiKey)"] == "לא ידוע"
    assert rows[0]["מלאי (DigiKey)"] == "DigiKey: לא ידוע"
    assert rows[0]["זמן אספקה (DigiKey)"] == "זמן אספקה: לא ידוע"
    assert rows[0]["מחיר ליחידה (DigiKey)"] == "לא זמין"
    assert rows[0]["מחזור חיים (Octopart)"] == "לא ידוע"
    assert rows[0]["מלאי (Octopart)"] == "Octopart: לא ידוע"
    assert rows[0]["זמן אספקה (Octopart)"] == "זמן אספקה: לא ידוע"
    assert rows[0]["מחיר ליחידה (Octopart)"] == "לא זמין"


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


def test_build_rows_includes_digikey_fields_side_by_side_with_mouser():
    """מוודא ששדות DigiKey מוצגים בעמודות נפרדות משלהן, לצד נתוני Mouser הקיימים באותה שורה."""
    components = [{
        "mpn": "NE555", "manufacturer": "TI", "lifecycle_status": "פעיל", "risk_score": 5,
        "inventory": "Mouser: 24,755 במלאי",
        "digikey_lifecycle": "פעיל",
        "digikey_inventory": "DigiKey: 1,200",
        "digikey_lead_time": "זמן אספקה: 4 שבועות",
        "digikey_price_per_unit": "$1.20",
    }]

    rows = build_rows(components)

    assert rows[0]["מלאי"] == "Mouser: 24,755 במלאי"
    assert rows[0]["מחזור חיים (DigiKey)"] == "פעיל"
    assert rows[0]["מלאי (DigiKey)"] == "DigiKey: 1,200"
    assert rows[0]["זמן אספקה (DigiKey)"] == "זמן אספקה: 4 שבועות"
    assert rows[0]["מחיר ליחידה (DigiKey)"] == "$1.20"


def test_build_rows_includes_octopart_fields_side_by_side_with_mouser_and_digikey():
    """מוודא ששדות Octopart מוצגים בעמודות נפרדות משלהן, לצד Mouser ו-DigiKey באותה שורה."""
    components = [{
        "mpn": "NE555", "manufacturer": "TI", "lifecycle_status": "פעיל", "risk_score": 5,
        "inventory": "Mouser: 24,755 במלאי",
        "digikey_inventory": "DigiKey: 1,200",
        "octopart_lifecycle": "פעיל",
        "octopart_inventory": "Octopart: 3,400",
        "octopart_lead_time": "זמן אספקה: 12 ימים",
        "octopart_price_per_unit": "$0.95",
    }]

    rows = build_rows(components)

    assert rows[0]["מלאי"] == "Mouser: 24,755 במלאי"
    assert rows[0]["מלאי (DigiKey)"] == "DigiKey: 1,200"
    assert rows[0]["מחזור חיים (Octopart)"] == "פעיל"
    assert rows[0]["מלאי (Octopart)"] == "Octopart: 3,400"
    assert rows[0]["זמן אספקה (Octopart)"] == "זמן אספקה: 12 ימים"
    assert rows[0]["מחיר ליחידה (Octopart)"] == "$0.95"
