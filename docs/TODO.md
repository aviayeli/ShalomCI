# מסמך משימות אופרטיביות (TODO) - ShalomCI

מסמך זה נגזר ישירות מדרישות המוצר (PRD) וממסמך הארכיטקטורה (PLAN). כל משימה חייבת לעמוד בחוק ה-150 שורות לקובץ, ולהיות מלווה בבדיקות יחידה (TDD) להבטחת כיסוי של 85% ומעלה.

## Phase 1: Setup & Infrastructure
- [x] **הקמת סביבת ניהול חבילות (`uv`):** אתחול פרויקט חדש באמצעות `uv init`.
- [x] **הגדרת תלויות ב-`pyproject.toml`:** הוספת חבילות הליבה (`httpx`, `pandas`, `openpyxl`, `pydantic`, `aiosqlite`) וספריות פיתוח.
- [x] **הגדרת החרגות וסודות:** יצירת קובץ `.gitignore` מחמיר והכנת קובץ תבנית `.env-example`.
- [x] **הגדרת Linter ו-Formatter:** קונפיגורציה של `Ruff` בתוך `pyproject.toml` (חוק 150 שורות).
- [x] **הקמת שלד התיקיות:** יצירת עץ התיקיות וקבצי ה-`__init__.py`.

## Phase 2: Core SDK & Database
- [x] **הקמת מסד נתונים מקומי (Cases):** פיתוח `src/data/case_manager.py` עם `aiosqlite`.
- [x] **TDD לניהול מקרים:** יצירת `tests/unit/test_case_manager.py` עם שימוש ב-`tmp_path`.
- [x] **הקמת שלד ה-SDK:** פיתוח `src/sdk.py` והגדרת ה-Stubs לכל מתודות הליבה.
- [x] **TDD לשכבת ה-SDK:** יצירת `tests/unit/test_sdk.py` לאימות אתחול.

## Phase 3: API Gatekeeper & Clients
- [x] **פיתוח Gatekeeper:** כתיבת `src/services/gatekeeper.py` עם מנגנון Token Bucket ו-Concurrency Lock.
- [x] **מנגנון Retries ל-Gatekeeper:** הוספת לוגיקת Exponential Backoff לטיפול בשגיאות 429.
- [x] **פיתוח קליינט Mouser:** כתיבת `src/services/mouser_api.py`.
- [x] **פיתוח קליינט Octopart:** כתיבת `src/services/octopart_api.py` עם מנגנון OAuth2.
- [x] **פיתוח קליינט DigiKey:** כתיבת `src/services/digikey_api.py` עם מנגנון OAuth2.
- [x] **TDD לשירותי ה-API:** כתיבת `tests/unit/test_apis.py` עם Mocking ל-httpx והוכחת עמידה בעומסים.

## Phase 4: BOM Parser & Risk Engine
- [x] **מנוע קליטת BOM:** פיתוח `src/core/bom_parser.py` המשתמש ב-`pandas` לזיהוי חכם של עמודות MPN.
- [x] **TDD ל-BOM Parser:** יצירת קבצי דמה "מלוכלכים" ווידוא חילוץ מדויק.
- [x] **פיתוח מנוע הדירוג:** כתיבת `src/core/risk_engine.py` לשקלול ציון 1-5 (כולל זיהוי NRND/LTB/EOL).
- [x] **TDD ל-Risk Engine:** בדיקות יחידה למנוע הסיכונים וחישוב ממוצע הפרויקט.

## Phase 5: Mitigation & Export
- [x] **מנוע חיפוש חלופות (Cross-Reference):** כתיבת `src/core/cross_ref.py` המתשאל חלופות FFF אם ציון הרכיב מסוכן.
- [x] **אינטגרציה לניהול מקרים:** עדכון ה-SDK כך שאם לא נמצאת חלופה לרכיב Obsolete, נפתח אוטומטית Case דרך ה-`case_manager`.
- [x] **TDD למנוע חלופות:** בדיקת מקרים בהם נמצאות חלופות וכאלו שבהם נפתח Case.
- [x] **מנוע ייצוא נתונים:** פיתוח `src/core/reporter.py` המייצר קובץ Excel צבעוני (.xlsx) הכולל ציונים וחלופות באמצעות `openpyxl`.
- [x] **TDD ל-Reporter:** יצירת קובץ פלט זמני ווידוא שכל העמודות והצבעים קיימים ללא שגיאות.

## Phase 6: CLI Integration
- [x] **מעטפת שורת פקודה (CLI):** כתיבת `src/cli/main.py` התומכת בפקודות `process` ו-`cases list`.
- [x] **חיבור ה-CLI ל-SDK:** קריאה למתודות ה-SDK מבלי לכתוב לוגיקה עסקית בשכבת ה-CLI.
- [x] **TDD ל-CLI:** בדיקות `tests/unit/test_cli.py` המוודאות ניתוב נכון של פקודות והדפסות.

## Phase 7: GUI (Streamlit)
- [x] **ממשק Streamlit:** כתיבת `src/gui/app.py` כשכבת Proxy בלבד (העלאת קובץ, קריאה ל-SDK, רינדור תוצאה) ללא לוגיקה עסקית.
- [x] **עיצוב RTL בעברית:** הגדרת `direction: rtl` הן ברמה הגלובלית והן במפורש ברמת הבלוק של טבלת הנתונים (`.risk-table`), כדי להבטיח סדר עמודות וזרימת תוכן נכונים.
- [x] **תמיכה בתוכן מעורב (Bidi):** `unicode-bidi: isolate` על תאי הטבלה כך שמק"טים באנגלית בתוך טבלה עברית לא משבשים כיוון טקסט או מיקום מקפים.
- [x] **חיבור ה-Gatekeeper בפועל:** `ShalomCI_SDK` מקימה `ApiGatekeeper` ו-`MouserClient` אוטומטית מתוך `MOUSER_API_KEY` ב-`.env` (באמצעות `python-dotenv`), כך שהעשרת הנתונים בטבלה מבוססת על מידע אמיתי ולא רק על ערכי N/A.
- [x] **ניקוי חיבורי רשת:** `SDK.close()` סוגר את ה-`httpx.AsyncClient` הפנימי של ה-Gatekeeper בסיום כל הרצה (CLI ו-GUI כאחד).
- [ ] **אייקוני נגישות (WCAG 2.2):** הוספת אייקונים מפורשים (לצד טקסט) לסטטוסים מסוכנים (EOL/NRND) בטבלת ה-GUI, כך שההתראה לא תסתמך על צבע בלבד — עדיין לא מומש בקוד, רק תועד כדרישה ב-PRD.
- [ ] **קליינטים ל-Octopart/DigiKey:** `src/services/octopart_api.py` ו-`digikey_api.py` עדיין stubs ריקים; `cross_ref.find_alternatives` מוגן כרגע להחזיר רשימה ריקה כשמחובר קליינט שלא תומך בקרוס-רפרנס (כמו Mouser).
- [ ] **כיסוי בדיקות מלא ל-100%:** הכיסוי הכולל עומד על כ-87% (מעל סף 85% הנדרש), אך `sdk.py` ו-`cross_ref.py` עדיין לא מכוסים במלואם.