# מסמך תכנון ארכיטקטוני (PLAN) - ShalomCI

## 1. מבנה תיקיות וקבצים (Directory Structure)
המבנה מתוכנן בהתאם לתקן V3, תוך הפרדה מוחלטת בין לוגיקה עסקית (Core), שירותים חיצוניים (Services), וניהול נתונים (Data).

```text
ShalomCI/
├── docs/
│   ├── PRD.md                 # דרישות המוצר (אושר)
│   ├── PLAN.md                # ארכיטקטורה (מסמך זה)
│   ├── TODO.md                # משימות לביצוע ומעקב סטטוס
│   └── CLAUDE.md              # חוקת הפרויקט V3
├── src/
│   ├── sdk.py                 # Single Entry Point - שכבת ה-SDK המרכזית
│   ├── core/
│   │   ├── bom_parser.py      # קליטה, זיהוי עמודות ופירוק קבצי Excel/CSV
│   │   ├── risk_engine.py     # אלגוריתם דירוג הסיכון (Project Scoring)
│   │   ├── cross_ref.py       # מנוע חלופות קרוס-רפרנס מתקדם
│   │   └── reporter.py        # ייצוא דוח ה-Excel המעוצב (.xlsx)
│   ├── services/
│   │   ├── gatekeeper.py      # API Gatekeeper - שומר הסף המרכזי (תורים, השהיות)
│   │   ├── mouser_api.py      # אינטגרציה מול Mouser (מחובר בפועל דרך ה-SDK)
│   │   ├── octopart_api.py    # אינטגרציה מול Octopart (GraphQL) - stub, שלב עתידי
│   │   └── digikey_api.py     # אינטגרציה מול DigiKey (OAuth2) - stub, שלב עתידי
│   ├── data/
│   │   └── case_manager.py    # ניהול מקרים מקומי (Cases) עבור רכיבים ללא חלופה
│   ├── shared/
│   │   └── translations.py    # שכבת תרגום עברית מרכזית (סטטוסים, שמות עמודות)
│   ├── cli/
│   │   └── main.py            # ממשק שורת הפקודה (Proxy בלבד, ללא לוגיקה)
│   └── gui/
│       ├── app.py             # ממשק Streamlit בעברית/RTL (Proxy בלבד, ללא לוגיקה)
│       ├── table_controls.py  # לוגיקת סינון/מיון טהורה (ניתנת לבדיקה, ללא Streamlit)
│       └── table_render.py    # רינדור הטבלה ב-iframe מבודד (components.html)
├── tests/
│   ├── unit/                  # בדיקות יחידה לכל מודול (test_sdk.py, test_gatekeeper.py, ...)
│   └── integration/           # בדיקות אינטגרציה בין שכבות
├── run_desktop.py             # נקודת כניסה לאריזת Desktop (PyInstaller) - ראו סעיף 7
├── build.py                   # סקריפט בנייה ל-PyInstaller (מופעל דרך uv run)
├── pyproject.toml             # הגדרות תלויות מנוהלות ע"י uv
├── uv.lock                    # נעילת גרסאות מדויקת
├── .env-example               # תבנית בטוחה למפתחות API
├── .gitignore                 # החרגת .env וקבצים זמניים
└── README.md                  # מדריך התקנה ושימוש למשתמש הקצה
```

## 2. ארכיטקטורת שכבת ה-SDK (Single Entry Point)
שכבת ה-`sdk.py` משמשת כמנצחת (Orchestrator) של המערכת. היא הדרך היחידה שבה ממשק הקצה (`cli/main.py`) יכול לתקשר עם המערכת.
ה-SDK יחשוף מחלקה ראשית `ShalomCI_SDK` עם מתודות ברורות לניהול מחזור החיים:
1. `process_bom(file_path)`: מעבירה את הקובץ ל-`bom_parser`.
2. `enrich_components(bom_data)`: דורשת מידע עדכני דרך ה-`sdk` שקורא ל-`Gatekeeper`.
3. `evaluate_risks(enriched_data)`: הפעלת ה-`risk_engine` לקבלת דירוג 1-5.
4. `find_mitigations(risky_components)`: הפעלת ה-`cross_ref` לחיפוש חלופות.
5. `generate_report(final_data, output_path)`: יצירת פלט למשתמש.

