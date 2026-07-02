import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# הגדרת נתיב השורש לפרויקט
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.cross_ref import NETWORK_ERROR_STATUS
from src.sdk import ShalomCI_SDK

# אייקוני נגישות (WCAG 2.2) - ההתראה על סטטוס לא מסתמכת על צבע בלבד; אותם ספים כמו צביעת התאים.
STATUS_ICONS = {1: "⛔", 2: "⚠️", 3: "⚠️", 4: "✅", 5: "✅"}


def status_icon(risk_score: int) -> str:
    """מחזיר אייקון נגישות התואם לרמת הסיכון; ציון לא ידוע (0) מסומן לבדיקה ידנית."""
    return STATUS_ICONS.get(risk_score, "❓")

# CSS גלובלי (RTL ורקע בלבד) - עיצוב הטבלה עבר ל-iframe מבודד ב-render_table, ראו שם למה.
RTL_CSS = """
<style>
    * { direction: rtl !important; text-align: right !important; font-family: 'Segoe UI', sans-serif; }
    .stApp { background-color: #F8F9FA; }
</style>
"""


def build_rows(components: list) -> list:
    """בונה את שורות טבלת התצוגה מתוך נתוני הרכיבים המועשרים (פונקציה טהורה, ניתנת לבדיקה)."""
    rows = []
    for c in components:
        score = c.get("risk_score", 0)
        rows.append({
            "מק\"ט": c.get("mpn", "N/A"),
            "יצרן": c.get("manufacturer", "N/A"),
            "סטטוס": f"{status_icon(score)} {c.get('lifecycle_status', 'N/A')}",
            "ציון סיכון": score,
            "מלאי": c.get("inventory", "לא ידוע"),
            "זמן אספקה": c.get("lead_time", "זמן אספקה: לא ידוע"),
            "מחיר ליחידה": c.get("price_per_unit", "לא זמין"),
            "חלופה מוצעת (Mouser)": c.get("suggested_replacement", "אין"),
            "תאימות RoHS": c.get("rohs_status", "לא ידוע"),
            "צורת אריזה": c.get("packaging", "לא ידוע"),
            "חלופות": ", ".join([a.get("mpn", "") for a in c.get("alternatives", [])]) if c.get(
                "alternatives") else "אין"
        })
    return rows


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


TABLE_CSS = """
body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
.risk-table { width: 100%; border-collapse: collapse; }
.risk-table thead th { position: sticky !important; top: 0 !important; background-color: #0056B3 !important;
    color: white !important; z-index: 1000 !important; padding: 10px; box-shadow: 0 2px 2px -1px rgba(0,0,0,0.4); }
.risk-table th, .risk-table td { border: 1px solid #ddd; padding: 8px; text-align: right; }
"""


def render_table(df: pd.DataFrame):  # pragma: no cover - חיווט Streamlit בלבד (Proxy)
    # iframe מבודד (components.html) עוקף את סינון aria-/role של DOMPurify ב-st.markdown ואת
    # התנגשות ה-CSS הגלובלי עם sticky header. format(escape="html") חובה: components.html מריץ
    # HTML/JS גולמי בלי sanitization, והערכים מגיעים מ-Mouser API/BOM שהועלה - מקורות לא מהימנים.
    html_table = df.style.hide(axis="index").format(escape="html").map(
        lambda val: 'background-color: #FFCCCC' if val == 1 else (
            'background-color: #FFFFCC' if val in [2, 3] else 'background-color: #CCFFCC'),
        subset=['ציון סיכון']
    ).to_html(table_attributes='class="risk-table" role="table"').replace("<th ", '<th scope="col" ')

    full_html = (f'<!DOCTYPE html><html dir="rtl" lang="he"><head><style>{TABLE_CSS}</style></head>'
                 f'<body><div role="region" aria-label="טבלת נתוני רכיבים מועשרים" tabindex="0">'
                 f'{html_table}</div></body></html>')
    components.html(full_html, height=600, scrolling=True)


def main():  # pragma: no cover - חיווט Streamlit בלבד (Proxy); הלוגיקה הטהורה נבדקת ב-status_icon/build_rows/run_analysis
    st.set_page_config(page_title="ShalomCI", layout="wide")
    st.markdown(RTL_CSS, unsafe_allow_html=True)
    st.title("⚙️ ShalomCI - אינטליגנציית רכיבים")

    uploaded_file = st.file_uploader("העלה עץ מוצר (BOM)", type=["xlsx", "csv"])
    col_run, col_download = st.columns(2)

    if col_run.button("🚀 הפעל ניתוח", disabled=not uploaded_file):
        with st.spinner("מעבד ומעשיר נתונים (זה לוקח רגע)..."):
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
    # utf-8-sig מוסיף BOM כך ש-Excel יזהה נכון קידוד עברי בפתיחת קובץ ה-CSV
    col_download.download_button(
        "הורד דוח", data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="shalomci_report.csv", mime="text/csv"
    )
    st.metric("ציון בריאות", f"{score} / 5.0")
    render_table(df)


if __name__ == "__main__":
    main()
