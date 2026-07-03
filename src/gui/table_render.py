import pandas as pd
import streamlit as st

TABLE_CSS = """
body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
.risk-table { width: 100%; border-collapse: collapse; }
.risk-table thead th { position: sticky !important; top: 0 !important; background-color: #0056B3 !important;
    color: white !important; z-index: 1000 !important; padding: 10px; box-shadow: 0 2px 2px -1px rgba(0,0,0,0.4); }
.risk-table th, .risk-table td { border: 1px solid #ddd; padding: 8px; text-align: right; }
"""


def render_table(df: pd.DataFrame):  # pragma: no cover - חיווט Streamlit בלבד (Proxy)
    # iframe מבודד (st.iframe) עוקף את סינון aria-/role של DOMPurify ב-st.markdown ואת
    # התנגשות ה-CSS הגלובלי עם sticky header. format(escape="html") חובה: ה-iframe מריץ
    # HTML/JS גולמי בלי sanitization, והערכים מגיעים מ-Mouser API/BOM שהועלה - מקורות לא מהימנים.
    html_table = df.style.hide(axis="index").format(escape="html").map(
        lambda val: 'background-color: #FFCCCC' if val == 1 else (
            'background-color: #FFFFCC' if val in [2, 3] else 'background-color: #CCFFCC'),
        subset=['ציון סיכון']
    ).to_html(table_attributes='class="risk-table" role="table"').replace("<th ", '<th scope="col" ')

    full_html = (f'<!DOCTYPE html><html dir="rtl" lang="he"><head><style>{TABLE_CSS}</style></head>'
                 f'<body><div role="region" aria-label="טבלת נתוני רכיבים מועשרים" tabindex="0">'
                 f'{html_table}</div></body></html>')
    st.iframe(full_html, height=600)