ממשק ה-CLI יקרא רק ל-SDK, וידפיס את הסטטוסים או הבר-התקדמות. שום קריאת רשת או חישוב לוגי לא יתבצעו ב-CLI.

## 3. תכנון שומר הסף (API Gatekeeper)
ה-Gatekeeper (בקובץ `services/gatekeeper.py`) יהיה רכיב אסינכרוני מבוסס תורים (Async Queues), אשר יעטוף את כל הבקשות היוצאות מספקי המידע.
- **Mouser Bucket:** מנגנון Token Bucket שיאפשר מקסימום 30 בקשות בדקה, ויעקוב אחרי מונה יומי שאינו עולה על 1000.
- **Octopart Bucket:** ניהול בקשות GraphQL.
- **מנגנון Retries:** יישום Exponential Backoff למקרה של חסימות זמניות או שגיאות 429 (Too Many Requests), כך שבקשה שנכשלה תוחזר לתור ותמתין (לדוגמה, 2 שניות, 4 שניות, 8 שניות) לפני ניסיון חוזר.
- שירותי ה-API (כמו `mouser_api.py`) יורשו לקבל נתונים רק באמצעות מתודה כמו `Gatekeeper.request()`.
- **חיבור בפועל (Wiring):** `ShalomCI_SDK.__init__` מקים `ApiGatekeeper` תמיד, ובונה `MouserClient` דרך שיטת עזר פרטית (`_build_default_client`) רק אם `MOUSER_API_KEY` מוגדר בסביבה (נטען מ-`.env` באמצעות `python-dotenv`). אם לא הוזרק `api_client` חיצוני (Dependency Injection לצורכי בדיקות) ואין מפתח בסביבה, `CrossReferenceEngine` נופל בחזרה לערכי N/A - כך שהמערכת אף פעם לא קורסת בהיעדר מפתחות, אלא רק מדווחת נתונים חסרים. `SDK.close()` סוגר את חיבור ה-`httpx.AsyncClient` של ה-Gatekeeper בסיום כל הרצה (CLI ו-GUI).
- **מגבלת שלב נוכחי:** ה-Gatekeeper מוכן לשלושת הספקים (`limiters` עבור mouser/octopart/digikey), אך רק קליינט Mouser מומש ומחובר בפועל. `octopart_api.py` ו-`digikey_api.py` נותרים stubs ריקים לשלב עתידי; `find_alternatives` (חיפוש חלופות FFF) דורש קליינט התומך בקרוס-רפרנס (Octopart) ומחזיר רשימה ריקה בבטחה כשמחובר קליינט שאינו תומך בכך (Mouser).

## 4. ניהול נתונים (Data & Case Management)
כדי לעמוד ביעדי ה-MVP ולנהל את מנגנון ה-"Case Management" בצורה חכמה מבלי להקים שרת מסד נתונים כבד, נשתמש ב-**SQLite** מקומי (מובנה ב-Python).
- המערכת תיצור קובץ `cases.db` מקומי.
- ברגע שה-SDK מזהה רכיב Obsolete ול-`cross_ref` אין חלופות (FFF), תופעל הפונקציה `CaseManager.open_case(mpn, project_name)`.
- מסד הנתונים ישמור טבלה הכוללת: מזהה תיק (Case ID), תאריך פתיחה, מק"ט בעייתי, פרויקט מקושר, וסטטוס התיק (Open / Engineering Review / Closed).
- למשתמש תהיה פקודת CLI נפרדת (לדוגמה `shalomci cases list`) לשליפת התיקים הפתוחים דרך ה-SDK.

