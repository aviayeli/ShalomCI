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
│   │   ├── octopart_api.py    # אינטגרציה מול Octopart/Nexar Supply GraphQL (OAuth2) - מומש ומחובר בפועל
│   │   └── digikey_api.py     # אינטגרציה מול DigiKey Product Information V4 (OAuth2) - מומש ומחובר בפועל
│   ├── data/
│   │   └── case_manager.py    # ניהול מקרים מקומי (Cases) עבור רכיבים ללא חלופה
│   ├── shared/
│   │   └── translations.py    # שכבת תרגום עברית מרכזית (סטטוסים, שמות עמודות)
│   ├── cli/
│   │   └── main.py            # ממשק שורת הפקודה (Proxy בלבד, ללא לוגיקה)
│   └── gui/
│       ├── app.py                   # ממשק Streamlit בעברית/RTL (Proxy בלבד, ללא לוגיקה)
│       ├── ui_helpers.py            # הודעת פתיחה + תבנית BOM להורדה (render_welcome_header)
│       ├── accessibility_widget.py  # הזרקת תפריט הנגישות Enable.co.il ל-window.parent
│       ├── table_rows.py            # בניית שורות הטבלה מנתוני הרכיבים (status_icon/build_rows, ניתן לבדיקה)
│       ├── table_controls.py        # לוגיקת סינון/מיון טהורה (ניתנת לבדיקה, ללא Streamlit)
│       └── table_render.py          # רינדור הטבלה ב-st.dataframe הטבעי + column_config
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
- **חיבור בפועל (Wiring):** `ShalomCI_SDK.__init__` מקים `ApiGatekeeper` תמיד, ובונה `MouserClient`/`DigiKeyClient`/`OctopartClient` דרך שיטות עזר פרטיות סימטריות (`_build_default_client` / `_build_digikey_client` / `_build_octopart_client`) רק אם `MOUSER_API_KEY`, `DIGIKEY_CLIENT_ID`+`DIGIKEY_CLIENT_SECRET`, או `OCTOPART_CLIENT_ID`+`OCTOPART_CLIENT_SECRET` בהתאמה מוגדרים בסביבה (נטענים מ-`.env` באמצעות `python-dotenv`). אם לא הוזרקו קליינטים חיצוניים (Dependency Injection לצורכי בדיקות) ואין מפתחות בסביבה, `CrossReferenceEngine` נופל בחזרה לערכי N/A/ברירות מחדל בעברית - כך שהמערכת אף פעם לא קורסת בהיעדר מפתחות, אלא רק מדווחת נתונים חסרים. `SDK.close()` סוגר את חיבור ה-`httpx.AsyncClient` של ה-Gatekeeper בסיום כל הרצה (CLI ו-GUI).
- **DigiKey (Product Information V4) - מומש ומחובר בפועל:** `DigiKeyClient` (ב-`services/digikey_api.py`) מאמת מול DigiKey באמצעות זרימת OAuth2 Client Credentials (`POST /v1/oauth2/token`, עם מיחזור טוקן עד לפקיעת תוקף) ושולף פרטי רכיב מול `GET /products/v4/search/{mpn}/productdetails`. **כל** קריאה - כולל שליפת הטוקן - מנותבת דרך `ApiGatekeeper.request(provider="digikey", ...)`. מלאי/מחיר (כמספרים גולמיים) וזמן אספקה נשלפים על ידי `CrossReferenceEngine.get_digikey_data()` **בנוסף** ל-Mouser (side-by-side, לא כתחליף) ומוצגים בעמודות GUI נפרדות (סעיף 6) - אינם משפיעים על `risk_score`/`lifecycle_status` המרכזיים שממשיכים להיגזר אך ורק מ-Mouser (DigiKey אינו מחזיר שדה מחזור חיים כלל - ראו סעיף 6).
- **Octopart/Nexar (Supply GraphQL) - מומש ומחובר בפועל, תפקיד כפול:** `OctopartClient` (ב-`services/octopart_api.py`) מאמת מול Nexar Identity Server (`POST https://identity.nexar.com/connect/token`) ומריץ שאילתת GraphQL יחידה (שדה עליון `supSearch`) מול `https://api.nexar.com/graphql`, גם דרך `ApiGatekeeper.request(provider="octopart", ...)` בלבד. (1) מלאי/מחיר (כמספרים גולמיים) וזמן אספקה נשלפים על ידי `CrossReferenceEngine.get_octopart_data()` side-by-side לצד Mouser/DigiKey, ללא השפעה על `risk_score` (Octopart אינו מחזיר שדה מחזור חיים - `lifecycleStatus` לא קיים על `SupPart` בסכימת Nexar בפועל). (2) `search_cross_reference` (alias ל-`search_part`, אותה שאילתה) הופך את Octopart לספק ה-FFF (`find_alternatives`) בפועל - הראשון שהתחבר בפועל לתפקיד שתוכנן לו מלכתחילה (ראו סעיף 6/PRD 4.4).
- **סטטוס Gatekeeper:** שלושת הספקים (`limiters` עבור mouser/octopart/digikey) מומשו ומחוברים בפועל - Mouser, DigiKey ו-Octopart. `find_alternatives` מעדיף את `octopart_client`, ונופל בחזרה ל-`api_client` הראשי רק אם הוא עצמו תומך בקרוס-רפרנס (לצורכי בדיקות/הזרקה ידנית); מחזיר רשימה ריקה בבטחה כשאף אחד מהם לא תומך בכך.

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
שכבת ה-GUI (`src/gui/app.py`) היא Proxy בלבד: מעלה קובץ, קוראת ל-`ShalomCI_SDK`, ומרנדרת את התוצאה. שום חישוב סיכון, ניקוד או קריאת API לא מתבצעים בקובץ זה. בניית שורות הטבלה (`status_icon`/`build_rows`/`recommended_vendor`) חיה ב-`src/gui/table_rows.py`, לוגיקת הסינון/מיון הטהורה חיה ב-`src/gui/table_controls.py`, ורינדור הטבלה עצמה חי ב-`src/gui/table_render.py` - פיצול שנדרש כדי לעמוד בחוק 150 השורות לקובץ.
- **טבלה ב-`st.dataframe` הטבעי (לא iframe/רכיב צד-שלישי):** `table_render.py` מרנדר באמצעות `st.dataframe` + `column_config` בלבד - **לא** `st_aggrid` או כל רכיב JS חיצוני, כדי להימנע מ-timeouts ב-WebSocket וכשלי רינדור iframe שנצפו בעבר עם הגישה הקודמת (`pandas.Styler.to_html` בתוך `st.iframe`/`components.html`). `st.dataframe` תומך באופן טבעי ב-sticky header ותגיות נגישות (ARIA) ללא צורך בפתרונות עוקפים - ה-workaround הישן הוסר במלואו.
- **`st.column_config`:** `ProgressColumn` לציון הסיכון (0-5, Mouser) ולעמודות המלאי (0-10,000 כקנה-מידה חזותי בלבד, לא הגבלה על הנתון), `NumberColumn` עם פורמט printf מותאם (`"₪ %.2f"`) לעמודות המחיר.
- **הודעת פתיחה ותבנית BOM (`ui_helpers.py`):** `render_welcome_header()` מוצג מיד אחרי הכותרת - מסביר בקצרה את מקורות הנתונים (Mouser/DigiKey/Octopart) ואת דרישת עמודת ה-MPN, ומציע תבנית CSV ריקה להורדה. מיישם את היוריסטיקות של Nielsen ל"System Status Visibility" ו-"Error Prevention" - מונע מראש כשל זיהוי עמודות ב-`BomParser`.
- **השוואת שלושה ספקים side-by-side, מחזור חיים פעם אחת בלבד (`table_rows.py`):** `PRICE_STOCK_VENDORS` ממפה שם ספק לתצוגה (Mouser/DigiKey/Octopart) לקידומת השדה ב-comp, ו-`vendor_price_stock_columns()` בונה מהן שתי עמודות מספריות גולמיות ("מחיר (₪) - {ספק}", "מלאי זמין - {ספק}") לכל ספק בלולאה - כדי למנוע שכפול קוד. **מחזור חיים וציון סיכון מוצגים פעם אחת בלבד** (מקור: Mouser בלעדית, עמודות "סטטוס"/"ציון סיכון") - `digikey_lifecycle`/`octopart_lifecycle` הוסרו לגמרי מהקוד (DigiKey/Octopart לא מספקים מידע כזה בפועל בפרויקט זה). `recommended_vendor()` (פונקציה טהורה) קובעת עמודת "ספק מומלץ" ראשונה: מעדיפה את המחיר הזול ביותר מבין הספקים שדיווחו מחיר, ונופלת בחזרה למלאי הגבוה ביותר אם אף ספק לא דיווח מחיר; `None` (חוסר נתון) לעולם לא "מנצח" ערך אמיתי (גם 0).
- **מגבלה ידועה - אין כותרות מקובצות אמיתיות:** נבדק ואומת (Streamlit 1.58) ש-`st.dataframe` **אינו** תומך ב-`pandas.MultiIndex` על עמודות יחד עם `column_config` - השילוב קורס (`TypeError: keys must be str, int, float, bool or None, not tuple`, כי `column_config` דורש מפתחות מחרוזת). לכן נבחרו עמודות שטוחות עם שם קבוצה+ספק בשם עצמו (למשל "מחיר (₪) - Mouser"), לא כותרת-על מרושתת אמיתית - כדי לשמר את `NumberColumn`/`ProgressColumn` שנחשבו לחשובים יותר בפועל. אם בעתיד המשקל ישתנה, האפשרות לחזור ל-`pandas.Styler`/HTML קיימת אך במחיר איבוד יתרונות `st.dataframe` (ראו לעיל).
- **סרגל סינון ומיון (`table_controls.py`):** מיישם חיפוש חופשי, סינון סטטוסים מרובה-בחירה, ומיון. אפשרויות המיון (`sort_options`) נגזרות דינמית מרשימת עמודות ה-DataFrame הנוכחי בפועל (`list(df.columns)`) ולא מרשימה קבועה בקוד, כך שכל עמודה עתידית תופיע אוטומטית בתפריט. עמודות המחיר/מלאי מספריות (float) ולכן ממוינות נכון באופן טבעי ללא צורך בחילוץ Regex; רק "זמן אספקה" (Mouser, טקסט מפורמט) עדיין דורש זאת (`_NUMERIC_TEXT_COLUMNS`).
- **RTL וטיפוגרפיה (`RTL_CSS` ב-`app.py`):** כיוון RTL גלובלי, גופן נקי (`Segoe UI`/Arial), גודל גופן בסיסי מוגדל מעט (1.05rem), ואיסור מוחלט על italics (`font-style: normal !important` - קריאות עברית). **מגבלה ידועה:** מאחר ש-`st.dataframe` (בניגוד לפתרון ה-iframe/HTML הקודם) מצייר את הרשת הפנימית (glide-data-grid) על HTML canvas, לא ניתן לעצב תא-תא בתוך הרשת עצמה באמצעות CSS גלובלי - רק את המכולות (containers) סביבה.
- **קידוד צבעים לפי חוק 60-30-10:** רקע ניטרלי (60%), כחול המותג `#0056B3` (30%, מסמל אמינות), וצבעי אדום/צהוב/ירוק להדגשת סיכון בלבד (10%) - ב-`st.column_config.ProgressColumn` של ציון הסיכון.
- **נגישות (WCAG 2.2):** עמודת הסטטוס תמיד כוללת גם אייקון מפורש (⛔/⚠️/✅/❓) וגם טקסט (`status_icon` ב-`table_rows.py`), כך שהתראת EOL/NRND אינה מסתמכת על צבע בלבד. `accessibility_widget.py` מזריק את תפריט הנגישות של Enable.co.il ל-`window.parent.document.head` באמצעות `st.iframe` בגודל 1x1 (המינימום החוקי - `height`/`width=0` נדחים על ידי Streamlit).
- **שכבת תרגום (`src/shared/translations.py`):** ריכוז מיפויי הטקסט העברי (סטטוסי מחזור חיים) ו-`extract_number()` (חילוץ מספר גולמי ממחרוזת מפורמטת של ספק, למשל מלאי/מחיר Mouser) במודול אחד, כדי למנוע כפילות בין ה-GUI, ה-CLI ומנוע הדוחות.
- **ציון סיכון מצטבר (Risk Score):** הציון המצטבר (`calculate_project_score`) מוצג באופן בולט ב-GUI באמצעות `st.metric` מעל טבלת הרכיבים (ראו PRD סעיף 4.3), עם הסבר מלווה (`help`) המפרט שהציון משוקלל מתוך סטטוס מחזור החיים, זמינות מלאי וזמני אספקה של כלל הרכיבים - כדי לאפשר למשתמש שאינו טכני להעריך במבט אחד את רמת סיכון ה-BOM הכוללת. אותו ערך מוחזר גם על ידי ה-SDK ומודפס בממשק ה-CLI.

