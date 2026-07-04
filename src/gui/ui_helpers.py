import hashlib
import os

import streamlit as st

# תבנית BOM ריקה להורדה - עמודת MPN בלבד. שומרת על אותה עמודה שה-BomParser מזהה תמיד
# (mpn_aliases כולל 'mpn' כמועמד ראשון), כדי להבטיח למשתמש נתיב עלייה תקין ומהיר.
_BLANK_BOM_TEMPLATE_CSV = "MPN\n"

_WELCOME_MESSAGE = (
    "**ShalomCI** היא מערכת לניהול מחזור חיי רכיבים (CLM) השולפת בזמן אמת נתוני "
    "**מלאי, תמחור ומחזור חיים** משלושה ספקים מובילים: **Mouser, DigiKey ו-Octopart**.\n\n"
    "📋 **לפני ההעלאה:** קובץ עץ המוצר (BOM) חייב לכלול עמודה בשם המדויק **MPN** (מק\"ט יצרן). "
    "ניתן להוריד תבנית ריקה ותקינה למטה."
)

# כותרת ה-expander של ההסבר (מתקפל: פתוח לפני ניתוח ראשון, מכווץ לאחר שיש תוצאות).
_WELCOME_EXPANDER_TITLE = "❓ כיצד להתחיל · דרישות קובץ ה-BOM"

# help של מדד הסיכון הכללי (מדד חמישי ברצועת ה-KPI) - תרגום עברי מלא.
RISK_SCORE_HELP = (
    "ציון הסיכון הכללי (1–5) משקלל את סיכון האספקה וההתיישנות של כלל הרכיבים בעץ המוצר. "
    "הוא נגזר מסטטוס מחזור החיים (למשל EOL/NRND), מזמינות המלאי הנוכחית ומזמני האספקה "
    "של הספקים. ציון נמוך = סיכון גבוה."
)


def render_welcome_header(expanded: bool) -> None:
    """
    מציג הסבר קצר על מקור הנתונים ודרישת עמודת ה-MPN, וכפתור הורדת תבנית BOM ריקה, בתוך
    st.expander מתקפל (expanded=True לפני ניתוח ראשון, False לאחר שקיימות תוצאות).

    יישום היוריסטיקות של Nielsen: "System Status Visibility" (המשתמש מבין מייד מה המערכת
    עושה ומאיפה מגיע המידע) ו-"Error Prevention" (מניעת כשל BomParser.parse_file - "לא זוהתה
    עמודת MPN" - עוד לפני שהמשתמש בכלל מעלה קובץ, על ידי מתן תבנית מוכנה וידועה כתקינה).
    """
    with st.expander(_WELCOME_EXPANDER_TITLE, expanded=expanded):
        st.markdown(_WELCOME_MESSAGE)
        st.download_button(
            "📥 הורד תבנית BOM ריקה",
            data=_BLANK_BOM_TEMPLATE_CSV.encode("utf-8-sig"),
            file_name="shalomci_bom_template.csv",
            mime="text/csv",
        )


# 5 משתני הסביבה שה-SDK קורא בבניית הקליינטים (ראו src/sdk.py). משמשים כיום רק לטביעת
# האצבע של cached_analysis; עדכון הערכים נעשה ידנית בקובץ ה-.env (ראו _API_KEYS_HELP_MD).
_API_KEY_ENV_VARS = [
    "MOUSER_API_KEY",
    "DIGIKEY_CLIENT_ID",
    "DIGIKEY_CLIENT_SECRET",
    "OCTOPART_CLIENT_ID",
    "OCTOPART_CLIENT_SECRET",
]

# טקסט ההסבר בסרגל הצד: כיצד לעבור מממשקי ה-API החינמיים (מוגבלי קצב) למפתחות בתשלום דרך קובץ ה-.env.
_API_KEYS_HELP_MD = (
    "האפליקציה רצה כרגע על ממשקי API **חינמיים** עם מגבלת קצב (rate limit) — "
    "למשל Mouser מוגבל ל-1,000 קריאות ביום.\n\n"
    "כדי לעבוד ללא מגבלות עם מפתחות בתשלום:\n\n"
    "1. פתחו את הקובץ `.env` שבתיקיית השורש של האפליקציה.\n"
    "2. עדכנו שם את המפתחות שלכם: `MOUSER_API_KEY`, `DIGIKEY_CLIENT_ID`, "
    "`DIGIKEY_CLIENT_SECRET`, `OCTOPART_CLIENT_ID`, `OCTOPART_CLIENT_SECRET`.\n"
    "3. שמרו את הקובץ והפעילו מחדש את האפליקציה."
)


def render_api_keys_sidebar() -> None:
    """סרגל צד סטטי המסביר כיצד להחליף את מפתחות ה-API החינמיים (מוגבלי הקצב) במפתחות בתשלום
    דרך עריכת קובץ ה-.env והפעלה מחדש. אינו קורא/כותב ל-os.environ ואינו מציג שדות קלט."""
    with st.sidebar.expander("🔌 הגדרות מפתחות API"):
        st.markdown(_API_KEYS_HELP_MD)


def api_keys_fingerprint() -> str:
    """טביעת אצבע יציבה ולא-הפיכה (sha256) של ערכי המפתחות הנוכחיים, לשימוש כפרמטר מטמון של
    cached_analysis - כדי ששינוי מפתח יוכל להפיק תוצאה שונה, בלי לאחסן את המפתחות עצמם במפתח המטמון."""
    raw = "\x00".join(os.environ.get(var, "") for var in _API_KEY_ENV_VARS)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def render_summary_metrics(summary: dict, score) -> None:
    """מציג רצועת מדדים (5 עמודות): סה"כ / קריטי / אזהרה / תקינים / ציון סיכון כללי.
    ציון הסיכון הכללי (מדד פרויקט) שייך לרצועת ה-KPI ולא צף בודד בין הסינון לטבלה."""
    cols = st.columns(5)
    cols[0].metric("סה\"כ רכיבים", summary["total"])
    cols[1].metric("סיכון קריטי", summary["critical"])
    cols[2].metric("אזהרה", summary["warning"])
    cols[3].metric("תקינים", summary["healthy"])
    # בידוד LTR (LRI...PDI): בלי זה, ההקשר הכללי RTL מסדר את הרצף "1.0 / 5.0" הפוך
    # ויזואלית ("5.0 / 1.0") - מה שנקרא כ"5 מתוך 1". הבידוד שומר על סדר קריאה שמאל-לימין.
    cols[4].metric("ציון סיכון כללי", f"\u2066{score} / 5.0\u2069", help=RISK_SCORE_HELP)
