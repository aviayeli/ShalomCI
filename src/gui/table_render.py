import pandas as pd
import streamlit as st

from src.gui.table_format import (VENDOR_BADGE_COLORS, latin_ltr, mpn_bidi, price_text,
                                  risk_color, stock_text, vendor_badge)
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
# תכלת עדין להדגשת עמודות ספק נבחר: inline (גובר על zebra/hover כמו צביעת הסיכון), נשמרת
# ניגודיות WCAG קריאה מול טקסט התא הכהה גם על שורות ה-zebra.
_HIGHLIGHT_TINT = "#DBEAFE"

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
        for slug, (bg, fg) in VENDOR_BADGE_COLORS.items()
    ],
]


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
    # הפורמטרים פולטי ה-HTML (עטיפות <bdo>/badge, ראו table_format) מופעלים עם subset ממוקד
    # בלבד - כך שהעמודות הנותרות (יצרן/סטטוס/RoHS/אריזה/חלופה מוצעת) נשארות מוברחות.
    styler = (
        df.style
        .hide(axis="index")
        .format(escape="html")
        .format(price_text, subset=_PRICE_COLUMNS)
        .format(stock_text, subset=_STOCK_COLUMNS)
        .format(latin_ltr, subset=_LEAD_TIME_COLUMNS + ["חלופות"])
        .format(mpn_bidi, subset=[MPN_COLUMN])
        .format(vendor_badge, subset=["ספק מומלץ"])
        .set_td_classes(td_classes)
        .map(risk_color, subset=["ציון סיכון"])
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
