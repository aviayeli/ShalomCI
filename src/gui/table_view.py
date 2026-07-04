import math

import streamlit as st

from src.gui.table_render import render_table
from src.gui.table_rows import PRICE_STOCK_VENDORS

# גדלי עמוד נתמכים (הגנת DOM): ה-Styler מרנדר כל שורה כ-HTML ומזריק ל-DOM הראשי; BOM גדול
# (מאות/אלפי רכיבים) היה מקפיא את הדפדפן. ברירת המחדל (הראשון) = 50 שורות לעמוד.
PAGE_SIZES = [50, 100]


def paginate(df, page: int, page_size: int):
    """חותך עמוד יחיד מה-DataFrame ומחזיר (slice, total_pages) - פונקציה טהורה, ניתנת לבדיקה.
    ה-page עובר clamp לטווח [1, total_pages] במקום לזרוק KeyError: סינון עשוי לכווץ את מספר
    התוצאות בין rerun-ים, כך שמספר עמוד ש"נשמר" מ-rerun קודם עלול לחרוג מהטווח החדש.
    df ריק -> total_pages=1 ו-slice ריק (המשתמש עדיין רואה מבנה תקין, לא קריסה)."""
    total_rows = len(df)
    total_pages = max(1, math.ceil(total_rows / page_size))
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    return df.iloc[start:start + page_size], total_pages


def range_caption(page: int, page_size: int, total_rows: int) -> str:
    """מחשב את כיתוב טווח התצוגה "מציג X–Y מתוך Z רכיבים" (פונקציה טהורה, ניתנת לבדיקה).
    total_rows=0 -> "מציג 0 רכיבים" (אין טווח להציג). ה-en-dash (–) מפריד את גבולות הטווח."""
    if total_rows == 0:
        return "מציג 0 רכיבים"
    start = (page - 1) * page_size + 1
    end = min(page * page_size, total_rows)
    return f"מציג {start}–{end} מתוך {total_rows} רכיבים"


def render_vendor_highlight_pills():  # pragma: no cover - חיווט Streamlit בלבד (Proxy)
    """בורר תגיות (st.pills, selection_mode='single') לבחירת ספק להדגשה אנכית. Streamlit
    מריץ rerun אוטומטי בכל שינוי בחירה - זהו מנגנון ה-state שמפעיל את הרינדור מחדש עם
    ההדגשה. מחזיר את שם הספק שנבחר, או None כשאין בחירה (ואז אין הדגשה)."""
    return st.pills(
        "🎯 הדגשת עמודות ספק",
        options=list(PRICE_STOCK_VENDORS.keys()),
        selection_mode="single",
        help="בחרו ספק כדי להדגיש את עמודות המחיר, המלאי והאספקה שלו לכל אורך הטבלה.",
    )


def render_table_view(df):  # pragma: no cover - חיווט Streamlit בלבד (Proxy); הלוגיקה נבדקת בנפרד
    """חיווט מלא של אזור הטבלה: בורר הדגשת ספק, בקרות עימוד, וקריאה ל-render_table על עמוד
    הנתונים הנוכחי בלבד. חשוב: החיתוך כאן הוא לתצוגה בלבד - הורדת ה-CSV (ב-app.py) עדיין
    מייצאת את ה-df המלא המסונן. BOM קטן (<=גודל עמוד ברירת מחדל): אין בקרות עימוד (מניעת עומס)."""
    highlight = render_vendor_highlight_pills()
    total = len(df)

    if total <= PAGE_SIZES[0]:
        st.caption(range_caption(1, PAGE_SIZES[0], total))
        render_table(df, highlight)
        return

    ctrl_size, ctrl_page, ctrl_caption = st.columns([1, 1, 2])
    page_size = ctrl_size.selectbox("שורות בעמוד", options=PAGE_SIZES)
    total_pages = max(1, math.ceil(total / page_size))
    page = int(ctrl_page.number_input("עמוד", min_value=1, max_value=total_pages, value=1, step=1))
    page_df, _ = paginate(df, page, page_size)
    ctrl_caption.caption(range_caption(page, page_size, total))
    render_table(page_df, highlight)
