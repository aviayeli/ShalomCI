import streamlit.components.v1 as components

# מזהה ה-<script> שמוזרק ל-head העליון - מונע הזרקה כפולה בכל rerun של Streamlit
# (Streamlit מריץ מחדש את כל הסקריפט בכל אינטראקציה של המשתמש, כמו לחיצת כפתור או שינוי סינון).
_SCRIPT_ELEMENT_ID = "enable-accessibility-widget"
_ENABLE_SCRIPT_URL = "https://cdn.enable.co.il/licenses/enable-L55759ypmgdn0l5n-0726-82870/init.js"


def inject_accessibility_widget() -> None:
    """
    מזריק את תפריט הנגישות של Enable.co.il לחלון העליון (window.parent) של הדף.

    Streamlit מרנדר components.html בתוך iframe מבודד (sandboxed) - סקריפט המוזרק דרך
    st.markdown/components.html ישירות ירוץ בתוך ה-iframe בלבד ולא ישפיע על שאר האפליקציה.
    לכן יוצרים כאן אלמנט <script> דרך JS ומוסיפים אותו במפורש ל-window.parent.document.head,
    כדי שהתפריט יפעל ברמת הדף המלא ולא רק בתוך ה-iframe המבודד של הרכיב הזה.
    """
    snippet = f"""
    <script>
    (function() {{
        try {{
            if (window.parent.document.getElementById('{_SCRIPT_ELEMENT_ID}')) {{
                return;
            }}
            var script = window.parent.document.createElement('script');
            script.id = '{_SCRIPT_ELEMENT_ID}';
            script.src = '{_ENABLE_SCRIPT_URL}';
            window.parent.document.head.appendChild(script);
        }} catch (e) {{
            console.error('Failed to inject accessibility widget:', e);
        }}
    }})();
    </script>
    """
    components.html(snippet, height=0, width=0)
