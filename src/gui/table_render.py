import html

import pandas as pd
import streamlit as st

from src.gui.table_rows import MPN_COLUMN, PRICE_COLUMN_PREFIX, PRICE_STOCK_VENDORS, STOCK_COLUMN_PREFIX

# פונט מותאם עברית (אותיות עבריות "קטנות" חזותית מלטיניות באותו גודל נומינלי), ללא
# italics וללא letter-spacing נוסף - טיפוגרפיה נגישה (WCAG) לקריאות עברית מיטבית.
_FONT_STACK = "'Assistant', 'Heebo', 'Noto Sans Hebrew', 'Segoe UI', sans-serif"

# "פרדוקס היישור": הטבלה כולה RTL, אך מספרים (מחיר/מלאי) ומק"ט (אלפאנומרי/לטיני בדרך
# כלל) מיושרים end (שמאל) כדי שהספרות יתלכדו טור-מול-טור בין שורות להשוואה נוחה; טקסט
# עברי וכל כותרות העמודות מיושרים start (ימין) כברירת מחדל דרך _TABLE_STYLES.
_END_ALIGNED_COLUMNS = [MPN_COLUMN] + [
    f"{prefix}{label}" for prefix in (PRICE_COLUMN_PREFIX, STOCK_COLUMN_PREFIX) for label in PRICE_STOCK_VENDORS
]

# CSS מקובע ל-Styler (scoped אוטומטית על ידי pandas לתחילית ה-id הייחודית של הטבלה, כך
# שלא דולף/מתנגש עם שאר העמוד) - RTL לוגי (start/end), sticky header, וטיפוגרפיה נגישה.
_TABLE_STYLES = [
    {"selector": "table", "props": [
        ("direction", "rtl"), ("width", "100%"), ("border-collapse", "collapse"),
        ("font-family", _FONT_STACK), ("font-size", "1rem"), ("line-height", "1.5"),
        ("font-style", "normal"), ("letter-spacing", "normal"),
    ]},
    {"selector": "thead th", "props": [
        ("position", "sticky"), ("top", "0"), ("background-color", "#0056B3"), ("color", "white"),
        ("z-index", "1000"), ("padding", "10px"), ("text-align", "start"),
        ("box-shadow", "0 2px 2px -1px rgba(0,0,0,0.4)"),
    ]},
    {"selector": "td", "props": [("border", "1px solid #ddd"), ("padding", "8px"), ("text-align", "start")]},
]


def _price_text(value) -> str:
    return "לא זמין" if pd.isna(value) else f"₪ {value:,.2f}"


def _stock_text(value) -> str:
    return "לא ידוע" if pd.isna(value) else f"{value:,.0f}"


def _mpn_bidi(value) -> str:
    """עוטף מק"ט ב-<bdi> כדי שמחרוזת אלפאנומרית/לטינית לא תתהפך/תישבר בהקשר RTL. ה-HTML
    מוברח ידנית (html.escape) כי escape="html" הכללי של Styler היה בורח גם את ה-<bdi> עצמו."""
    return f"<bdi>{html.escape(str(value))}</bdi>"


def _risk_color(value) -> str:
    if value == 1:
        return "background-color: #FFCCCC"
    if value in (2, 3):
        return "background-color: #FFFFCC"
    return "background-color: #CCFFCC"


def render_table(df: pd.DataFrame) -> None:  # pragma: no cover - חיווט Streamlit בלבד (Proxy)
    """
    מרנדר את טבלת הרכיבים כטבלת HTML טהורה (pandas.Styler -> st.html) - לא st.dataframe
    (ה-grid הפנימי מצויר על canvas ושובר RTL עברי לחלוטין) ולא st.iframe/components.html
    (בעיות WebSocket/רינדור iframe). st.html מזריק ישירות ל-DOM הראשי (לא iframe מבודד),
    כך שה-CSS של ה-Styler עצמו שולט לגמרי על ה-RTL/הטיפוגרפיה בלי תלות ב-CSS הגלובלי.

    אזהרת אבטחה: מאחר שהטבלה מוזרקת ל-DOM הראשי (לא מבודדת ב-iframe כמו קודם), format
    עם escape="html" הוא קריטי - חובה למנוע החדרת קוד (XSS) מערכים שמקורם ב-BOM שהועלה
    או בתגובות API חיצוניות (לא מהימנים) לתוך שאר האפליקציה, לא רק לתוך iframe מבודד.
    """
    formatters = {}
    for label in PRICE_STOCK_VENDORS:
        formatters[f"{PRICE_COLUMN_PREFIX}{label}"] = _price_text
        formatters[f"{STOCK_COLUMN_PREFIX}{label}"] = _stock_text

    table_html = (
        df.style
        .hide(axis="index")
        .format(escape="html")
        .format(formatter=formatters, escape="html")
        .format(_mpn_bidi, subset=[MPN_COLUMN])
        .map(_risk_color, subset=["ציון סיכון"])
        .set_properties(subset=_END_ALIGNED_COLUMNS, **{"text-align": "end !important"})
        .set_table_styles(_TABLE_STYLES)
        .set_table_attributes('role="table"')
        .to_html()
        .replace("<th ", '<th scope="col" ')
    )
    full_html = f'<div role="region" aria-label="טבלת נתוני רכיבים מועשרים" tabindex="0">{table_html}</div>'
    st.html(full_html)
