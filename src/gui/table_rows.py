# אייקוני נגישות (WCAG 2.2) - ההתראה על סטטוס לא מסתמכת על צבע בלבד; אותם ספים כמו צביעת התאים.
STATUS_ICONS = {1: "⛔", 2: "⚠️", 3: "⚠️", 4: "✅", 5: "✅"}

# שלושת הספקים המושווים side-by-side (מפתח בעברית לתצוגה -> קידומת שדה ב-comp). מחזור
# חיים/ציון סיכון מוצגים פעם אחת בלבד (מקור: Mouser בלבד) - ראו PRD 4.3/PLAN סעיף 6.
PRICE_STOCK_VENDORS = {"Mouser": "mouser", "DigiKey": "digikey", "Octopart": "octopart"}
PRICE_COLUMN_PREFIX = "מחיר - "
STOCK_COLUMN_PREFIX = "מלאי - "
LEAD_TIME_COLUMN_PREFIX = "אספקה - "
MPN_COLUMN = "מק\"ט"


def vendor_columns(vendor) -> list:
    """מחזיר את שלוש עמודות הספק (מחיר / מלאי / אספקה) לצורך הדגשה אנכית - כך שהמשתמש יכול
    לעקוב אחר נתוני ספק יחיד לאורך הטבלה. vendor ריק/None -> רשימה ריקה (אין הדגשה כלל).
    ממוקם כאן, לצד קבועי סכמת העמודות, כדי שהקידומות יוגדרו במקום אחד בלבד."""
    if not vendor:
        return []
    return [f"{prefix}{vendor}" for prefix in (PRICE_COLUMN_PREFIX, STOCK_COLUMN_PREFIX, LEAD_TIME_COLUMN_PREFIX)]


def summarize_risk(components: list) -> dict:
    """
    מסכם את התפלגות הסיכון של הרכיבים לספירות (פונקציה טהורה, ניתנת לבדיקה): total (סה"כ),
    critical (ציון 1), warning (ציון 2-3), healthy (ציון 4-5). ציון לא ידוע (0 או מחוץ לטווח)
    נספר ב-total בלבד ולא באף קטגוריית משנה - אותם ספים כמו צביעת התאים ואייקוני הסטטוס.
    """
    summary = {"total": 0, "critical": 0, "warning": 0, "healthy": 0}
    for c in components:
        summary["total"] += 1
        score = c.get("risk_score", 0)
        if score == 1:
            summary["critical"] += 1
        elif score in (2, 3):
            summary["warning"] += 1
        elif score in (4, 5):
            summary["healthy"] += 1
    return summary


def status_icon(risk_score: int) -> str:
    """מחזיר אייקון נגישות התואם לרמת הסיכון; ציון לא ידוע (0) מסומן לבדיקה ידנית."""
    return STATUS_ICONS.get(risk_score, "❓")


def recommended_vendor(c: dict) -> str:
    """
    קובע את הספק המומלץ לרכיב: מעדיף את הספק עם המחיר הנמוך ביותר מבין אלו שדיווחו מחיר;
    אם אף ספק לא החזיר מחיר, נופל בחזרה לספק עם המלאי הגבוה ביותר. None (חוסר נתון)
    לעולם לא "מנצח" ספק עם ערך אמיתי, גם אם הערך האמיתי הוא 0.
    """
    prices = {label: c.get(f"{prefix}_price_value") for label, prefix in PRICE_STOCK_VENDORS.items()}
    valid_prices = {label: p for label, p in prices.items() if p is not None}
    if valid_prices:
        return min(valid_prices, key=valid_prices.get)

    stocks = {label: c.get(f"{prefix}_stock_qty") for label, prefix in PRICE_STOCK_VENDORS.items()}
    valid_stocks = {label: s for label, s in stocks.items() if s is not None}
    if valid_stocks:
        return max(valid_stocks, key=valid_stocks.get)

    return "לא ידוע"


def vendor_price_stock_columns(c: dict) -> dict:
    """בונה עמודות מחיר/מלאי גולמיות (מספריות) לכל ספק, מתוך שדות comp[f'{prefix}_*'].
    קיבוץ לפי מדד (סדר ה-dict = סדר התצוגה): כל 3 המחירים צמודים, אחריהם כל 3 המלאים -
    לסריקה השוואתית של מדד אחד לרוחב הספקים (במקום זוגות מחיר+מלאי לסירוגין)."""
    cols = {}
    for label, prefix in PRICE_STOCK_VENDORS.items():
        cols[f"{PRICE_COLUMN_PREFIX}{label}"] = c.get(f"{prefix}_price_value")
    for label, prefix in PRICE_STOCK_VENDORS.items():
        cols[f"{STOCK_COLUMN_PREFIX}{label}"] = c.get(f"{prefix}_stock_qty")
    return cols


def build_rows(components: list) -> list:
    """בונה את שורות טבלת התצוגה מתוך נתוני הרכיבים המועשרים (פונקציה טהורה, ניתנת לבדיקה)."""
    rows = []
    for c in components:
        score = c.get("risk_score", 0)
        # סדר המפתחות = סדר העמודות (RTL): המפתח הראשון מרונדר בימין (תחילת זרימת הקריאה
        # העברית) והאחרון בשמאל (סופה). מק"ט (המפתח הראשי) פותח את הזרימה בימין, ו"ספק מומלץ"
        # (המסקנה הפעילה - איזה ספק לבחור) סוגר אותה בשמאל כמפתח האחרון. בין השניים: תקציר
        # ההחלטה (יצרן → סטטוס → ציון סיכון), בלוקי המדדים (מחירים → מלאים → אספקה) והזנב
        # הארוך (חלופה מוצעת / RoHS / אריזה / חלופות).
        rows.append({
            MPN_COLUMN: c.get("mpn", "N/A"),
            "יצרן": c.get("manufacturer", "N/A"),
            "סטטוס": f"{status_icon(score)} {c.get('lifecycle_status', 'N/A')}",
            "ציון סיכון": score,
            **vendor_price_stock_columns(c),
            f"{LEAD_TIME_COLUMN_PREFIX}Mouser": c.get("lead_time", "זמן אספקה: לא ידוע"),
            f"{LEAD_TIME_COLUMN_PREFIX}DigiKey": c.get("digikey_lead_time", "זמן אספקה: לא ידוע"),
            f"{LEAD_TIME_COLUMN_PREFIX}Octopart": c.get("octopart_lead_time", "זמן אספקה: לא ידוע"),
            "חלופה מוצעת": c.get("suggested_replacement", "אין"),
            "תאימות RoHS": c.get("rohs_status", "לא ידוע"),
            "צורת אריזה": c.get("packaging", "לא ידוע"),
            "חלופות": ", ".join([a.get("mpn", "") for a in c.get("alternatives", [])]) if c.get(
                "alternatives") else "אין",
            "ספק מומלץ": recommended_vendor(c),
        })
    return rows
