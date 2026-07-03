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
- [x] **אייקוני נגישות (WCAG 2.2):** הוספת אייקונים מפורשים (⛔/⚠️/✅/❓) לצד הטקסט לכל סטטוס בטבלת ה-GUI (`status_icon` ב-`app.py`), כך שההתראה לא מסתמכת על צבע בלבד.
- [x] **סרגל סינון ומיון:** `src/gui/table_controls.py` (חיפוש חופשי, סינון סטטוסים מרובה-בחירה, מיון עם חילוץ מספר מ-Regex לעמודות טקסט מפורמטות) ו-`tests/unit/test_table_controls.py`.
- [x] **מיון דינמי לכל העמודות:** `sort_options(df)` גוזר את אפשרויות המיון מרשימת עמודות ה-DataFrame בפועל, במקום רשימה קבועה בקוד - כל עמודה עתידית מופיעה אוטומטית בתפריט.
- [x] **טבלה ב-iframe מבודד:** `src/gui/table_render.py` מרנדר את הטבלה בתוך `components.html` כדי לתקן sticky header ואת סינון ה-aria attributes של DOMPurify (עם `format(escape="html")` למניעת XSS ממקורות לא מהימנים).
- [x] **שכבת תרגום עברית מרכזית:** `src/shared/translations.py`, מלאי ספקים (Vendor Inventory) ושדות Mouser מורחבים (זמן אספקה, מחיר, RoHS, אריזה, חלופה מוצעת) בטבלת ה-GUI.
- [x] **ציון סיכון מצטבר (Risk Score) ב-GUI:** `st.metric` המציג את הציון המצטבר (`calculate_project_score`) מוצג באופן בולט מעל טבלת הרכיבים, עם הסבר מלווה (`help`) שמפרט שהציון משוקלל מתוך סטטוס מחזור החיים, זמינות מלאי וזמני אספקה - ראו PRD סעיף 4.3 ו-PLAN סעיף 6.

## Phase 8: אריזת Desktop (PyInstaller)
- [x] **נקודת כניסה ל-Desktop:** `run_desktop.py` - `multiprocessing.freeze_support()`, איתור פורט פנוי דינמי, פתיחת דפדפן אוטומטית ב-thread, והרצת `streamlit.web.cli.main()` פרוגרמטית. פותר נתיבים גם תחת PyInstaller (`sys._MEIPASS`).
- [x] **סקריפט בנייה:** `build.py` (מופעל דרך `uv run python build.py`) - `--onedir --windowed --collect-all streamlit --copy-metadata streamlit --copy-metadata altair --add-data "src;src"`.
- [x] **`pyinstaller` כתלות פיתוח:** נוסף ל-`dependency-groups.dev` ב-`pyproject.toml`/`uv.lock` באמצעות `uv add --dev pyinstaller` בלבד (ללא `pip`).

## Phase 9: אינטגרציית DigiKey (Product Information V4 / SupplyChain)
- [x] **סודות והגדרה:** `DIGIKEY_CLIENT_ID`/`DIGIKEY_CLIENT_SECRET` ב-`.env-example`, נטענים אוטומטית על ידי `ShalomCI_SDK._build_digikey_client()` (אותו דפוס בדיוק כמו `_build_default_client()` של Mouser).
- [x] **קליינט DigiKey אמיתי:** `src/services/digikey_api.py` - `DigiKeyClient` מממש זרימת OAuth2 Client Credentials מול `POST /v1/oauth2/token` (עם מיחזור טוקן עד לפקיעת תוקף), ושליפת רכיב מול `GET /products/v4/search/{mpn}/productdetails`. **כל** קריאה (כולל שליפת הטוקן) מנותבת דרך `ApiGatekeeper.request(provider="digikey", ...)` - אין קריאות רשת ישירות עוקפות.
- [x] **חילוץ שדות:** `DigiKeyClient.parse_extra_fields` מחלץ ומתרגם מחזור חיים (`ProductStatus.Status`), מלאי (`QuantityAvailable`), זמן אספקה (`ManufacturerLeadWeeks`) ומחיר (`UnitPrice`).
- [x] **מיזוג side-by-side ב-SDK:** `CrossReferenceEngine.get_digikey_data()` (ב-`cross_ref.py`) נקרא מתוך `enrich_components` בנוסף (לא במקום) ל-`get_part_data` של Mouser; נכשל בעדינות לברירות מחדל בעברית (`DIGIKEY_FIELD_DEFAULTS`) ואינו משפיע על `risk_score`/`lifecycle_status` המרכזיים.
- [x] **עמודות GUI חדשות:** `build_rows` ב-`app.py` מוסיף "מחזור חיים (DigiKey)", "מלאי (DigiKey)", "זמן אספקה (DigiKey)", "מחיר ליחידה (DigiKey)" לצד עמודות Mouser הקיימות; `sort_options(df)` הדינמי (Phase 7) קולט אותן אוטומטית ללא כל שינוי בתפריט המיון עצמו.
- [x] **TDD:** `tests/unit/test_apis.py` (קליינט DigiKey: אימות, מיחזור טוקן, חילוץ שדות), `tests/unit/test_cross_ref.py` (מיזוג/ברירות מחדל/שגיאות רשת), `tests/unit/test_sdk.py` (חיווט מהסביבה + מיזוג ב-enrich_components), `tests/unit/test_gui_app.py` (עמודות חדשות בטבלה). 72 בדיקות עוברות, כיסוי כולל 93%.

