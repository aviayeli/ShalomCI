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

from src.sdk import ShalomCI_SDK

# אייקוני נגישות (WCAG 2.2) - ההתראה על סטטוס לא מסתמכת על צבע בלבד, תמיד מלווה בטקסט ובאייקון מפורש.
# משתמשים באותם ספי ציון סיכון כמו צביעת התאים, כדי שהאייקון תמיד יתאם לצבע ולא יסתור אותו.
STATUS_ICONS = {1: "⛔", 2: "⚠️", 3: "⚠️", 4: "✅", 5: "✅"}


def status_icon(risk_score: int) -> str:
    """מחזיר אייקון נגישות התואם לרמת הסיכון; ציון לא ידוע (0) מסומן לבדיקה ידנית."""
    return STATUS_ICONS.get(risk_score, "❓")

# CSS מעודכן לתמיכה בטבלה מעוצבת
RTL_CSS = """
<style>
    * { direction: rtl !important; text-align: right !important; font-family: 'Segoe UI', sans-serif; }
    .stApp { background-color: #F8F9FA; }
    /* direction מוגדר במפורש ברמת הבלוק של הטבלה (ולא רק דרך ה-* הכללי) כדי להבטיח
       שסדר העמודות וזרימת התוכן יהיו נכונים גם כשהדפדפן מרנדר טבלה כרכיב עצמאי */
    .risk-table { direction: rtl; width: 100%; border-collapse: collapse; background-color: white; border: 1px solid #ddd; }
    .risk-table th { background-color: #0056B3; color: white; padding: 12px; text-align: right; }
    /* unicode-bidi: isolate מבודד ערכים לועזיים (כגון מק"טים באנגלית) בתוך תא עברי
       כך שהם יזרמו משמאל-לימין בתוך התא מבלי לשבש את כיוון הטקסט הכללי או את מיקום המקפים */
    .risk-table td { padding: 10px; border: 1px solid #ddd; text-align: right; unicode-bidi: isolate; }
    /* עיצוב צבעים */
    .critical { background-color: #FFCCCC !important; font-weight: bold; }
    .warning { background-color: #FFFFCC !important; font-weight: bold; }
    .healthy { background-color: #CCFFCC !important; font-weight: bold; }
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

        # מחזירים רק את הציון ואת הנתונים!
        return eval_result["project_score"], final_data
    finally:
        await sdk.close()


def main():  # pragma: no cover - חיווט Streamlit בלבד (Proxy); הלוגיקה הטהורה נבדקת ב-status_icon/build_rows/run_analysis
    st.set_page_config(page_title="ShalomCI", layout="wide")
    st.markdown(RTL_CSS, unsafe_allow_html=True)
    st.title("⚙️ ShalomCI - אינטליגנציית רכיבים")

    uploaded_file = st.file_uploader("העלה עץ מוצר (BOM)", type=["xlsx", "csv"])

    if uploaded_file and st.button("🚀 הפעל ניתוח"):
        with st.spinner("מעבד ומעשיר נתונים (זה לוקח רגע)..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            try:
                # וודא שזה מה שכתוב אצלך:
                score, data = asyncio.run(run_analysis(tmp_path, uploaded_file.name))
                st.metric("ציון בריאות", f"{score} / 5.0")

                df = pd.DataFrame(build_rows(data))

                # רינדור הטבלה כ-HTML
                # נשתמש ב-DataFrame.style כדי להחיל עיצוב
                html_table = df.style.map(
                    lambda val: 'background-color: #FFCCCC' if val == 1 else (
                        'background-color: #FFFFCC' if val in [2, 3] else 'background-color: #CCFFCC'),
                    subset=['ציון סיכון']
                ).to_html(classes="risk-table", index=False)

                st.markdown(html_table, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"שגיאה בתהליך: {e}. וודא שמפתחות ה-API תקינים ב-env.")
            finally:
                if os.path.exists(tmp_path): os.remove(tmp_path)


if __name__ == "__main__":
    main()
