import pandas as pd
import streamlit as st

from src.gui.table_rows import PRICE_COLUMN_PREFIX, PRICE_STOCK_VENDORS, STOCK_COLUMN_PREFIX

# תקרה סבירה להצגת "מלאי זמין" כ-ProgressColumn (בר התקדמות) - כמות מעל התקרה עדיין
# מוצגת כבר מלא, לא נחתכת; זהו רק קנה-מידה חזותי, לא הגבלה על הנתון עצמו.
_MAX_STOCK_FOR_PROGRESS_BAR = 10_000


def _build_column_config() -> dict:
    """מגדיר עיצוב עמודות (ProgressColumn לציון סיכון/מלאי, NumberColumn למחיר בש"ח)."""
    config = {
        "ציון סיכון": st.column_config.ProgressColumn(
            "ציון סיכון", help="1 = סיכון קריטי, 5 = תקין (Mouser)", min_value=0, max_value=5, format="%d"
        ),
    }
    for label in PRICE_STOCK_VENDORS:
        config[f"{PRICE_COLUMN_PREFIX}{label}"] = st.column_config.NumberColumn(
            label, help=f"מחיר ליחידה - {label}", format="₪ %.2f"
        )
        config[f"{STOCK_COLUMN_PREFIX}{label}"] = st.column_config.ProgressColumn(
            label, help=f"מלאי זמין - {label}", min_value=0, max_value=_MAX_STOCK_FOR_PROGRESS_BAR, format="%d"
        )
    return config


def render_table(df: pd.DataFrame) -> None:  # pragma: no cover - חיווט Streamlit בלבד (Proxy)
    """
    מרנדר את טבלת הרכיבים באמצעות st.dataframe הטבעי (לא iframe/רכיב צד-שלישי כמו
    st_aggrid) - נמנע מ-timeouts ב-WebSocket וכשלי רינדור iframe שנצפו בעבר, ותומך
    ב-sticky header ונגישות (ARIA) מובנים ללא צורך בפתרונות עוקפים.
    """
    numeric_columns = [
        f"{prefix}{label}"
        for prefix in (PRICE_COLUMN_PREFIX, STOCK_COLUMN_PREFIX)
        for label in PRICE_STOCK_VENDORS
    ]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    st.dataframe(
        df,
        hide_index=True,
        height=600,
        column_config=_build_column_config(),
    )
