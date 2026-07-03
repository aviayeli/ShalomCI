# אייקוני נגישות (WCAG 2.2) - ההתראה על סטטוס לא מסתמכת על צבע בלבד; אותם ספים כמו צביעת התאים.
STATUS_ICONS = {1: "⛔", 2: "⚠️", 3: "⚠️", 4: "✅", 5: "✅"}

# ספקי משנה המוצגים side-by-side ל-Mouser (מפתח בעברית לתצוגה -> קידומת שדה ב-comp)
SECONDARY_VENDORS = {"DigiKey": "digikey", "Octopart": "octopart"}


def status_icon(risk_score: int) -> str:
    """מחזיר אייקון נגישות התואם לרמת הסיכון; ציון לא ידוע (0) מסומן לבדיקה ידנית."""
    return STATUS_ICONS.get(risk_score, "❓")


def vendor_columns(c: dict) -> dict:
    """בונה עמודות מחזור חיים/מלאי/זמן אספקה/מחיר לכל ספק משני, מתוך שדות comp[f'{prefix}_*']."""
    cols = {}
    for label, prefix in SECONDARY_VENDORS.items():
        cols[f"מחזור חיים ({label})"] = c.get(f"{prefix}_lifecycle", "לא ידוע")
        cols[f"מלאי ({label})"] = c.get(f"{prefix}_inventory", f"{label}: לא ידוע")
        cols[f"זמן אספקה ({label})"] = c.get(f"{prefix}_lead_time", "זמן אספקה: לא ידוע")
        cols[f"מחיר ליחידה ({label})"] = c.get(f"{prefix}_price_per_unit", "לא זמין")
    return cols


def build_rows(components: list) -> list:
    """בונה את שורות טבלת התצוגה מתוך נתוני הרכיבים המועשרים (פונקציה טהורה, ניתנת לבדיקה)."""
    rows = []
    for c in components:
        score = c.get("risk_score", 0)
        rows.append({
            "מק\"ט": c.get("mpn", "N/A"),
            "יצרן": c.get("manufacturer", "N/A"),
            "סטטוס": f"{status_icon(score)} {c.get('lifecycle_status', 'N/A')}",
            "ציון סיכון": score,
            "מלאי": c.get("inventory", "לא ידוע"),
            "זמן אספקה": c.get("lead_time", "זמן אספקה: לא ידוע"),
            "מחיר ליחידה": c.get("price_per_unit", "לא זמין"),
            "חלופה מוצעת (Mouser)": c.get("suggested_replacement", "אין"),
            "תאימות RoHS": c.get("rohs_status", "לא ידוע"),
            "צורת אריזה": c.get("packaging", "לא ידוע"),
            **vendor_columns(c),
            "חלופות": ", ".join([a.get("mpn", "") for a in c.get("alternatives", [])]) if c.get(
                "alternatives") else "אין"
        })
    return rows
