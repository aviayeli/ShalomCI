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

# מערכת העיצוב של ShalomCI (Claude Design, ראו DESIGN.md): טוקנים גלובליים (צבע/רקע/סמנטיקה),
# בסיס טיפוגרפי RTL, וכללי טבלת נתונים (sci-table: יישור לוגי, ספרות טבלאיות בעמודות num,
# תגי סטטוס). מוזרק ב-app.py מייד אחרי RTL_CSS - סדר ההזרקה קובע: ה-background של .stApp
# כאן (--sci-bg) גובר על גיליון קודם באותה ספציפיות. הבלוק נשמר כלשונו (verbatim) מהאפיון.
DESIGN_CSS = """
<style>
/* ===== ShalomCI · Global RTL + Design Tokens ===== */
:root {
  --sci-primary:#2F6BDB; --sci-bg:#F4F6F9; --sci-surface:#FFFFFF;
  --sci-text:#1B2431; --sci-muted:#566072; --sci-border:#E7EAEF;
  --sci-eol:#DC2626;   --sci-eol-bg:#FEECEC;   --sci-eol-fg:#B91C1C;
  --sci-nrnd:#D97706;  --sci-nrnd-bg:#FDF2E0;  --sci-nrnd-fg:#92590B;
  --sci-active:#059669;--sci-active-bg:#E6F6EF;--sci-active-fg:#047857;
}

html, body, .stApp {
  direction: rtl;
  text-align: start;
  font-family: "Assistant","Heebo",system-ui,sans-serif;
  font-size: 16px;
  line-height: 1.6;
  letter-spacing: normal;
  color: var(--sci-text);
  background: var(--sci-bg);
}

* { letter-spacing: normal !important; }

bdo[dir="ltr"], .ltr { unicode-bidi: isolate; direction: ltr; }

table.sci-table { width: 100%; border-collapse: collapse; }
.sci-table th, .sci-table td {
  padding-block: 10px;
  padding-inline: 14px;
  border-block-end: 1px solid #F1F3F6;
  text-align: start;
  vertical-align: middle;
}
.sci-table thead th { background:#F7F9FB; color:#7A828F; font-size:13px; font-weight:700; }

.sci-table .num, .sci-table th.num, .sci-table td.num {
  text-align: end;
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum" 1;
}

.sci-badge { display: inline-flex; align-items: center; gap: 7px; padding-block: 4px; padding-inline: 10px; border-radius: 999px; font-size: 13px; font-weight: 700; }
.sci-badge::before { content:""; width:7px; height:7px; border-radius:50%; }
.status-eol    { background:var(--sci-eol-bg);    color:var(--sci-eol-fg); }
.status-nrnd   { background:var(--sci-nrnd-bg);   color:var(--sci-nrnd-fg); }
.status-active { background:var(--sci-active-bg); color:var(--sci-active-fg); }
.status-eol::before    { background:var(--sci-eol); }
.status-nrnd::before   { background:var(--sci-nrnd); }
.status-active::before { background:var(--sci-active); }

.risk-low  { color:var(--sci-active-fg); font-weight:800; font-variant-numeric:tabular-nums; }
.risk-med  { color:#B45309;              font-weight:800; font-variant-numeric:tabular-nums; }
.risk-high { color:var(--sci-eol);       font-weight:800; font-variant-numeric:tabular-nums; }

/* שכבת תאימות (מחוץ לבלוק ה-verbatim): כלל ה-* ב-RTL_CSS קובע direction: rtl עם !important,
   שגובר גם על מאפיין dir="ltr" וגם על כלל ה-bdo שלמעלה (שאינו !important) - וכל <bdo dir="ltr">
   (מק"ט, מחיר, תאריך לועזי) היה מתהפך חזרה ל-RTL. הכלל כאן משחזר את הבידוד בעדיפות שווה. */
bdo[dir="ltr"], .ltr { direction: ltr !important; unicode-bidi: isolate !important; }
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