## 5. טכנולוגיות וספריות תשתית (Tech Stack)
הסביבה תנוהל בלעדית על ידי `uv` דרך קובץ `pyproject.toml`.
הספריות המרכזיות שיותקנו (Dependencies):
- `httpx`: לביצוע קריאות רשת אסינכרוניות ומהירות (עדיף על `requests` תודות לתמיכה הטבעית ב-`asyncio` הנדרשת עבור ה-Gatekeeper).
- `pandas`: לעיבוד טבלאי מהיר, נרמול שמות עמודות, ומיזוג הנתונים המגיעים מה-APIs השונים לתוך מבנה נתונים אחיד (DataFrames).
- `openpyxl`: לעיצוב והפקת דוח ה-Excel הסופי (.xlsx), כולל יכולות צביעת תאים (לדוגמה: אדום ל-EOL, צהוב ל-NRND).
- `pydantic`: לאימות נתונים (Data Validation) ומידול התשובות שמגיעות מה-APIs למחלקות פייתון מסודרות, כדי למנוע שגיאות הרצה בקוד הפנימי.
- `aiosqlite`: לעבודה אסינכרונית מול ה-SQLite כדי לא לחסום את ה-Event Loop של מערכת ה-Gatekeeper בזמן שמירת "תיק טיפול" (Case).
- `streamlit`: להקמת ממשק המשתמש הגרפי (GUI) - שכבת Proxy דקה בלבד מעל ה-SDK, כולל תמיכה בעיצוב RTL מותאם אישית באמצעות HTML/CSS מוטמע.
- `python-dotenv`: לטעינת מפתחות API וסודות מקובץ `.env` מקומי לתוך משתני הסביבה של התהליך, כך שה-SDK יכול לבנות קליינטים אמיתיים (כמו `MouserClient`) בזמן ריצה מבלי לחשוף מפתחות בקוד.

## 6. ארכיטקטורת ה-GUI (Streamlit, RTL & Accessibility)
שכבת ה-GUI (`src/gui/app.py`) היא Proxy בלבד: מעלה קובץ, קוראת ל-`ShalomCI_SDK`, ומרנדרת את התוצאה. שום חישוב סיכון, ניקוד או קריאת API לא מתבצעים בקובץ זה. לוגיקת הסינון/מיון הטהורה (הניתנת לבדיקה ללא Streamlit) חיה ב-`src/gui/table_controls.py`, ורינדור הטבלה עצמה חי ב-`src/gui/table_render.py`.
- **טבלה ב-iframe מבודד (`components.html`):** `table_render.py` מרנדר את הטבלה בתוך `iframe` מבודד במקום `st.markdown`, כדי לעקוף שני מכשולים: (1) סינון aria-/role attributes על ידי DOMPurify של Streamlit, החוסם תגיות נגישות; (2) התנגשות ה-CSS הגלובלי של האפליקציה עם ה-`position: sticky` של כותרת הטבלה. מאחר ש-`components.html` מריץ HTML/JS גולמי ללא sanitization, וערכי התאים מגיעים ממקורות לא מהימנים (BOM שהועלה, Mouser API), חובה להשתמש ב-`df.style.format(escape="html")` לפני ההמרה ל-HTML כדי למנוע החדרת קוד (XSS).
- **סרגל סינון ומיון (`table_controls.py`):** מיישם חיפוש חופשי, סינון סטטוסים מרובה-בחירה, ומיון. אפשרויות המיון (`sort_options`) נגזרות דינמית מרשימת עמודות ה-DataFrame הנוכחי בפועל (`list(df.columns)`) ולא מרשימה קבועה בקוד, כך שכל עמודה עתידית תופיע אוטומטית בתפריט. עמודות טקסט מפורמטות (`_NUMERIC_TEXT_COLUMNS`, למשל "מחיר ליחידה" או "זמן אספקה") ממוינות על בסיס הערך המספרי שמחולץ מהן ב-Regex ולא לקסיקוגרפית; שאר העמודות נופלות חזרה למיון הרגיל של Pandas.
- **RTL בשתי רמות:** כיוון ה-RTL מוגדר גם גלובלית (`* { direction: rtl !important; }`) וגם במפורש ברמת הבלוק על `.risk-table`, כדי להבטיח שסדר העמודות בטבלה (שנקבע לפי `direction` של האלמנט עצמו, לא רק של אב קדמון) יהיה נכון בכל דפדפן.
- **תוכן מעורב (Bidi):** לתאי הטבלה (`.risk-table td`) מוגדר `unicode-bidi: isolate`, כך שמק"טים באנגלית בתוך שורה עברית מוצגים משמאל-לימין באופן מבודד, מבלי לשבש את זרימת הטקסט העברי הסובב או מיקום מקפים/סימני פיסוק.
- **קידוד צבעים לפי חוק 60-30-10:** רקע ניטרלי (60%), כחול המותג `#0056B3` לכותרות טבלה וניווט (30%, מסמל אמינות), וצבעי אדום/צהוב/ירוק להדגשת סיכון בלבד (10%).
- **נגישות (WCAG 2.2):** ממומש - עמודת הסטטוס תמיד כוללת גם אייקון מפורש (⛔/⚠️/✅/❓) וגם טקסט (`status_icon` ב-`app.py`), כך שהתראת EOL/NRND אינה מסתמכת על צבע בלבד.
- **שכבת תרגום (`src/shared/translations.py`):** ריכוז כל מיפויי הטקסט העברי (סטטוסי מחזור חיים, שמות עמודות) במודול אחד, כדי למנוע כפילות מחרוזות בין ה-GUI, ה-CLI ומנוע הדוחות.
- **ציון סיכון מצטבר (Risk Score):** הציון המצטבר (`calculate_project_score`) מוצג באופן בולט ב-GUI באמצעות `st.metric` מעל טבלת הרכיבים (ראו PRD סעיף 4.3), עם הסבר מלווה (`help`) המפרט שהציון משוקלל מתוך סטטוס מחזור החיים, זמינות מלאי וזמני אספקה של כלל הרכיבים - כדי לאפשר למשתמש שאינו טכני להעריך במבט אחד את רמת סיכון ה-BOM הכוללת. אותו ערך מוחזר גם על ידי ה-SDK ומודפס בממשק ה-CLI.

