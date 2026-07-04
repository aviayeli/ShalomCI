import hmac
import os

import streamlit as st


def auth_enabled() -> bool:
    """אימות הוא אופציונלי: מופעל רק אם הוגדרה סיסמה (SHALOMCI_PASSWORD) לא-ריקה.
    בלי סיסמה - האפליקציה רצה בדיוק כמו קודם, ללא מסך התחברות."""
    return bool(os.environ.get("SHALOMCI_PASSWORD"))


def check_credentials(username: str, password: str) -> bool:
    """השוואת אישורים מול משתני הסביבה. משתמש ברירת מחדל: 'admin' אם SHALOMCI_USERNAME לא הוגדר.
    hmac.compare_digest על שני השדות מונע השוואה מבוססת-זמן (timing attack) שעלולה לדלוף אורך/תוכן."""
    expected_user = os.environ.get("SHALOMCI_USERNAME", "admin")
    expected_pass = os.environ.get("SHALOMCI_PASSWORD", "")
    user_ok = hmac.compare_digest(username.encode("utf-8"), expected_user.encode("utf-8"))
    pass_ok = hmac.compare_digest(password.encode("utf-8"), expected_pass.encode("utf-8"))
    return user_ok and pass_ok


def require_login() -> bool:  # pragma: no cover - חיווט Streamlit; הלוגיקה נבדקת ב-check_credentials/auth_enabled
    """שער הכניסה שנקרא מ-main(). מחזיר True אם מותר להמשיך (אימות כבוי או המשתמש מחובר),
    אחרת מרנדר מסך התחברות ומחזיר False. מצב האימות חי רק ב-session_state - סגירת הלשונית
    הורגת את ה-WebSocket וכך מנתקת באופן טבעי (ללא cookies/localStorage)."""
    if not auth_enabled() or st.session_state.get("authenticated"):
        return True

    st.title("🔐 התחברות ל-ShalomCI")
    st.header("נא להזדהות כדי להמשיך")
    # מרכוז הטופס בעמודה אמצעית - כך זה נראה כמסך התחברות ולא כטופס ברוחב מלא.
    _, center, _ = st.columns([1, 2, 1])
    with center:
        # st.form כדי שלחיצת Enter תשלח (ולא רק לחיצה על הכפתור).
        with st.form("login_form"):
            username = st.text_input("שם משתמש")
            password = st.text_input("סיסמה", type="password")
            if st.form_submit_button("התחברות"):
                if check_credentials(username, password):
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("שם משתמש או סיסמה שגויים")
    return False


def render_logout_button() -> None:  # pragma: no cover - חיווט Streamlit בלבד
    """כפתור התנתקות בתחתית סרגל הצד (no-op כשאימות כבוי). בהתנתקות מסירים גם את 'result'
    (מטען הניתוח במטמון) כדי שתוצאות לא ישרדו לתוך התחברות הבאה באותו session של הדפדפן."""
    if not auth_enabled():
        return
    if st.sidebar.button("🚪 התנתקות"):
        st.session_state.pop("authenticated", None)
        st.session_state.pop("result", None)
        st.rerun()
