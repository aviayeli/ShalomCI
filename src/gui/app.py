import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

# הגדרת נתיב השורש לפרויקט
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.cross_ref import NETWORK_ERROR_STATUS
from src.gui.accessibility_widget import inject_accessibility_widget
from src.gui.table_controls import available_statuses, filter_and_sort, sort_options
from src.gui.table_render import render_table
from src.gui.table_rows import build_rows
from src.gui.ui_helpers import render_welcome_header
from src.sdk import ShalomCI_SDK

RISK_SCORE_HELP = (
    "This score represents the overall supply chain and obsolescence risk of the BOM. "
    "It is calculated by factoring in the Lifecycle Status (e.g., EOL, NRND), current "
    "stock availability, and lead times across all components."
)

# CSS גלובלי (RTL ורקע בלבד) - עיצוב הטבלה עבר ל-iframe מבודד ב-render_table, ראו שם למה.
RTL_CSS = """
<style>
    * { direction: rtl !important; text-align: right !important; font-family: 'Segoe UI', sans-serif; }
    .stApp { background-color: #F8F9FA; }
</style>
"""


async def run_analysis(file_path: str, filename: str):
    sdk = ShalomCI_SDK()
    await sdk.initialize()

    try:
        bom_data = await sdk.process_bom(file_path)
        await sdk.enrich_components(bom_data)
        eval_result = await sdk.evaluate_risks(bom_data)
        final_data = await sdk.find_mitigations(eval_result["components"], project_name=filename)
        return eval_result["project_score"], final_data
    finally:
        await sdk.close()


@st.cache_data(show_spinner=False)
def cached_analysis(file_bytes: bytes, filename: str):  # pragma: no cover - חיווט Streamlit/asyncio (Proxy); run_analysis נבדק ישירות
    """עוטף את run_analysis במטמון (keyed לפי hash תוכן+שם) - בלי זה, כל rerun של Streamlit
    היה מפעיל שוב את כל העשרת ה-Mouser API ועלול לגרום לחסימת קצב."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        return asyncio.run(run_analysis(tmp_path, filename))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def main():  # pragma: no cover - חיווט Streamlit בלבד (Proxy); הלוגיקה הטהורה נבדקת ב-table_rows/run_analysis
    st.set_page_config(page_title="ShalomCI", layout="wide")
    st.markdown(RTL_CSS, unsafe_allow_html=True)
    inject_accessibility_widget()
    st.title("⚙️ ShalomCI - אינטליגנציית רכיבים")
    render_welcome_header()

    uploaded_file = st.file_uploader("העלה עץ מוצר (BOM)", type=["xlsx", "csv"])
    col_run, col_download = st.columns(2)

    if col_run.button("🚀 הפעל ניתוח", disabled=not uploaded_file):
        with st.spinner("טוען נתונים ושואב מידע מ-Mouser, DigiKey ו-Octopart, אנא המתן..."):
            try:
                st.session_state["result"] = cached_analysis(uploaded_file.getvalue(), uploaded_file.name)
            except Exception as e:
                st.session_state.pop("result", None)
                st.error(f"שגיאה בתהליך: {e}. וודא שמפתחות ה-API תקינים ב-env.")

    if "result" not in st.session_state:
        return
    score, data = st.session_state["result"]

    # אם ה-Gatekeeper מיצה את כל ה-Retry-ים מול Mouser, נחשוף זאת במפורש ולא נציג בשקט N/A/❓
    if any(c.get("manufacturer") == NETWORK_ERROR_STATUS for c in data):
        st.warning(
            "⚠️ שגיאת רשת בפנייה ל-Mouser API (לאחר מספר ניסיונות חוזרים). "
            "מוצגים נתוני ברירת מחדל עבור חלק מהרכיבים - נסו שוב מאוחר יותר."
        )

    df = pd.DataFrame(build_rows(data))

    st.subheader("🔍 סינון ומיון")
    col_search, col_status, col_sort, col_order = st.columns([2, 2, 2, 1])
    search = col_search.text_input("חיפוש (מק\"ט / יצרן)")
    statuses = col_status.multiselect("סטטוס מחזור חיים", options=available_statuses(df))
    sort_by = col_sort.selectbox("מיין לפי", options=sort_options(df))
    ascending = col_order.radio("סדר", options=["עולה", "יורד"]) == "עולה"
    df = filter_and_sort(df, search, statuses, sort_by, ascending)

    # utf-8-sig מוסיף BOM כך ש-Excel יזהה נכון קידוד עברי בפתיחת קובץ ה-CSV
    col_download.download_button(
        "הורד דוח", data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="shalomci_report.csv", mime="text/csv"
    )
    st.metric("ציון סיכון כללי (Risk Score)", f"{score} / 5.0", help=RISK_SCORE_HELP)
    render_table(df)


if __name__ == "__main__":
    main()
