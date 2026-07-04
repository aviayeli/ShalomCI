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

from src.core.cross_ref import NETWORK_ERROR_STATUS, RATE_LIMIT_STATUS
from src.gui.accessibility_widget import inject_accessibility_widget
from src.gui.disclaimers import render_disclaimers, render_footer
from src.gui.table_controls import available_statuses, filter_and_sort, sort_options
from src.gui.table_rows import build_rows, summarize_risk
from src.gui.table_view import render_table_view
from src.gui.styles import DESIGN_CSS, RTL_CSS
from src.gui.ui_helpers import (
    api_keys_fingerprint,
    render_api_keys_sidebar,
    render_summary_metrics,
    render_welcome_header,
)
from src.sdk import ShalomCI_SDK


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
def cached_analysis(file_bytes: bytes, filename: str, keys_fingerprint: str):  # pragma: no cover - חיווט Streamlit/asyncio (Proxy); run_analysis נבדק ישירות
    """עוטף את run_analysis במטמון (keyed לפי hash תוכן+שם) - בלי זה, כל rerun של Streamlit
    היה מפעיל שוב את כל העשרת ה-Mouser API ועלול לגרום לחסימת קצב.
    keys_fingerprint הוא חלק ממפתח המטמון בלבד (אינו בשימוש בגוף) - שינוי מפתחות ה-API משנה
    אותו וכך מאפשר תוצאה חדשה, מבלי לאחסן את המפתחות הגולמיים במפתח המטמון."""
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
    # DESIGN_CSS אחרי RTL_CSS בכוונה: באותה ספציפיות, הגיליון המאוחר גובר (רקע .stApp, טוקנים).
    st.markdown(DESIGN_CSS, unsafe_allow_html=True)
    inject_accessibility_widget()
    render_api_keys_sidebar()
    st.title("⚙️ ShalomCI — אינטליגנציית רכיבים")
    st.caption("ניהול מחזור חיי רכיבים אלקטרוניים · השוואת מלאי, תמחור וסיכון אספקה בזמן אמת")
    # ההסבר מתקפל: פתוח בכניסה הראשונה, מכווץ אוטומטית לאחר שיש תוצאות.
    render_welcome_header("result" not in st.session_state)
    # גילויי נאות (מגבלות API ותנאי שימוש) - expander מכווץ מיד מתחת להסבר הראשי.
    render_disclaimers()

    # תווית מפורשת אחת מעל הווידג'ט + label_visibility="collapsed": כך תווית הווידג'ט
    # המובנית אינה יכולה לשכפל את הכיתוב, ונשארת כותרת עברית יחידה וברורה.
    st.markdown("**העלה קובץ עץ מוצר (BOM)**")
    uploaded_file = st.file_uploader(
        "העלה קובץ עץ מוצר (BOM)", type=["xlsx", "csv"], label_visibility="collapsed",
        help="פורמטים נתמכים: Excel‏ (xlsx) או CSV. הקובץ חייב לכלול עמודה בשם MPN.",
    )

    if st.button("🚀 הפעל ניתוח", disabled=not uploaded_file):
        with st.spinner("מנתח את עץ המוצר ושואב נתונים מ-Mouser, DigiKey ו-Octopart, אנא המתן…"):
            try:
                st.session_state["result"] = cached_analysis(
                    uploaded_file.getvalue(), uploaded_file.name, api_keys_fingerprint()
                )
            except Exception as e:
                st.session_state.pop("result", None)
                st.error(f"אירעה שגיאה בתהליך הניתוח: {e}. ודא שמפתחות ה-API מוגדרים כראוי בקובץ ה-env ונסה שוב.")

    if "result" not in st.session_state:
        render_footer()
        return
    score, data = st.session_state["result"]

    # מיצוי מכסת קצב (כל ה-Retries הסתיימו ב-429) - התראה מובחנת מכשל רשת: המשתמש צריך לדעת
    # שהמכסה היומית/הקרדיטים נגמרו (ולא שיש תקלת רשת חולפת) ולנסות מחר או להוסיף מפתחות.
    if any(c.get("manufacturer") == RATE_LIMIT_STATUS for c in data):
        st.warning(
            "⚠️ מכסת הקצב של ה-API מוצתה (Mouser: 1,000 קריאות ביום · Octopart/Nexar: קרדיטים). "
            "מוצגים נתוני ברירת מחדל עבור חלק מהרכיבים — נסו שוב מחר, או הוסיפו מפתחות API "
            "בסרגל הצד (🔌 הגדרות מפתחות API)."
        )

    # אם ה-Gatekeeper מיצה את כל ה-Retry-ים מול Mouser, נחשוף זאת במפורש ולא נציג בשקט N/A/❓
    if any(c.get("manufacturer") == NETWORK_ERROR_STATUS for c in data):
        st.warning(
            "⚠️ שגיאת רשת בפנייה ל-Mouser API (לאחר מספר ניסיונות חוזרים). "
            "מוצגים נתוני ברירת מחדל עבור חלק מהרכיבים — נסו שוב מאוחר יותר."
        )

    df = pd.DataFrame(build_rows(data))

    render_summary_metrics(summarize_risk(data), score)

    # שורת כותרת התוצאות: הכותרת בימין, מציין מקום לכפתור ההורדה בשמאל. הכפתור עצמו
    # מרונדר אחרי הסינון (למטה) כדי לייצא את ה-DataFrame המסונן/המוצג בפועל.
    col_title, col_download = st.columns([4, 1])
    col_title.subheader("תוצאות הניתוח")

    st.subheader("🔍 סינון ומיון")
    col_search, col_status, col_sort, col_order = st.columns([2, 2, 2, 1])
    search = col_search.text_input("חיפוש לפי מק\"ט או יצרן")
    statuses = col_status.multiselect(
        "סטטוס מחזור חיים", options=available_statuses(df), placeholder="בחרו סטטוסים"
    )
    sort_by = col_sort.selectbox("מיין לפי", options=sort_options(df))
    ascending = col_order.radio("סדר מיון", options=["עולה", "יורד"]) == "עולה"
    df = filter_and_sort(df, search, statuses, sort_by, ascending)

    # utf-8-sig מוסיף BOM כך ש-Excel יזהה נכון קידוד עברי בפתיחת קובץ ה-CSV
    col_download.download_button(
        "📥 הורד דוח (CSV)", data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="shalomci_report.csv", mime="text/csv"
    )
    render_table_view(df)
    render_footer()


if __name__ == "__main__":
    main()
