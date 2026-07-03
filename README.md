# ShalomCI

**Shalom Component Intelligence** — מערכת ניהול מחזור חיי רכיבים אלקטרוניים (Electronic Component Lifecycle Management) פרואקטיבית, התואמת לתקן הבינלאומי **IEC 62402:2019**. קולטת עצי מוצר (BOM), מתשאלת שלושה ספקי רכיבים מחוברים בפועל (Mouser, DigiKey, Octopart/Nexar), מדרגת סיכון EOL/NRND/LTB/Allocation לכל רכיב, מאתרת חלופות פונקציונליות (FFF) דרך Octopart, ופותחת "תיק טיפול" הנדסי אוטומטית כשלא נמצאה חלופה.

מסמכי הארכיטקטורה המלאים: [`docs/PRD.md`](docs/PRD.md) (דרישות מוצר), [`docs/PLAN.md`](docs/PLAN.md) (ארכיטקטורה), [`docs/TODO.md`](docs/TODO.md) (סטטוס פיתוח), חוקת הפרויקט: [`docs/CLAUDE.md`](docs/CLAUDE.md).

## תכונות עיקריות (Features)

- **קליטת BOM חכמה:** העלאת עצי מוצר בפורמט Excel/CSV עם זיהוי אוטומטי של עמודות מק"ט (MPN) ויצרן. הודעת פתיחה בראש המסך מסבירה זאת ומציעה תבנית CSV ריקה (עמודת MPN בלבד) להורדה, כדי למנוע מראש כשל זיהוי עמודות.
- **דירוג סיכון 1-5:** ציון סיכון לכל רכיב (NRND/LTB/EOL/Allocation), מוצג עם אייקון נגישות מפורש (⛔/⚠️/✅) כך שההתראה לא מסתמכת על צבע בלבד (WCAG 2.2).
- **ציון סיכון כללי (Risk Score):** מדד מצטבר לכל ה-BOM, מוצג באופן בולט מעל טבלת הרכיבים עם הסבר (tooltip) המפרט שהוא משוקלל מתוך סטטוס מחזור החיים, זמינות המלאי וזמני האספקה - כדי לאפשר למשתמש שאינו טכני להעריך במבט אחד את רמת הסיכון הכוללת.
- **מנוע חלופות קרוס-רפרנס (FFF):** איתור אוטומטי של חלופות תואמות (Form, Fit, Function) לרכיבים מסוכנים דרך Octopart/Nexar, כולל דירוג זמינות ומחיר.
- **העשרת נתונים משלושה ספקים (Mouser + DigiKey + Octopart):** מלאי, זמן אספקה ומחיר נשלפים בנפרד מכל ספק ומוצגים side-by-side בעמודות נפרדות בטבלה, כדי לאפשר השוואה בין ספקים על אותו רכיב. מחזור חיים וציון סיכון מוצגים פעם אחת בלבד (Mouser, מקור יחיד) כדי למנוע כפילות מבלבלת.
- **ניהול מקרים (Case Management):** כשלא נמצאת חלופה לרכיב Obsolete, נפתח אוטומטית "תיק טיפול" מקומי (SQLite, `cases.db`) למעקב הנדסי.
- **סרגל סינון ומיון:** חיפוש חופשי, סינון לפי סטטוס מחזור חיים, ומיון דינמי לפי כל עמודה בטבלה (כולל מיון נכון של עמודות טקסט מפורמטות כמו מחיר או זמן אספקה).
- **ייצוא דוח Excel:** דוח `.xlsx` מעוצב וצבעוני עם כל הנתונים, הציונים והחלופות.
- **ממשקים כפולים:** CLI לעיבוד אצווה (batch) ו-GUI גרפי (Streamlit) בעברית מלאה עם יישור RTL.
- **חבילת Desktop ל-Windows:** אריזה כקובץ הפעלה עצמאי (`.exe`) למשתמש קצה שאינו טכני, ללא צורך בהתקנת Python.

## ארכיטקטורה בקצרה

- **שכבת SDK מרכזית (`src/sdk.py`):** נקודת הכניסה היחידה לכל הלוגיקה העסקית. ה-CLI וה-GUI הם שכבות תצוגה (Proxy) בלבד וללא לוגיקה עצמאית משלהם.
- **API Gatekeeper (`src/services/gatekeeper.py`):** כל קריאה חיצונית (Mouser/Octopart/DigiKey) עוברת דרך שומר סף מרכזי המנהל תורים אסינכרוניים, מגבלות קצב (Token Bucket, לדוגמה עד 30 בקשות/דקה מול Mouser) ומנגנון Retries חכם עם Exponential Backoff — כדי למנוע חסימות (429) מצד הספקים. אין קריאות רשת ישירות עוקפות בשום מקום בקוד.
- **טבלת השוואת ספקים ב-`st.dataframe` הטבעי:** `src/gui/table_render.py` מרנדר באמצעות `st.dataframe` + `column_config` (`ProgressColumn`/`NumberColumn`) - במתכוון **לא** `st_aggrid` או רכיב JS חיצוני אחר, כדי להימנע מ-timeouts ב-WebSocket וכשלי רינדור iframe. עמודות מחיר/מלאי מוצגות בנפרד לכל אחד משלושת הספקים (Mouser/DigiKey/Octopart), עם עמודת "ספק מומלץ" ראשונה המחשבת אוטומטית את הספק הזול/הזמין ביותר. מחזור חיים וציון סיכון מוצגים פעם אחת בלבד (מקור: Mouser).
- לפירוט מלא (כולל שכבת ה-Gatekeeper, ניהול המקרים, ותקן IEC 62402:2019) ראו [`docs/PLAN.md`](docs/PLAN.md) ו-[`docs/PRD.md`](docs/PRD.md).

