import html

import pandas as pd
import streamlit as st

from src.gui.table_rows import (LEAD_TIME_COLUMN_PREFIX, MPN_COLUMN, PRICE_COLUMN_PREFIX,
                                PRICE_STOCK_VENDORS, STOCK_COLUMN_PREFIX, vendor_columns)

# פונט מותאם עברית (אותיות עבריות "קטנות" חזותית מלטיניות באותו גודל נומינלי), ללא
# italics וללא letter-spacing נוסף - טיפוגרפיה נגישה (WCAG) לקריאות עברית מיטבית.
_FONT_STACK = "'Assistant', 'Heebo', 'Noto Sans Hebrew', 'Segoe UI', sans-serif"

# "פרדוקס היישור": הטבלה כולה RTL, אך מספרים (מחיר/מלאי/ציון סיכון) ומק"ט (אלפאנומרי/לטיני
# בדרך כלל) מיושרים end (שמאל) כדי שהספרות יתלכדו טור-מול-טור בין שורות להשוואה נוחה; טקסט
# עברי וכל כותרות העמודות מיושרים start (ימין) כברירת מחדל דרך _TABLE_STYLES.
# היישור חייב לעבור דרך set_properties של ה-Styler (inline !important): כלל ה-* הגלובלי
# (text-align: start !important ב-RTL_CSS) וכללי ה-#T_xxx גוברים על .sci-table td.num.
_PRICE_COLUMNS = [f"{PRICE_COLUMN_PREFIX}{label}" for label in PRICE_STOCK_VENDORS]
_STOCK_COLUMNS = [f"{STOCK_COLUMN_PREFIX}{label}" for label in PRICE_STOCK_VENDORS]
_LEAD_TIME_COLUMNS = [f"{LEAD_TIME_COLUMN_PREFIX}{label}" for label in PRICE_STOCK_VENDORS]
_END_ALIGNED_COLUMNS = [MPN_COLUMN] + _PRICE_COLUMNS + _STOCK_COLUMNS + ["ציון סיכון"]

# עמודות נתונים מספריים - מקבלות class="num" (על ה-td דרך set_td_classes ועל כותרת ה-th
# בפוסט-עיבוד), עבור ספרות טבלאיות (tabular-nums) מכללי מערכת העיצוב (.sci-table .num).
_NUMERIC_COLUMNS = _PRICE_COLUMNS + _STOCK_COLUMNS + ["ציון סיכון"]

# המלצות ויזואליות (אפיון סעיף 5): nowrap על עמודות מספריות (התלכדות ספרות טור-מול-טור);
# מפריד border בתחילת כל בלוק מדד (תיחום 3 בלוקי ההשוואה); גלישת זנב ארוך (רשימות MPN)
# לשורה במקום מתיחת הטבלה לרוחב; רוחב מינימלי למק"ט/יצרן למניעת קריסת עמודה.
_NOWRAP_COLUMNS = _PRICE_COLUMNS + _STOCK_COLUMNS
_BLOCK_START_COLUMNS = [f"{prefix}Mouser" for prefix in (PRICE_COLUMN_PREFIX, STOCK_COLUMN_PREFIX, LEAD_TIME_COLUMN_PREFIX)]
_MIN_WIDTH_COLUMNS = [MPN_COLUMN, "יצרן"]
_WRAP_COLUMNS = ["חלופה מוצעת", "חלופות"]

# CSS מקובע ל-Styler (scoped אוטומטית על ידי pandas לתחילית ה-id הייחודית של הטבלה, כך
# שלא דולף/מתנגש עם שאר העמוד) - RTL לוגי (start/end), sticky header, וטיפוגרפיה נגישה.
# צבעי תג ("pill") לכל ספק מומלץ - מראה "ממשלתי" נקי; slug נייטרלי ל"לא ידוע".
# תכלת עדין להדגשת עמודות ספק נבחר: inline (גובר על zebra/hover כמו צביעת הסיכון), נשמרת
# ניגודיות WCAG קריאה מול טקסט התא הכהה גם על שורות ה-zebra.
_HIGHLIGHT_TINT = "#DBEAFE"
_VENDOR_SLUGS = {"Mouser": "mouser", "DigiKey": "digikey", "Octopart": "octopart"}
_VENDOR_BADGE_COLORS = {
    "mouser": ("#0056B3", "#FFFFFF"), "digikey": ("#CC0000", "#FFFFFF"),
    "octopart": ("#00857C", "#FFFFFF"), "unknown": ("#E3E8EF", "#475467"),
}

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
    # גבולות אופקיים בלבד (border-bottom) במקום רשת מלאה - מראה נקי יותר; פסים לסירוגין
    # (zebra) והדגשת שורה במעבר עכבר (hover) לשיפור סריקה ויזואלית. קריטי: zebra/hover על
    # ה-tr (לא על ה-td) - צבעי תא פרטניים (ציון סיכון, הדגשת ספק) נקבעים על ה-td ומכסים את
    # רקע השורה ללא מלחמת specificity (כלל ברמת td של ה-zebra גבר על צבעי התא בשורות זוגיות).
    {"selector": "td", "props": [
        ("border", "none"), ("border-bottom", "1px solid #E3E8EF"), ("padding", "8px"), ("text-align", "start"),
    ]},
    {"selector": "tbody tr:nth-child(even)", "props": [("background-color", "#F6F8FB")]},
    {"selector": "tbody tr:hover", "props": [("background-color", "#EEF4FB")]},
    {"selector": ".vendor-badge", "props": [
        ("display", "inline-block"), ("padding", "2px 12px"), ("border-radius", "999px"),
        ("font-size", "0.85rem"), ("font-weight", "600"), ("white-space", "nowrap"),
    ]},
    *[
        {"selector": f".vendor-badge-{slug}", "props": [("background-color", bg), ("color", fg)]}
        for slug, (bg, fg) in _VENDOR_BADGE_COLORS.items()
    ],
]