## Phase 10: אינטגרציית Octopart (Nexar Supply GraphQL)
- [x] **סודות והגדרה:** `OCTOPART_CLIENT_ID`/`OCTOPART_CLIENT_SECRET` ב-`.env-example` (מחליפים את placeholders `NEXAR_CLIENT_ID/SECRET` הישנים שלא היו בשימוש בקוד), נטענים אוטומטית על ידי `ShalomCI_SDK._build_octopart_client()` - אותו דפוס בדיוק כמו Mouser/DigiKey.
- [x] **קליינט Octopart אמיתי:** `src/services/octopart_api.py` - `OctopartClient` מממש זרימת OAuth2 Client Credentials מול Nexar Identity Server (`POST https://identity.nexar.com/connect/token`, עם מיחזור טוקן עד לפקיעת תוקף), ושאילתת GraphQL יחידה מול `https://api.nexar.com/graphql` (שדה עליון `supSearch`) הכוללת גם מחזור חיים/מלאי/זמן אספקה/מחיר וגם `similarParts`. **כל** קריאה (כולל שליפת הטוקן) מנותבת דרך `ApiGatekeeper.request(provider="octopart", ...)`.
- [x] **חילוץ שדות:** `OctopartClient.parse_extra_fields` מחלץ ומתרגם מחזור חיים (`lifecycleStatus`), מלאי (`inventoryLevel` מהמוכר הראשון עם הצעה), זמן אספקה (`factoryLeadDays`) ומחיר (מדרגת כמות=1, או המדרגה הראשונה כברירת מחדל).
- [x] **חיפוש חלופות FFF מחובר בפועל:** `CrossReferenceEngine.find_alternatives` מעדיף כעת את `octopart_client` (ספק הקרוס-רפרנס הטבעי) על פני `api_client` הראשי, תוך שמירה על נפילה-חזרה קיימת (לבדיקות/הזרקה ידנית) - `search_cross_reference` הוא alias לאותה שאילתת GraphQL של `search_part`.
- [x] **מיזוג side-by-side ב-SDK:** `CrossReferenceEngine.get_octopart_data()` נקרא מתוך `enrich_components` בנוסף ל-Mouser/DigiKey; נכשל בעדינות ל-`OCTOPART_FIELD_DEFAULTS` בעברית ואינו משפיע על `risk_score`/`lifecycle_status` המרכזיים.
- [x] **עמודות GUI חדשות:** לוגיקת בניית השורות (`build_rows`) הועברה למודול ייעודי `src/gui/table_rows.py` (יחד עם `status_icon`) כדי לעמוד בחוק 150 השורות אחרי הוספת Octopart; מוסיפה "מחזור חיים/מלאי/זמן אספקה/מחיר ליחידה (Octopart)" לצד עמודות Mouser/DigiKey. `sort_options(df)` הדינמי קולט אותן אוטומטית.
- [x] **TDD:** `tests/unit/test_apis.py` (קליינט Octopart: אימות, מיחזור טוקן, GraphQL, חילוץ שדות), `tests/unit/test_cross_ref.py` (מיזוג/ברירות מחדל/שגיאות רשת/עדיפות ל-Octopart ב-find_alternatives), `tests/unit/test_sdk.py` (חיווט מהסביבה + מיזוג ב-enrich_components), `tests/unit/test_table_rows.py` (עמודות חדשות בטבלה, כולל build_rows/status_icon שהועברו מ-test_gui_app.py). 88 בדיקות עוברות, כיסוי כולל 94%.

