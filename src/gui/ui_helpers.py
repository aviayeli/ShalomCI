import streamlit as st

# תבנית BOM ריקה להורדה - עמודת MPN בלבד. שומרת על אותה עמודה שה-BomParser מזהה תמיד
# (mpn_aliases כולל 'mpn' כמועמד ראשון), כדי להבטיח למשתמש נתיב עלייה תקין ומהיר.
_BLANK_BOM_TEMPLATE_CSV = "MPN\n"

_WELCOME_MESSAGE = (
    "**ShalomCI** היא מערכת ניהול מחזור חיי רכיבים (Component Lifecycle Management - CLM) "
    "השולפת בזמן אמת נתוני **מלאי, תמחור ומחזור חיים** משלושה ספקים מובילים: "
    "**Mouser, DigiKey ו-Octopart**.\n\n"
    "📋 **לפני ההעלאה:** קובץ עץ המוצר (BOM) חייב לכלול עמודה בשם המדויק **MPN** (מק\"ט יצרן). "
    "ניתן להוריד תבנית ריקה מוכנה מתחת."
)


def render_welcome_header() -> None:
    """
    מציג הסבר קצר על מקור הנתונים ודרישת עמודת ה-MPN, וכפתור הורדת תבנית BOM ריקה.

    יישום היוריסטיקות של Nielsen: "System Status Visibility" (המשתמש מבין מייד מה המערכת
    עושה ומאיפה מגיע המידע) ו-"Error Prevention" (מניעת כשל BomParser.parse_file - "לא זוהתה
    עמודת MPN" - עוד לפני שהמשתמש בכלל מעלה קובץ, על ידי מתן תבנית מוכנה וידועה כתקינה).
    """
    st.info(_WELCOME_MESSAGE)
    st.download_button(
        "📥 הורד תבנית BOM ריקה",
        data=_BLANK_BOM_TEMPLATE_CSV.encode("utf-8-sig"),
        file_name="shalomci_bom_template.csv",
        mime="text/csv",
    )


def render_summary_metrics(summary: dict) -> None:
    """מציג רצועת מדדים (4 עמודות) עם התפלגות הסיכון: סה"כ / קריטי / אזהרה / תקינים."""
    cols = st.columns(4)
    cols[0].metric("סה\"כ רכיבים", summary["total"])
    cols[1].metric("סיכון קריטי", summary["critical"])
    cols[2].metric("אזהרה", summary["warning"])
    cols[3].metric("תקינים", summary["healthy"])