def _ltr(text: str) -> str:
    """עוטף טקסט (שכבר הוברח!) ב-<bdo dir="ltr"> - בידוד Bidi כפוי לתוכן לטיני/מספרי בהקשר
    RTL, לפי מערכת העיצוב (DESIGN.md סעיף 3). ה-CSS הגלובלי (DESIGN_CSS) קובע ל-bdo
    unicode-bidi: isolate, כך שהעטיפה מבודדת את הרצף מסביבתו העברית בלי להפוך את תוכנו."""
    return f'<bdo dir="ltr">{text}</bdo>'


def _price_text(value) -> str:
    """מעצב מחיר: ערך מספרי נעטף ב-bdo (רצף "₪ 1,234.56" נשאר בסדר קריאה LTR); המחרוזת
    העברית "לא זמין" נשארת חשופה - כפיית LTR על עברית הייתה מציגה אותה הפוך."""
    return "לא זמין" if pd.isna(value) else _ltr(f"₪ {value:,.2f}")


def _stock_text(value) -> str:
    return "לא ידוע" if pd.isna(value) else _ltr(f"{value:,.0f}")


def _mpn_bidi(value) -> str:
    """עוטף מק"ט ב-<bdo dir="ltr"> כדי שמחרוזת אלפאנומרית/לטינית לא תתהפך/תישבר בהקשר RTL
    (מערכת העיצוב מחייבת bdo, בעבר <bdi>). ה-HTML מוברח ידנית (html.escape) כי escape="html"
    הכללי של Styler היה בורח גם את התגית עצמה."""
    return _ltr(html.escape(str(value)))


_HEBREW_CHARS = set(map(chr, range(0x0590, 0x0600)))


def _latin_ltr(value) -> str:
    """מבריח ערך טקסטואלי מעורב (זמני אספקה/תאריכים לועזיים/רשימות מק"ט חלופיות) ועוטף אותו
    ב-<bdo dir="ltr"> רק אם אין בו אף תו עברי - טקסט עברי ("זמן אספקה: לא ידוע") שייכפה
    ל-LTR היה מתרנדר הפוך, ולכן נשאר חשוף בהקשר ה-RTL הטבעי."""
    text = str(value)
    escaped = html.escape(text)
    return escaped if _HEBREW_CHARS.intersection(text) else _ltr(escaped)


def _vendor_badge(value) -> str:
    """עוטף את הספק המומלץ בתג ("pill") מעוצב. ה-HTML מוברח ידנית (html.escape) בדיוק כמו
    ב-_mpn_bidi, כי format ללא escape="html" אינו מבריח את הפלט שלנו - קריטי למניעת XSS."""
    text = str(value)
    slug = _VENDOR_SLUGS.get(text, "unknown")
    return f'<span class="vendor-badge vendor-badge-{slug}">{html.escape(text)}</span>'


def _risk_color(value) -> str:
    if value == 1:
        return "background-color: #FFCCCC"
    if value in (2, 3):
        return "background-color: #FFFFCC"
    return "background-color: #CCFFCC"