## 7. אריזת שולחן עבודה (Desktop Packaging - PyInstaller)
כדי לאפשר הפצה למשתמש קצה שאינו טכני כקובץ הפעלה יחיד ל-Windows, מבלי לגעת בקבצי האפליקציה הקיימים:
- **`run_desktop.py`:** נקודת כניסה נפרדת בשורש הפרויקט. קוראת ל-`multiprocessing.freeze_support()` כשורה ראשונה תחת `if __name__ == "__main__"` (מונע לולאת שכפול תהליכים אינסופית תחת PyInstaller), מאתרת פורט פנוי דינמית באמצעות `socket`, פותחת את הדפדפן אוטומטית ב-thread ברקע, ומפעילה את `streamlit.web.cli.main()` באופן פרוגרמטי מול `src/gui/app.py`.
- **פתרון תלות בזמן ריצה (Frozen Path Resolution):** מאחר ש-Streamlit קורא את קובץ ה-`app.py` מהדיסק (`exec`) ולא מייבא אותו כמודול, `run_desktop.py` מזהה סביבת PyInstaller (`sys.frozen`) ומחשב את נתיב הבסיס דרך `sys._MEIPASS` (תיקיית `_internal` במצב `--onedir`) במקום `__file__`.
- **`build.py`:** סקריפט הבנייה, מופעל אך ורק דרך `uv run python build.py` (חובה להריץ על Windows בפועל - PyInstaller אינו תומך ב-Cross-Compilation). מריץ `uv run pyinstaller` עם הדגלים: `--onedir` (טעינה מהירה), `--windowed` (ללא חלון קונסולה), `--collect-all streamlit` ו-`--copy-metadata streamlit/altair` (חובה - שתי הספריות קוראות ל-`importlib.metadata.version()` בזמן ייבוא וקורסות ללא כך תחת PyInstaller), ו-`--add-data "src;src"` (מבטיח ש-`src/gui/app.py` וכל חבילות ה-`src` קיימות כקבצים ממשיים בתיקיית ההרצה, כנדרש להרצת Streamlit).
- **`pyinstaller`** מוגדר כתלות פיתוח (`dependency-groups.dev`) ב-`pyproject.toml`/`uv.lock`, בהתאם לחוק הברזל של ניהול סביבה באמצעות `uv` בלבד.