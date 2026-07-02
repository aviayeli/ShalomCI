import re

import pandas as pd

# עמודות שניתן למיין לפיהן בסרגל הכלים; המפתח = שם העמודה כפי שמופיע ב-DataFrame
SORT_OPTIONS = ["מק\"ט", "ציון סיכון", "מחיר ליחידה", "זמן אספקה"]

# עמודות מפורמטות כטקסט (למשל "₪1.85" או "זמן אספקה: 63 ימים") שדורשות שליפת מספר למיון נכון
_NUMERIC_TEXT_COLUMNS = {"מחיר ליחידה", "זמן אספקה"}
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


def available_statuses(df: pd.DataFrame) -> list:
    """מחזיר רשימת סטטוסי מחזור חיים ייחודיים (ללא אייקון הנגישות) לתפריט הסינון."""
    return sorted({str(status).split(" ", 1)[-1] for status in df["סטטוס"]})


def filter_and_sort(df: pd.DataFrame, search: str, statuses: list, sort_by: str, ascending: bool) -> pd.DataFrame:
    """מסנן וממיין את טבלת הרכיבים המועשרת לפני הרינדור (לוגיקת Pandas טהורה, ניתנת לבדיקה)."""
    result = df

    if search:
        query = search.strip()
        mask = (
            result["מק\"ט"].astype(str).str.contains(query, case=False, na=False)
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
