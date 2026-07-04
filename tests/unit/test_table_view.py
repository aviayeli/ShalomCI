import pandas as pd

from src.gui.table_view import PAGE_SIZES, paginate, range_caption


def _df(n: int) -> pd.DataFrame:
    """בונה DataFrame בגודל n עם עמודת מזהה רציפה לבדיקת גבולות החיתוך."""
    return pd.DataFrame({"idx": list(range(n))})


def test_paginate_slices_first_page_and_reports_total_pages():
    """מוודא ש-paginate מחזיר את שורות העמוד הראשון בלבד + מספר עמודות כולל נכון."""
    page_df, total_pages = paginate(_df(120), page=1, page_size=50)
    assert list(page_df["idx"]) == list(range(50))
    assert total_pages == 3


def test_paginate_middle_page_offsets_correctly():
    """מוודא שהחיתוך של עמוד פנימי מתחיל בהיסט הנכון (page-1)*page_size."""
    page_df, _ = paginate(_df(120), page=2, page_size=50)
    assert list(page_df["idx"]) == list(range(50, 100))


def test_paginate_exact_multiple_has_no_trailing_page():
    """מוודא שכאשר סך השורות הוא כפולה מדויקת של גודל העמוד - אין עמוד עודף ריק."""
    page_df, total_pages = paginate(_df(100), page=2, page_size=50)
    assert total_pages == 2
    assert list(page_df["idx"]) == list(range(50, 100))


def test_paginate_clamps_page_above_range():
    """מוודא ש-page מעבר לטווח (סינון שכיווץ תוצאות) עובר clamp לעמוד האחרון, ללא KeyError."""
    page_df, total_pages = paginate(_df(60), page=99, page_size=50)
    assert total_pages == 2
    assert list(page_df["idx"]) == [50, 51, 52, 53, 54, 55, 56, 57, 58, 59]


def test_paginate_clamps_page_below_one():
    """מוודא ש-page קטן מ-1 עובר clamp לעמוד הראשון."""
    page_df, _ = paginate(_df(60), page=0, page_size=50)
    assert list(page_df["idx"]) == list(range(50))


def test_paginate_empty_df_returns_single_page_and_empty_slice():
    """מוודא ש-DataFrame ריק מחזיר total_pages=1 ו-slice ריק (מבנה תקין, לא קריסה)."""
    page_df, total_pages = paginate(_df(0), page=1, page_size=50)
    assert total_pages == 1
    assert len(page_df) == 0


def test_range_caption_reports_visible_window():
    """מוודא שכיתוב הטווח מציג את X–Y הנכונים מתוך Z הכולל."""
    assert range_caption(page=2, page_size=50, total_rows=120) == "מציג 51–100 מתוך 120 רכיבים"


def test_range_caption_last_page_caps_end_at_total():
    """מוודא שבעמוד האחרון (חלקי) גבול הסוף (Y) לא חורג מסך השורות הכולל."""
    assert range_caption(page=3, page_size=50, total_rows=120) == "מציג 101–120 מתוך 120 רכיבים"


def test_range_caption_empty_reports_zero():
    """מוודא ש-0 רכיבים מציג כיתוב 'מציג 0 רכיבים' ללא טווח."""
    assert range_caption(page=1, page_size=50, total_rows=0) == "מציג 0 רכיבים"


def test_default_page_size_is_fifty():
    """מוודא שברירת המחדל (הראשון ברשימה) היא 50 שורות לעמוד, עם אפשרות 100."""
    assert PAGE_SIZES == [50, 100]
