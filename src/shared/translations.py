import re
from typing import Optional

# מילון תרגום מרכזי: ממפה ערכי מחרוזת המגיעים מ-API-ים חיצוניים (Mouser וכו') לעברית,
# כדי שהממשק (GUI/דוח) יוצג במלואו בעברית ללא תלות בשפת התשובה המקורית מהספק.
# הביטויים הארוכים/הספציפיים ביותר מופיעים קודם, כדי שלא יתאמו חלקית לביטוי כללי יותר
# (למשל "RoHS Compliant" חייב לנצח את "Compliant" הבודד).
TRANSLATIONS = {
    "Not Recommended for New Designs": "לא מומלץ לעיצוב חדש",
    "RoHS Compliant": "תואם RoHS",
    "Not Compliant": "לא תואם RoHS",
    "New Product": "מוצר חדש",
    "Last Time Buy": "רכישה אחרונה",
    "End of Life": "סוף חיי מוצר",
    "Non-Stocked": "לא במלאי קבוע",
    "Backordered": "בהזמנה מוקדמת (חוסר זמני)",
    "On Order": "בהזמנה",
    "In Stock": "במלאי",
    "Obsolete": "מיושן",
    "Compliant": "תואם",
    "Allocation": "הקצאה מוגבלת",
    "Active": "פעיל",
    "NRND": "לא מומלץ לעיצוב חדש",
    "EOL": "סוף חיי מוצר",
    "LTB": "רכישה אחרונה",
    "Unknown": "לא ידוע",
    "Weeks": "שבועות",
    "Week": "שבוע",
    "Days": "ימים",
    "Day": "יום",
}

_PATTERN = re.compile("|".join(re.escape(k) for k in sorted(TRANSLATIONS, key=len, reverse=True)))


def translate(text: Optional[str]) -> str:
    """מתרגם מחרוזת (או קטעים בתוכה, למשל '63 Days') לפי מילון התרגום.
    חלקים שלא מוכרים למילון (כגון מספרים) נשארים כפי שהם."""
    if not text:
        return "לא ידוע"
    return _PATTERN.sub(lambda m: TRANSLATIONS[m.group(0)], str(text))


def format_inventory(vendor: str, raw_availability: Optional[str]) -> str:
    """מעצב מחרוזת מלאי ספציפית לספק, למשל 'Mouser: 24,755 במלאי'."""
    return f"{vendor}: {translate(raw_availability)}"


def format_lead_time(raw_lead_time: Optional[str]) -> str:
    """מעצב זמן אספקה מתורגם, למשל 'זמן אספקה: 63 ימים'."""
    if not raw_lead_time:
        return "זמן אספקה: לא ידוע"
    return f"זמן אספקה: {translate(raw_lead_time)}"
