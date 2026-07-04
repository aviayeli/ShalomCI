"""עיצוב תאי טבלה (formatters ל-pandas.Styler): הברחת HTML ידנית + בידוד Bidi.

פוצל מ-table_render.py לפי חוק 150 השורות (V3). כל הפונקציות כאן פולטות HTML גולמי
שמוזרק ל-DOM הראשי (st.html, ללא iframe) - ולכן כל אחת אחראית להבריח (html.escape)
את התוכן בעצמה; הן מופעלות ב-format ללא escape="html" (שהיה בורח את התגיות עצמן).
"""
import html

import pandas as pd

# צבעי תג ("pill") לכל ספק מומלץ - מראה "ממשלתי" נקי; slug נייטרלי ל"לא ידוע".
# נצרך גם ב-table_render (יצירת כללי ה-CSS של ה-Styler) ולכן פומבי.
VENDOR_BADGE_COLORS = {
    "mouser": ("#0056B3", "#FFFFFF"), "digikey": ("#CC0000", "#FFFFFF"),
    "octopart": ("#00857C", "#FFFFFF"), "unknown": ("#E3E8EF", "#475467"),
}
_VENDOR_SLUGS = {"Mouser": "mouser", "DigiKey": "digikey", "Octopart": "octopart"}

_HEBREW_CHARS = set(map(chr, range(0x0590, 0x0600)))


def _ltr(text: str) -> str:
    """עוטף טקסט (שכבר הוברח!) ב-<bdo dir="ltr"> - בידוד Bidi כפוי לתוכן לטיני/מספרי בהקשר
    RTL, לפי מערכת העיצוב (DESIGN.md סעיף 3). ה-CSS הגלובלי (DESIGN_CSS) קובע ל-bdo
    unicode-bidi: isolate, כך שהעטיפה מבודדת את הרצף מסביבתו העברית בלי להפוך את תוכנו."""
    return f'<bdo dir="ltr">{text}</bdo>'


def price_text(value) -> str:
    """מעצב מחיר: ערך מספרי נעטף ב-bdo (רצף "₪ 1,234.56" נשאר בסדר קריאה LTR); המחרוזת
    העברית "לא זמין" נשארת חשופה - כפיית LTR על עברית הייתה מציגה אותה הפוך."""
    return "לא זמין" if pd.isna(value) else _ltr(f"₪ {value:,.2f}")


def stock_text(value) -> str:
    return "לא ידוע" if pd.isna(value) else _ltr(f"{value:,.0f}")


def mpn_bidi(value) -> str:
    """עוטף מק"ט ב-<bdo dir="ltr"> כדי שמחרוזת אלפאנומרית/לטינית לא תתהפך/תישבר בהקשר RTL
    (מערכת העיצוב מחייבת bdo, בעבר <bdi>). ה-HTML מוברח ידנית (html.escape) כי escape="html"
    הכללי של Styler היה בורח גם את התגית עצמה."""
    return _ltr(html.escape(str(value)))


def latin_ltr(value) -> str:
    """מבריח ערך טקסטואלי מעורב (זמני אספקה/תאריכים לועזיים/רשימות מק"ט חלופיות) ועוטף אותו
    ב-<bdo dir="ltr"> רק אם אין בו אף תו עברי - טקסט עברי ("זמן אספקה: לא ידוע") שייכפה
    ל-LTR היה מתרנדר הפוך, ולכן נשאר חשוף בהקשר ה-RTL הטבעי."""
    text = str(value)
    escaped = html.escape(text)
    return escaped if _HEBREW_CHARS.intersection(text) else _ltr(escaped)


def vendor_badge(value) -> str:
    """עוטף את הספק המומלץ בתג ("pill") מעוצב. ה-HTML מוברח ידנית (html.escape) בדיוק כמו
    ב-mpn_bidi, כי format ללא escape="html" אינו מבריח את הפלט שלנו - קריטי למניעת XSS."""
    text = str(value)
    slug = _VENDOR_SLUGS.get(text, "unknown")
    return f'<span class="vendor-badge vendor-badge-{slug}">{html.escape(text)}</span>'


def risk_color(value) -> str:
    if value == 1:
        return "background-color: #FFCCCC"
    if value in (2, 3):
        return "background-color: #FFFFCC"
    return "background-color: #CCFFCC"