## דרישות מוקדמות (Ubuntu / Linux / Windows)

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) — מנהל הסביבה והחבילות **היחיד** בפרויקט.

> ⚠️ **`pip` אסור בהחלט בפרויקט זה.** אין להריץ `pip install` בשום שלב, ואין להסתמך על `requirements.txt`. כל ניהול התלויות (כולל הוספת חבילות חדשות) מתבצע אך ורק דרך `uv` (`uv add`, `uv sync`, `uv lock`) מול `pyproject.toml`/`uv.lock`.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

> **חשוב — קובץ `.venv` הוא ספציפי-פלטפורמה:** אל תעתיקו/תסנכרנו תיקיית `.venv` בין Windows ל-Linux (או להפך). Windows יוצר `.venv/Scripts/*.exe` ללא תיקיית `bin/` הנדרשת ב-Linux, ולכן `uv run` פשוט לא יצליח להריץ כלום. `.venv` כבר מוחרג ב-`.gitignore` — כל מכונה (או container) צריכה לבנות משלה עם `uv sync` (ראו למטה).

## התקנה

```bash
git clone <repo-url> ShalomCI
cd ShalomCI
uv sync
```

`uv sync` בונה `.venv` מקומי תואם-מערכת מתוך `pyproject.toml`/`uv.lock` ומתקין את כל התלויות (כולל תלויות הפיתוח: pytest, ruff, pyinstaller) — **לא** דרך `pip`.

## סודות ומפתחות API

```bash
cp .env-example .env
```

ערכו את `.env` והזינו את `MOUSER_API_KEY` שלכם, את `DIGIKEY_CLIENT_ID`/`DIGIKEY_CLIENT_SECRET` (מ-DigiKey API Console, אפליקציית "Product Information V4" + "SupplyChain"), ואת `OCTOPART_CLIENT_ID`/`OCTOPART_CLIENT_SECRET` (מ-Nexar Developer Portal - Octopart פועל כיום תחת Nexar) להפעלת ההעשרה המלאה משלושת הספקים. ה-SDK טוען את הקובץ אוטומטית באמצעות `python-dotenv`; ללא מפתחות לספק מסוים, המערכת פשוט תחזיר נתוני N/A/ברירת מחדל במקום נתונים אמיתיים לאותו ספק בלבד, ולא תיכשל. **לעולם אל תעלו את `.env` עצמו ל-Git** — הוא מוחרג ב-`.gitignore`; `.env-example` הוא התבנית הציבורית הנקייה.

## הרצה

כל הפקודות רצות דרך `uv run` — אין צורך להפעיל (`activate`) את הסביבה הווירטואלית ידנית.

**CLI — עיבוד BOM והפקת דוח:**

```bash
uv run python -m src.cli.main process TestData.xlsx
```

**CLI — רשימת תיקי טיפול פתוחים:**

```bash
uv run python -m src.cli.main cases list
```

**GUI — ממשק Streamlit (עברית, RTL):**

```bash
uv run streamlit run src/gui/app.py
```

הממשק ייפתח בדפדפן בכתובת `http://localhost:8501`.

## חבילת Desktop ל-Windows (PyInstaller)

לבניית קובץ הפעלה עצמאי (`.exe`) למשתמש קצה שאינו טכני — יש להריץ **על מחשב Windows בפועל** (PyInstaller אינו תומך ב-Cross-Compilation):

```bash
uv run python build.py
```

הפקודה יוצרת תיקיית `dist/ShalomCI/` הכוללת את `ShalomCI.exe` וכל הקבצים הנלווים (מצב `--onedir`, ללא חלון קונסולה). לפני ההרצה יש להעתיק את `.env` שלכם (ראו לעיל) אל תוך `dist/ShalomCI/`, לצד קובץ ה-`.exe` — הוא נטען יחסית לתיקיית ההרצה ואינו נארז בתוך הקובץ המהודר. הפעלת `ShalomCI.exe` תפתח את הדפדפן אוטומטית מול פורט פנוי מקומי.

## בדיקות ואיכות קוד

```bash
uv run pytest          # מריץ את כל הבדיקות + דוח כיסוי (סף מינימלי: 85%)
uv run ruff check .    # לינטינג לפי תקן הפרויקט
```

## מבנה הפרויקט

ראו את עץ התיקיות המלא ב-[`docs/PLAN.md`](docs/PLAN.md). בקצרה: `src/sdk.py` הוא נקודת הכניסה היחידה ללוגיקה העסקית; `src/cli/` ו-`src/gui/` הן שכבות תצוגה (Proxy) בלבד; `src/services/` מכיל את ה-API Gatekeeper ואת קליינטי הספקים; `src/core/` מכיל את מנוע ה-BOM, מנוע הסיכון, מנוע החלופות ומחולל הדוחות; `src/data/` מנהל את `cases.db` המקומי (SQLite); `src/shared/` מכיל את שכבת התרגום העברית המרכזית; `run_desktop.py`/`build.py` הם שכבת אריזת ה-Desktop.

## 👨‍💻 קרדיטים (Credits)

💡 פרויקט זה תוכנן ע"י שלום יפרח, ופותח ונוצר ע"י אבי איילי. (Planned by Shalom Yfrah. Developed and created by Avi Ayeli.)

## Contact / Author

**אבי איילי (Avi Ayeli)** — avi.ayeli@gmail.com