## 7. אריזת שולחן עבודה (Desktop Packaging - PyInstaller)
כדי לאפשר הפצה למשתמש קצה שאינו טכני כקובץ הפעלה יחיד ל-Windows, מבלי לגעת בקבצי האפליקציה הקיימים:
- **`run_desktop.py`:** נקודת כניסה נפרדת בשורש הפרויקט. קוראת ל-`multiprocessing.freeze_support()` כשורה ראשונה תחת `if __name__ == "__main__"` (מונע לולאת שכפול תהליכים אינסופית תחת PyInstaller), מאתרת פורט פנוי דינמית באמצעות `socket`, פותחת את הדפדפן אוטומטית ב-thread ברקע, ומפעילה את `streamlit.web.cli.main()` באופן פרוגרמטי מול `src/gui/app.py`.
- **פתרון תלות בזמן ריצה (Frozen Path Resolution):** מאחר ש-Streamlit קורא את קובץ ה-`app.py` מהדיסק (`exec`) ולא מייבא אותו כמודול, `run_desktop.py` מזהה סביבת PyInstaller (`sys.frozen`) ומחשב את נתיב הבסיס דרך `sys._MEIPASS` (תיקיית `_internal` במצב `--onedir`) במקום `__file__`.
- **`build.py`:** סקריפט הבנייה, מופעל אך ורק דרך `uv run python build.py` (חובה להריץ על Windows בפועל - PyInstaller אינו תומך ב-Cross-Compilation). מריץ `uv run pyinstaller` עם הדגלים: `--onedir` (טעינה מהירה), `--windowed` (ללא חלון קונסולה), `--collect-all streamlit` ו-`--copy-metadata streamlit/altair` (חובה - שתי הספריות קוראות ל-`importlib.metadata.version()` בזמן ייבוא וקורסות ללא כך תחת PyInstaller), ו-`--add-data "src;src"` (מבטיח ש-`src/gui/app.py` וכל חבילות ה-`src` קיימות כקבצים ממשיים בתיקיית ההרצה, כנדרש להרצת Streamlit).
- **`pyinstaller`** מוגדר כתלות פיתוח (`dependency-groups.dev`) ב-`pyproject.toml`/`uv.lock`, בהתאם לחוק הברזל של ניהול סביבה באמצעות `uv` בלבד.