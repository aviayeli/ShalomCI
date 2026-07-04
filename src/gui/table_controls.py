import re

import pandas as pd

from src.gui.table_rows import MPN_COLUMN

# עמודות מפורמטות כטקסט (למשל "זמן אספקה: 63 ימים") שדורשות שליפת מספר למיון נכון - עמודות
# המחיר/מלאי כבר מספריות (float, ראו table_rows.py) וממוינות נכון באופן טבעי ללא צורך בכך.
_NUMERIC_TEXT_COLUMNS = {"אספקה - Mouser", "אספקה - DigiKey", "אספקה - Octopart"}
_NUMBER_RE = re.compile(r"[\d.,]+")


def _extract_number(value) -> float:
    """שולף את הערך המספרי הראשון ממחרוזת מפורמטת; ערך לא ידוע/לא זמין הופך ל-NaN כדי ש-
    sort_values (עם na_position='last' כברירת מחדל) ידחוף אותו לסוף בשני כיווני המיון."""
    match = _NUMBER_RE.search(str(value))
    if not match:
        return float("nan")
    try:
        return float(match.group().replace(",", ""))
    except ValueError:
        return float("nan")


def sort_options(df: pd.DataFrame) -> list:
    """מחזיר את כל עמודות ה-DataFrame הנוכחי כאפשרויות מיון, כך שעמודה חדשה תופיע בסרגל הכלים אוטומטית."""
    return list(df.columns)


def available_statuses(df: pd.DataFrame) -> list:
    """מחזיר רשימת סטטוסי מחזור חיים ייחודיים (ללא אייקון הנגישות) לתפריט הסינון."""
    return sorted({str(status).split(" ", 1)[-1] for status in df["סטטוס"]})


def filter_and_sort(df: pd.DataFrame, search: str, statuses: list, sort_by: str, ascending: bool) -> pd.DataFrame:
    """מסנן וממיין את טבלת הרכיבים המועשרת לפני הרינדור (לוגיקת Pandas טהורה, ניתנת לבדיקה)."""
    result = df

    if search:
        query = search.strip()
        mask = (
            result[MPN_COLUMN].astype(str).str.contains(query, case=False, na=False)
            | result["יצרן"].astype(str).str.contains(query, case=False, na=False)
        )
        result = result[mask]

    if statuses:
        status_mask = result["סטטוס"].apply(lambda s: str(s).split(" ", 1)[-1] in statuses)
        result = result[status_mask]

    if sort_by:
        if sort_by in _NUMERIC_TEXT_COLUMNS:
            result = (result.assign(_sort_key=result[sort_by].map(_extract_number))
                      .sort_values("_sort_key", ascending=ascending)
                      .drop(columns="_sort_key"))
        else:
            result = result.sort_values(by=sort_by, ascending=ascending)

    return result