## Phase 11: תיקון Retry קריטי + תפריט נגישות (Enable.co.il)
- [x] **תיקון תקלה קריטית - חסימת UI מלאה:** לאחר שילוב Octopart, שאילתת ה-GraphQL (`supSearch`) החזירה 400 Bad Request על כל מק"ט, וה-Gatekeeper ניסה שוב (Exponential Backoff) על כל שגיאת 4xx כאילו הייתה 429/5xx חולפת - לולאת ה-Retry הסינכרונית הזו על פני כל רכיבי ה-BOM חסמה את חיבור ה-WebSocket של Streamlit לדקות ארוכות.
- [x] **`src/services/gatekeeper.py` - כישלון מהיר על 4xx:** `ApiGatekeeper.request` מפצל כעת את הטיפול בשגיאות: 429 ממשיך להיות מטופל כברירת מחדל הקיימת (Retry עם Backoff); כל שגיאת 4xx אחרת (400/401/403/404 וכו') נכשלת **מיידית** ללא Retry; שגיאת 5xx וכשלי רשת (`httpx.RequestError`) ממשיכים ליהנות מה-Retry/Backoff הרגיל.
- [x] **`src/services/octopart_api.py` - חשיפת שגיאת GraphQL מדויקת:** `_log_http_error` מדפיס ללוג את `response.text` הגולמי (וקוד הסטטוס) בכל כשל HTTP - הן בשלב שליפת הטוקן והן בשאילתת `supSearch` - כדי לחשוף את הודעת השגיאה המדויקת של Nexar (למשל שם שדה שגוי בסכימה) לצורך תיקון השאילתה.
- [x] **TDD:** `tests/unit/test_apis.py` - `test_gatekeeper_fails_fast_on_400_client_error_no_retry`, `test_gatekeeper_retries_on_500_server_error`, `test_octopart_search_part_logs_response_body_and_reraises_on_400`, `test_octopart_token_request_logs_and_reraises_on_400`. 96 בדיקות עוברות, כיסוי כולל 94%.
- [x] **תפריט נגישות Enable.co.il:** `src/gui/accessibility_widget.py` (מודול ייעודי חדש, בהתאם לדפוס הפיצול הקיים ב-`table_rows.py`/`table_controls.py`/`table_render.py`) - `inject_accessibility_widget()` מזריק אלמנט `<script>` ל-`window.parent.document.head` (לא ל-DOM המבודד של ה-iframe עצמו), כולל בדיקת `getElementById` למניעת הזרקה כפולה בכל rerun של Streamlit. נקרא מתוך `app.py::main()` מיד אחרי `st.set_page_config`.
- [x] **TDD לתפריט הנגישות:** `tests/unit/test_accessibility_widget.py` - מוודא את כתובת הסקריפט, היעד (`window.parent`), ומנגנון מניעת הכפילות (ראו Phase 12 לגבי ממדי ה-iframe בפועל).

## Phase 12: תיקון שאילתת Octopart + מיגרציית st.iframe
- [x] **תיקון שאילתת GraphQL בפועל:** ה-smoke test חשף שגיאת 400 מדויקת: `"The field 'lifecycleStatus' does not exist on the type 'SupPart'"`. הוסר השדה `lifecycleStatus` מ-`_PART_QUERY` ב-`octopart_api.py`; `OctopartClient.parse_extra_fields` מחזיר כעת `"octopart_lifecycle": "לא ידוע"` באופן קבוע (Mouser נותר המקור היחיד למחזור חיים/ציון סיכון) - עמודות המלאי, המחיר וזמן האספקה של Octopart מאוכלסות כעת בפועל.
- [x] **מיגרציה מ-`st.components.v1.html` המיושן ל-`st.iframe`:** `accessibility_widget.py` עודכן להשתמש ב-`st.iframe` (המזהה אוטומטית מחרוזת HTML גולמית, כולל אותו בידוד sandbox - הטריק `window.parent` עדיין עובד). **אומת דרך הרצה אמיתית** (`streamlit.testing.v1.AppTest`, לא רק מוקים): `height=0`/`width=0` שנעבדו מקודם נדחים על ידי `st.iframe` (`StreamlitInvalidWidthError` - נדרש int חיובי, `"stretch"` או `"content"`) - תוקן ל-1x1 פיקסלים (המינימום החוקי, בפועל בלתי נראה).
- [x] **TDD:** עודכנו הבדיקות ב-`test_apis.py`/`test_cross_ref.py` (מחזור חיים = "לא ידוע" תמיד) ו-`test_accessibility_widget.py` (מוקים ל-`st.iframe` במקום `components.html`, ממדים 1x1). 96 בדיקות עוברות, כיסוי כולל 94%.

## Phase 13: Null-Safety מלא ל-Octopart + סגירת מיגרציית st.iframe
- [x] **בעיה שהתגלתה:** אחרי תיקון שאילתת ה-400 (Phase 12), עמודות Octopart נותרו ריקות והלוג הראה `'NoneType' object has no attribute 'get'` ב-`find_alternatives`. הסיבה: Nexar מחזיר `null` מפורש (לא רק מפתח חסר) בכל שלב במבנה - `data`/`supSearch`/`results`/`part`/`sellers`/`offers`/`prices` - ואף עבור איברים בודדים בתוך רשימה (למשל `results: [null]`). `dict.get(key, default)` מגן רק על מפתח **חסר**, לא על ערך `null` מפורש - `{"data": None}.get("data", {})` עדיין מחזיר `None`.
- [x] **`src/core/cross_ref.py` - `find_alternatives`:** כל שרשרת ה-`.get(key, default)` הוחלפה בתבנית הבטוחה `(x or {}).get(key)`/`(x or []).get(...)` בכל שלב; תוצאת `similarParts` מסוננת מאיברי `None` בודדים לפני שהיא מוחזרת (כדי לא להעביר `None` הלאה לצרכנים כמו `build_rows`).
- [x] **`src/services/octopart_api.py` - `parse_extra_fields`:** אותה תבנית הוחלה על `results[0]`, `sellers`, ואיברי `offers`/`prices` בודדים בתוך רשימותיהם (סינון `if seller`/`if o`/`if p`), כדי שרכיב עם מידע מוכר חלקית בלבד (מוכר אחד תקין מתוך כמה, שחלקם `null`) עדיין יניב תוצאה נכונה במקום ליפול לברירת מחדל.
- [x] **מציאת קריאת `components.html` שנותרה בפועל:** מקור אזהרת ה-Deprecation שנמשכה היה `src/gui/table_render.py` (טבלת הסיכונים הראשית), שלא טופל בסבב הקודם (טופל אז רק `accessibility_widget.py`) - הוחלף גם הוא ל-`st.iframe(full_html, height=600)`. חיפוש מלא בקוד (`grep -r "components\.v1\|components\.html"`) אישר שאין יותר אף שימוש ב-API המיושן בכל הריפו.
- [x] **DRY:** `get_digikey_data`/`get_octopart_data` (כמעט זהים) אוחדו למתודה גנרית משותפת `_get_secondary_vendor_data` כדי לעמוד בחוק 150 השורות אחרי תוספות ה-null-safety.
- [x] **אימות:** תוקן ואומת בפועל דרך `streamlit.testing.v1.AppTest` (הרצת סקריפט אמיתית, לא רק מוקים) - גם עבור `inject_accessibility_widget()` וגם עבור `render_table()` - ללא חריגות וללא אזהרת Deprecation בלוג. נבדק גם ידנית מול payload מלא-nulls שמדמה תגובת Nexar אמיתית לרכיב חסר מידע.
- [x] **TDD:** בדיקות פרמטריות חדשות ב-`test_cross_ref.py`/`test_apis.py` עבור `null` בכל שכבה במבנה (`data`/`supSearch`/`results`/`part`/`sellers`/`offers`/`prices`, וגם איברי `null` בודדים בתוך רשימות). 115 בדיקות עוברות, כיסוי כולל 94%.

## Phase 14: שיפורי UX (Nielsen Heuristics) לפני אריזת Desktop
- [x] **הודעת פתיחה + תבנית BOM להורדה:** `src/gui/ui_helpers.py::render_welcome_header()` (מודול UI ייעודי חדש, באותו דפוס פיצול כמו `table_rows.py`/`accessibility_widget.py`) - `st.info` המסביר בקצרה שהמערכת שולפת בזמן אמת מלאי/תמחור/מחזור חיים מ-Mouser/DigiKey/Octopart, ומציין שקובץ ה-BOM חייב לכלול עמודה בשם המדויק **MPN**; מיד מתחתיו `st.download_button` המציע תבנית CSV ריקה (`"MPN\n"` בלבד). מיישם "System Status Visibility" ו-"Error Prevention" (Nielsen) - מונע מראש את כשל `BomParser.parse_file` ("לא זוהתה עמודת MPN") לפני שהמשתמש בכלל מעלה קובץ. נקרא מתוך `app.py::main()` מיד אחרי `st.title`.
- [x] **הודעת טעינה מרכזית ומפורטת:** טקסט ה-`st.spinner` העוטף את `cached_analysis` (קריאה מקבילה לשלושת ה-APIs + בניית ה-DataFrame) עודכן מ"מעבד ומעשיר נתונים (זה לוקח רגע)..." להודעה מפורטת יותר: "טוען נתונים ושואב מידע מ-Mouser, DigiKey ו-Octopart, אנא המתן..." - מוצג באזור התוכן המרכזי (לא בפינה), במקום להסתמך על אינדיקטור הריצה הקטן של Streamlit בפינה.
- [x] **TDD:** `tests/unit/test_ui_helpers.py` - מוודא שהודעת הפתיחה מזכירה את שלושת הספקים ואת דרישת ה-MPN, ושכפתור ההורדה מציע בדיוק את תוכן התבנית הצפוי. אומת גם בפועל דרך `streamlit.testing.v1.AppTest` (ללא חריגות). 118 בדיקות עוברות, כיסוי כולל 94%.

## Phase 15: שדרוג טבלה מלא (st.dataframe טבעי, השוואת ספקים, RTL/טיפוגרפיה)
> ⚠️ **הוחלף ב-Phase 16:** הגישה המתוארת כאן (`st.dataframe` + `column_config`) הוחלפה בחזרה ל-`pandas.Styler` + `st.html` אחרי שנצפה בפועל (screenshot) שה-grid הפנימי של `st.dataframe` (glide-data-grid, מצויר על HTML canvas) שובר לחלוטין RTL עברי - טקסט לא קריא ולא מיושר. הפריטים למטה (מחזור חיים פעם אחת, מחיר/מלאי כמספרים גולמיים, "ספק מומלץ") **עדיין תקפים ולא השתנו** - רק שיטת הרינדור עצמה הוחלפה.
- [x] **מעבר ל-`st.dataframe` הטבעי (הוחלף ב-Phase 16):** ~~`table_render.py` נכתב מחדש - הוסרה לחלוטין גישת ה-iframe/`pandas.Styler.to_html` הקודמת, לטובת `st.dataframe` עם `column_config`~~.
- [x] **מחזור חיים/ציון סיכון פעם אחת בלבד (עדיין תקף):** הוסרו לחלוטין השדות `digikey_lifecycle`/`octopart_lifecycle` (מ-`digikey_api.py`/`octopart_api.py`) ועמודות "מחזור חיים (DigiKey/Octopart)" הכפולות מה-GUI - Mouser הוא המקור היחיד, מוצג פעם אחת בעמודות "סטטוס"/"ציון סיכון".
- [x] **מחיר/מלאי כמספרים גולמיים (עדיין תקף):** `MouserClient`/`DigiKeyClient`/`OctopartClient.parse_extra_fields` מחזירים `{vendor}_price_value`/`{vendor}_stock_qty` כ-`float`/`None` (לא מחרוזות "Mouser: 24,755 במלאי"). `extract_number()` חדש ב-`src/shared/translations.py` משותף לחילוץ מספר ממחרוזת מפורמטת של ספק (Mouser); DigiKey/Octopart כבר קיבלו את הערך הגולמי מה-API. `format_inventory()` הוסר (הפך ללא בשימוש).
- [x] **עמודות מחיר/מלאי מקובצות לפי ספק (עדיין תקף):** `table_rows.py::vendor_price_stock_columns()` בונה "מחיר (₪) - {ספק}"/"מלאי זמין - {ספק}" לכל אחד משלושת הספקים. **הערה טכנית שנותרה רלוונטית:** נבדק ואומת ש-`st.dataframe` (Streamlit 1.58) אינו תומך ב-`pandas.MultiIndex` עבור עמודות יחד עם `column_config` - קורס (`TypeError: keys must be str, int, float, bool or None, not tuple`). מאחר שעברנו בכל מקרה ל-`Styler`/HTML ב-Phase 16, המגבלה הזו כבר לא רלוונטית בפועל (HTML תומך בכותרות מקובצות אמיתיות דרך `colspan`, אך לא מומש - ראו "פריטים שנדחו" למטה).
- [x] **"ספק מומלץ" (עדיין תקף):** `table_rows.py::recommended_vendor()` (פונקציה טהורה, נבדקת) - מעדיף את הספק הזול ביותר מבין אלו שדיווחו מחיר; נופל בחזרה לספק עם המלאי הגבוה ביותר אם אף ספק לא דיווח מחיר; `None` (חוסר נתון) לעולם לא "מנצח" ערך אמיתי (כולל 0). עמודה ראשונה בטבלה.
- [x] **`st.column_config` (הוחלף ב-Phase 16):** ~~`ProgressColumn`/`NumberColumn`~~ - הוחלף בפורמט טקסט ידני (`_price_text`/`_stock_text`) בתוך `pandas.Styler`.
- [x] **RTL/טיפוגרפיה (עודכן שוב ב-Phase 16):** `RTL_CSS` ב-`app.py` הורחב - גופן נקי, הגדלת גודל גופן בסיסי (1.05rem), איסור italics. התברר בפועל ש-CSS גלובלי לא הספיק לתוך ה-grid של `st.dataframe` (ראו למעלה) - הפתרון הסופי הוא CSS ממוקד ב-`Styler.set_table_styles` (Phase 16).
- [x] **TDD:** עודכן לשדות המספריים החדשים ול-`recommended_vendor`; חלק מהבדיקות הותאמו שוב ב-Phase 16 עבור שיטת הרינדור החדשה.

## Phase 16: חזרה ל-pandas.Styler + st.html (תיקון RTL שנשבר ב-st.dataframe)
- [x] **`table_render.py` נכתב מחדש שוב:** `st.dataframe`/`column_config` הוסרו לחלוטין. כעת: `pandas.Styler` (`.hide(axis="index")`, `.format(formatter=..., escape="html")`, `.map()` לצביעת תא ציון הסיכון, `.set_table_styles()` ל-RTL/sticky header/טיפוגרפיה, `.set_table_attributes('role="table"')`) -> `.to_html()` -> `st.html()`. **לא** `st.iframe`/`st.components.v1.html` - `st.html` מזריק ישירות ל-DOM הראשי (לא iframe מבודד), כך שה-CSS של ה-Styler שולט לגמרי ברינדור וב-RTL, ללא תלות/התנגשות עם CSS גלובלי, ובלי בעיות ה-canvas-grid של `st.dataframe`.
- [x] **פורמוט ידני במקום `column_config`:** `_price_text()` (₪, שתי ספרות עשרוניות, מפריד אלפים) ו-`_stock_text()` (מפריד אלפים, ללא עשרוניות) מטפלים ב-`NaN`/`None` במפורש (`pd.isna`) ומחזירים "לא זמין"/"לא ידוע" - אומת אמפירית ש-`na_rep` של Styler (אם היה מוגדר) היה **עוקף** את הפונקציות המותאמות עבור תאי NaN, ולכן לא הוגדר `na_rep` כלל.
- [x] **אבטחה (XSS) בעדיפות גבוהה יותר, לא נמוכה:** מאחר שהטבלה מוזרקת כעת ל-DOM **הראשי** (לא ל-iframe מבודד כמו בעבר), `format(escape="html")` הוא קריטי יותר משהיה - ערך זדוני (למשל MPN עם `<script>`) יכול היה להשפיע על כל האפליקציה, לא רק על iframe מבודד. אומת אמפירית (לא רק בתיאוריה) עם `streamlit.testing.v1.AppTest` ומק"ט מכיל `<script>alert(1)</script>` בפועל - מוצג כ-`&lt;script&gt;...` בתגובת ה-HTML הסופית שנשלחת מהאפליקציה.
- [x] **`st.column_config.ProgressColumn`/`NumberColumn` שהוסרו:** ציון הסיכון חזר לצביעת רקע (אדום/צהוב/ירוק, חוק 60-30-10) במקום בר התקדמות; מחיר/מלאי מוצגים כטקסט מפורמט רגיל.
- [x] **TDD:** `tests/unit/test_table_render.py` (חדש) - בדיקות ישירות ל-`_price_text`/`_stock_text`/`_risk_color` (כולל `pd.NA`, לא רק `None`/`float('nan')`) - קודם לא היו מכוסות כלל כי כל `render_table` מסומן `pragma: no cover`. אומת קצה-לקצה עם `AppTest` (כולל תרחיש ה-XSS למעלה) - ללא חריגות. 136 בדיקות עוברות, כיסוי כולל 94%.

## פריטים שנדחו במכוון מעבר ל-MVP (Out of Scope, לא חוסמים סגירת שלב הפיתוח)
- **כיסוי בדיקות מעבר ל-85%:** הכיסוי הכולל עומד על כ-94% (מעל סף ה-85% הנדרש), עם 136 בדיקות עוברות. `cross_ref.py`/`sdk.py`/`gatekeeper.py`/`cli/main.py` אינם מכוסים ב-100% (מסלולי שגיאת רשת/CLI קיצוניים) - שיפור אפשרי לשלב תחזוקה עתידי, לא חוסם.
- **כותרות מקובצות אמיתיות (spanning headers עם `colspan`):** כעת אפשריות טכנית (HTML טהור, לא `st.dataframe`) אך לא מומשו ב-Phase 16 - לא התבקש; ניתן להוסיף בעתיד ל-`_TABLE_STYLES`/מבנה ה-HTML של `table_render.py` אם יידרש.

---
## סטטוס פרויקט: שלב הפיתוח הושלם (Development Phase Complete)
כל שלבי הפיתוח שהוגדרו במסמך זה (Phase 1 עד Phase 16) הושלמו ואומתו בבדיקות, כולל שלב הליטוש הסופי, אינטגרציית DigiKey ו-Octopart המלאות (כולל null-safety מלא מול תגובות GraphQL אמיתיות), תיקון תקלת ה-Retry הקריטית, שיפורי UX לפי היוריסטיקות של Nielsen, והשוואת שלושת הספקים side-by-side עם "ספק מומלץ". רינדור הטבלה עבר שני שינויים: Phase 15 ניסתה `st.dataframe`+`column_config` וגילתה בפועל (screenshot) שה-grid הפנימי (canvas) שובר RTL עברי; Phase 16 חזרה ל-`pandas.Styler` + `st.html` (לא iframe) - RTL/טיפוגרפיה נשלטים במלואם דרך CSS ממוקד של ה-Styler עצמו. המערכת כעת multi-provider אמיתית ומאומתת (Mouser + DigiKey + Octopart) כפי שתוכנן במקור ב-PRD סעיף 4.2, ומוכנה לשלב אריזת ה-Desktop הבא. אין פריטים פתוחים חוסמים; ההמשך (כיסוי 100%, כותרות מקובצות אמיתיות עם colspan אם יידרש בעתיד) מנוהל כתחזוקה שוטפת, בכפוף לאותה מתודולוגיית עבודה (PRD → PLAN → TODO → קוד) המתוארת ב-`docs/CLAUDE.md`.