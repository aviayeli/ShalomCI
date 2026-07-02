# ShalomCI

**Shalom Component Intelligence** — מערכת ניהול מחזור חיי רכיבים אלקטרוניים (Electronic Component Lifecycle Management) פרואקטיבית. קולטת עצי מוצר (BOM), מתשאלת ספקי רכיבים (Mouser כרגע; Octopart/DigiKey בשלב עתידי), מדרגת סיכון EOL/NRND/LTB לכל רכיב ולפרויקט כולו, ומאתרת חלופות ו/או פותחת "תיק טיפול" הנדסי אוטומטית.

מסמכי הארכיטקטורה המלאים: [`docs/PRD.md`](docs/PRD.md), [`docs/PLAN.md`](docs/PLAN.md), [`docs/TODO.md`](docs/TODO.md), חוקת הפרויקט: [`docs/CLAUDE.md`](docs/CLAUDE.md).

## 👨‍💻 קרדיטים (Credits)

💡 פרויקט זה תוכנן ע"י שלום יפרח, ופותח ונוצר ע"י אבי איילי. (Planned by Shalom Yfrah. Developed and created by Avi Ayeli.)

## דרישות מוקדמות (Ubuntu / Linux)

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) — מנהל הסביבה והחבילות היחיד בפרויקט. אין להשתמש ב-`pip install` ישירות ואין להסתמך על `requirements.txt`.

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

`uv sync` בונה `.venv` מקומי תואם-מערכת מתוך `pyproject.toml`/`uv.lock` ומתקין את כל התלויות (כולל תלויות הפיתוח: pytest, ruff).

## סודות ומפתחות API

```bash
cp .env-example .env
```

ערכו את `.env` והזינו את `MOUSER_API_KEY` שלכם (Nexar/DigiKey שמורים לשלב עתידי — הקליינטים שלהם עדיין stubs). ה-SDK טוען את הקובץ אוטומטית באמצעות `python-dotenv`; ללא מפתח, המערכת פשוט תחזיר נתוני N/A במקום נתונים אמיתיים, ולא תיכשל.

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

## בדיקות ואיכות קוד

```bash
uv run pytest          # מריץ את כל הבדיקות + דוח כיסוי (סף מינימלי: 85%)
uv run ruff check .    # לינטינג לפי תקן הפרויקט
```

## מבנה הפרויקט

ראו את עץ התיקיות המלא ב-[`docs/PLAN.md`](docs/PLAN.md). בקצרה: `src/sdk.py` הוא נקודת הכניסה היחידה ללוגיקה העסקית; `src/cli/` ו-`src/gui/` הן שכבות תצוגה (Proxy) בלבד; `src/services/` מכיל את ה-API Gatekeeper ואת קליינטי הספקים; `src/core/` מכיל את מנוע ה-BOM, מנוע הסיכון, מנוע החלופות ומחולל הדוחות; `src/data/` מנהל את `cases.db` המקומי (SQLite).