def render_table(df: pd.DataFrame, highlight_vendor: str | None = None) -> None:  # pragma: no cover - חיווט Streamlit בלבד (Proxy)
    """
    מרנדר את טבלת הרכיבים כטבלת HTML טהורה (pandas.Styler -> st.html) - לא st.dataframe
    (ה-grid הפנימי מצויר על canvas ושובר RTL עברי לחלוטין) ולא st.iframe/components.html
    (בעיות WebSocket/רינדור iframe). st.html מזריק ישירות ל-DOM הראשי (לא iframe מבודד),
    כך שה-CSS של ה-Styler עצמו שולט לגמרי על ה-RTL/הטיפוגרפיה בלי תלות ב-CSS הגלובלי.

    אזהרת אבטחה: מאחר שהטבלה מוזרקת ל-DOM הראשי (לא מבודדת ב-iframe כמו קודם), format
    עם escape="html" הוא קריטי - חובה למנוע החדרת קוד (XSS) מערכים שמקורם ב-BOM שהועלה
    או בתגובות API חיצוניות (לא מהימנים) לתוך שאר האפליקציה, לא רק לתוך iframe מבודד.
    """
    # class="num" על תאי הנתונים של העמודות המספריות (הכותרות מקבלות אותו בפוסט-עיבוד למטה).
    td_classes = pd.DataFrame("", index=df.index, columns=df.columns)
    for col in _NUMERIC_COLUMNS:
        if col in td_classes.columns:
            td_classes[col] = "num"

    # סדר קריאות ה-format קריטי לאבטחה: קריאת format ללא subset מאפסת את פונקציות התצוגה של
    # כל העמודות (כולל escape קודם!), ולכן ה-escape="html" הכללי חייב להיות ראשון וכל
    # הפורמטרים פולטי ה-HTML (עטיפות <bdo>/badge) מופעלים עם subset ממוקד בלבד - כך שהעמודות
    # הנותרות (יצרן/סטטוס/RoHS/אריזה/חלופה מוצעת) נשארות מוברחות. ההברחה בפורמטרים ידנית
    # (_latin_ltr/_mpn_bidi/_vendor_badge); מחיר/מלאי מפורמטים מ-float ואינם מכילים תווי HTML.
    styler = (
        df.style
        .hide(axis="index")
        .format(escape="html")
        .format(_price_text, subset=_PRICE_COLUMNS)
        .format(_stock_text, subset=_STOCK_COLUMNS)
        .format(_latin_ltr, subset=_LEAD_TIME_COLUMNS + ["חלופות"])
        .format(_mpn_bidi, subset=[MPN_COLUMN])
        .format(_vendor_badge, subset=["ספק מומלץ"])
        .set_td_classes(td_classes)
        .map(_risk_color, subset=["ציון סיכון"])
        .set_properties(subset=_END_ALIGNED_COLUMNS, **{"text-align": "end !important"})
        .set_properties(subset=_NOWRAP_COLUMNS, **{"white-space": "nowrap"})
        .set_properties(subset=_BLOCK_START_COLUMNS, **{"border-inline-start": "2px solid #D0D7E2"})
        .set_properties(subset=_MIN_WIDTH_COLUMNS, **{"min-width": "120px"})
        .set_properties(
            subset=_WRAP_COLUMNS,
            **{"white-space": "normal", "word-break": "break-word", "max-width": "220px"},
        )
        .set_table_styles(_TABLE_STYLES)
        # sci-table: מחיל את כללי הטבלה של מערכת העיצוב (DESIGN_CSS); כללי ה-#T_xxx הממוקדים
        # של ה-Styler גוברים עליהם בכל התנגשות (ספציפיות id), כך שהמראה הקיים נשמר.
        .set_table_attributes('role="table" class="sci-table"')
    )
    highlight_cols = [c for c in vendor_columns(highlight_vendor) if c in df.columns]
    if highlight_cols:
        styler = styler.set_properties(subset=highlight_cols, **{"background-color": _HIGHLIGHT_TINT})
    table_html = styler.to_html().replace("<th ", '<th scope="col" ')
    # class="num" גם על כותרות העמודות המספריות: ה-Styler מסמן כל כותרת ב-col{i} לפי מיקום
    # העמודה, ואין לו API להוספת class ל-th - לכן ההזרקה בפוסט-עיבוד מחרוזתי מדויק.
    for i, col in enumerate(df.columns):
        if col in _NUMERIC_COLUMNS:
            table_html = table_html.replace(
                f'class="col_heading level0 col{i}"', f'class="col_heading level0 col{i} num"'
            )
    # מיכל גלילה: הופך את ה-thead ה-sticky ל"דביק" בתוך האזור עצמו (ולא ביחס לחלון), ומעניק
    # מסגרת/פינות מעוגלות/צל עדין למראה "ממשלתי" נקי. שומר על role/aria-label/tabindex לנגישות.
    container_style = (
        "max-height:600px;overflow-y:auto;border:1px solid #E3E8EF;"
        "border-radius:8px;box-shadow:0 1px 3px rgba(16,24,40,.1);"
    )
    full_html = (
        f'<div role="region" aria-label="טבלת נתוני רכיבים מועשרים" tabindex="0" '
        f'style="{container_style}">{table_html}</div>'
    )
    st.html(full_html)
