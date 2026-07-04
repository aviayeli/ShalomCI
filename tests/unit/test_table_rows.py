import pytest

from src.gui.table_rows import build_rows, recommended_vendor, status_icon, summarize_risk


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
    """מוודא שרכיב ללא נתונים (למשל כשלון העשרה) מקבל ברירות מחדל תקינות, כולל מחיר/מלאי לכל ספק."""
    rows = build_rows([{}])

    assert rows[0]["מק\"ט"] == "N/A"
    assert rows[0]["יצרן"] == "N/A"
    assert rows[0]["סטטוס"] == "❓ N/A"
    assert rows[0]["ציון סיכון"] == 0
    assert rows[0]["ספק מומלץ"] == "לא ידוע"
    for label in ("Mouser", "DigiKey", "Octopart"):
        assert rows[0][f"מחיר - {label}"] is None
        assert rows[0][f"מלאי - {label}"] is None
    assert rows[0]["חלופה מוצעת"] == "אין"
    assert rows[0]["אספקה - DigiKey"] == "זמן אספקה: לא ידוע"
    assert rows[0]["אספקה - Octopart"] == "זמן אספקה: לא ידוע"


def test_build_rows_includes_extended_mouser_fields():
    """מוודא שהעמודות המורחבות (מחיר/מלאי, זמן אספקה, חלופה, RoHS, אריזה) מוצגות כראוי."""
    components = [{
        "mpn": "NE555", "manufacturer": "TI", "lifecycle_status": "פעיל", "risk_score": 5,
        "mouser_stock_qty": 24755.0,
        "mouser_price_value": 1.85,
        "lead_time": "זמן אספקה: 63 ימים",
        "suggested_replacement": "NE555DR-ALT",
        "rohs_status": "תואם RoHS",
        "packaging": "Cut Tape",
    }]

    rows = build_rows(components)

    assert rows[0]["מלאי - Mouser"] == 24755.0
    assert rows[0]["מחיר - Mouser"] == 1.85
    assert rows[0]["אספקה - Mouser"] == "זמן אספקה: 63 ימים"
    assert rows[0]["חלופה מוצעת"] == "NE555DR-ALT"
    assert rows[0]["תאימות RoHS"] == "תואם RoHS"
    assert rows[0]["צורת אריזה"] == "Cut Tape"


def test_build_rows_includes_digikey_and_octopart_price_stock_side_by_side_with_mouser():
    """מוודא שמחיר/מלאי של שלושת הספקים מוצגים בעמודות נפרדות משלהם, ללא עמודות מחזור חיים כפולות."""
    components = [{
        "mpn": "NE555", "manufacturer": "TI", "lifecycle_status": "פעיל", "risk_score": 5,
        "mouser_stock_qty": 24755.0, "mouser_price_value": 1.85,
        "digikey_stock_qty": 1200.0, "digikey_price_value": 1.2,
        "digikey_lead_time": "זמן אספקה: 4 שבועות",
        "octopart_stock_qty": 3400.0, "octopart_price_value": 0.95,
        "octopart_lead_time": "זמן אספקה: 12 ימים",
    }]

    rows = build_rows(components)

    assert rows[0]["מלאי - Mouser"] == 24755.0
    assert rows[0]["מלאי - DigiKey"] == 1200.0
    assert rows[0]["מחיר - DigiKey"] == 1.2
    assert rows[0]["אספקה - DigiKey"] == "זמן אספקה: 4 שבועות"
    assert rows[0]["מלאי - Octopart"] == 3400.0
    assert rows[0]["מחיר - Octopart"] == 0.95
    assert rows[0]["אספקה - Octopart"] == "זמן אספקה: 12 ימים"
    assert "מחזור חיים (DigiKey)" not in rows[0]
    assert "מחזור חיים (Octopart)" not in rows[0]


def test_recommended_vendor_picks_cheapest_price_among_available():
    """מוודא שהספק המומלץ הוא זה עם המחיר הנמוך ביותר, כשקיימים כמה מחירים."""
    c = {"mouser_price_value": 1.85, "digikey_price_value": 1.2, "octopart_price_value": 0.95}
    assert recommended_vendor(c) == "Octopart"


def test_recommended_vendor_ignores_none_prices_not_zero():
    """מוודא ש-None (אין נתון) לא 'מנצח' מחיר אמיתי, גם אם קטן ממנו כמו 0."""
    c = {"mouser_price_value": None, "digikey_price_value": 0.5, "octopart_price_value": None}
    assert recommended_vendor(c) == "DigiKey"


def test_recommended_vendor_falls_back_to_highest_stock_without_any_price():
    """כשאין אף מחיר זמין, הספק המומלץ הוא זה עם המלאי הגבוה ביותר."""
    c = {"mouser_stock_qty": 500.0, "digikey_stock_qty": 1200.0, "octopart_stock_qty": 300.0}
    assert recommended_vendor(c) == "DigiKey"


def test_recommended_vendor_unknown_without_any_price_or_stock():
    """כשאין אף נתון מספק כלשהו, הספק המומלץ הוא 'לא ידוע' ולא קורס."""
    assert recommended_vendor({}) == "לא ידוע"


def test_summarize_risk_buckets_scores_into_categories():
    """מוודא ש-summarize_risk מסווג נכון ציונים לקטגוריות קריטי/אזהרה/תקין וסופר total."""
    components = [
        {"risk_score": 1}, {"risk_score": 2}, {"risk_score": 3},
        {"risk_score": 4}, {"risk_score": 5},
    ]
    assert summarize_risk(components) == {"total": 5, "critical": 1, "warning": 2, "healthy": 2}


def test_summarize_risk_empty_list_returns_zeros():
    """מוודא שרשימה ריקה מחזירה אפסים בכל הקטגוריות ולא קורסת."""
    assert summarize_risk([]) == {"total": 0, "critical": 0, "warning": 0, "healthy": 0}


def test_summarize_risk_unknown_score_counted_only_in_total():
    """מוודא שציון לא ידוע (0 / חסר) נספר ב-total בלבד ולא באף קטגוריית משנה."""
    summary = summarize_risk([{"risk_score": 0}, {}])
    assert summary == {"total": 2, "critical": 0, "warning": 0, "healthy": 0}
