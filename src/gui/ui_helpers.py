import hashlib
import os

import streamlit as st

# CSS גלובלי: RTL לוגי (start/end, לא right/left קשיח), טיפוגרפיה נגישה מותאמת עברית, ורקע.
# הטבלה עצמה (table_render.py, pandas.Styler -> st.html) מרונדרת ב-DOM הראשי, לכן ה-CSS
# הזה משפיע עליה גם כן - אך ל-Styler יש CSS ממוקד משלו (scoped לתחילית ה-id הייחודי שלו,
# עם !important) שגובר על הכללים הגלובליים כאן היכן שהם מתנגשים (למשל יישור עמודות מספריות).
RTL_CSS = """
<style>
    * {
        direction: rtl !important;
        text-align: start !important;
        font-family: 'Assistant', 'Heebo', 'Noto Sans Hebrew', 'Segoe UI', sans-serif !important;
        font-size: 1rem;
        line-height: 1.5;
        font-style: normal !important;
        letter-spacing: normal !important;
    }
    /* תיקון "הכיתוב הכפול" על כפתור ההעלאה: אייקוני Material הם ligature של הפונט
       'Material Symbols Rounded' (span עם data-testid=stIconMaterial ותוכן הטקסט "upload").
       דריסת font-family עם !important על ה-* שברה את ה-ligature והציגה את המילה "upload"
       כטקסט ליטרלי ליד תווית הכפתור - וכך נראה כיתוב כפול. החזרת פונט האייקונים מתקנת
       זאת באופן דטרמיניסטי (ללא תלות במנגנון השכפול המדויק). */
    [data-testid="stIconMaterial"] {
        font-family: 'Material Symbols Rounded' !important;
    }
    .stApp { background-color: #F8F9FA; }
    /* מטרות מגע נגישות (WCAG) - מילים בעברית ("הורד" לעומת "Download") מקצרות כפתורים
       בברירת המחדל של Streamlit עד כדי חוסר שימושיות במגע; גובה/ריפוד מינימליים מתקנים זאת. */
    button {
        min-height: 48px !important;
        padding-inline: 32px !important;
    }
    /* הכפתור הפנימי של אזור הגרירה אינו כפתור פעולה עצמאי - הריפוד האוניברסלי מעוות אותו;
       ריפוד שפוי ממוקד ל-test-id של אזור הגרירה בלבד. */
    [data-testid="stFileUploaderDropzone"] button {
        padding-inline: 16px !important;
    }
    /* עברות אזור הגרירה + מניעת כפילות: הסתרת הטקסט האנגלי המובנה והזרקת עברית, ממוקד
       ל-test-ids המדויקים של Streamlit 1.58 בלבד (לא selector אוניברסלי נוסף). */
    [data-testid="stFileUploaderDropzoneInstructions"] span {
        font-size: 0 !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"]::after {
        content: "גררו קובץ לכאן או לחצו לבחירה (XLSX / CSV, עד 200MB)";
        display: block;
        font-size: 0.875rem !important;
        color: #31333F;
    }
    /* חייבים לכסות גם את הצאצאים (ולא רק את הכפתור עצמו): כלל ה-* האוניברסלי למעלה קובע
       font-size: 1rem ישירות על ה-span הפנימי של התווית, ולכן font-size: 0 על הכפתור בלבד
       אינו מגיע לטקסט "Upload" - והוא דלף לצד "בחר קובץ". כלל האייקון שמתחת (ספציפיות
       גבוהה יותר) ממשיך לגבור ולהציג את האייקון. */
    [data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"],
    [data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] * {
        font-size: 0 !important;
    }
    [data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] [data-testid="stIconMaterial"] {
        font-size: 1.25rem !important;
    }
    [data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"]::after {
        content: "בחר קובץ";
        font-size: 0.875rem !important;
    }
</style>
"""

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


# 5 משתני הסביבה שה-SDK קורא בבניית הקליינטים (ראו src/sdk.py). התוויות בעברית, אך שמות
# הספקים (Mouser/DigiKey) נשארים לטיניים בתוך טקסט עברי כמקובל בשאר האפליקציה.
_API_KEY_FIELDS = [
    ("MOUSER_API_KEY", "מפתח Mouser API"),
    ("DIGIKEY_CLIENT_ID", "DigiKey Client ID"),
    ("DIGIKEY_CLIENT_SECRET", "DigiKey Client Secret"),
    ("OCTOPART_CLIENT_ID", "Octopart/Nexar Client ID"),
    ("OCTOPART_CLIENT_SECRET", "Octopart/Nexar Client Secret"),
]

# ספק -> משתני הסביבה הנדרשים לו. הספק "מוגדר" רק אם כל המשתנים שלו אינם ריקים (DigiKey/Octopart
# דורשים גם ID וגם Secret; חסר אחד מהם והקליינט נופל ל-None וחוזר לנתוני ברירת מחדל).
_PROVIDER_REQUIREMENTS = {
    "Mouser": ["MOUSER_API_KEY"],
    "DigiKey": ["DIGIKEY_CLIENT_ID", "DIGIKEY_CLIENT_SECRET"],
    "Octopart": ["OCTOPART_CLIENT_ID", "OCTOPART_CLIENT_SECRET"],
}


def render_api_keys_sidebar() -> None:
    """סרגל צד להזנת מפתחות API. הערכים נכתבים ל-os.environ בזמן אמת (לפני כפתור הניתוח) כך
    שה-SDK ישאב אותם בריצה הבאה; שדה ריק => הסרת המשתנה (הקליינט יפול חזרה ל-None/ברירת מחדל).
    המפתחות חיים רק למשך ה-session (בזיכרון) ואינם נכתבים לדיסק."""
    with st.sidebar.expander("🔌 הגדרות מפתחות API"):
        for var, label in _API_KEY_FIELDS:
            # prefill מ-os.environ (כולל מפתחות שנטענו מ-.env) - מוצג ממוסך (password).
            value = st.text_input(label, value=os.environ.get(var, ""), type="password")
            if value:
                os.environ[var] = value
            else:
                os.environ.pop(var, None)

        st.markdown("**סטטוס ספקים:**")
        for provider, required in _PROVIDER_REQUIREMENTS.items():
            configured = all(os.environ.get(v) for v in required)
            st.markdown(f"{'✅ מוגדר' if configured else '⚠️ חסר'} · {provider}")

        st.caption(
            "המפתחות נשמרים לזמן ה-session בלבד (לא נכתבים לדיסק). "
            "מגבלות שכבה חינמית חלות — Mouser: 1,000 קריאות ביום."
        )


def api_keys_fingerprint() -> str:
    """טביעת אצבע יציבה ולא-הפיכה (sha256) של ערכי המפתחות הנוכחיים, לשימוש כפרמטר מטמון של
    cached_analysis - כדי ששינוי מפתח יוכל להפיק תוצאה שונה, בלי לאחסן את המפתחות עצמם במפתח המטמון."""
    raw = "\x00".join(os.environ.get(var, "") for var, _ in _API_KEY_FIELDS)
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
