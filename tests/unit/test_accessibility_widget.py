from unittest.mock import patch

from src.gui.accessibility_widget import (
    _ENABLE_SCRIPT_URL,
    _SCRIPT_ELEMENT_ID,
    inject_accessibility_widget,
)


@patch("src.gui.accessibility_widget.st.iframe")
def test_inject_accessibility_widget_embeds_enable_script_url(mock_iframe):
    """מוודא שה-snippet המוזרק כולל את כתובת סקריפט Enable.co.il המדויקת."""
    inject_accessibility_widget()

    mock_iframe.assert_called_once()
    snippet = mock_iframe.call_args[0][0]
    assert _ENABLE_SCRIPT_URL in snippet
    assert "<script>" in snippet


@patch("src.gui.accessibility_widget.st.iframe")
def test_inject_accessibility_widget_targets_parent_window_head(mock_iframe):
    """מוודא שה-snippet מוסיף את הסקריפט ל-window.parent.document.head, לא ל-document המקומי
    של ה-iframe המבודד של st.iframe - אחרת התפריט לא ישפיע על שאר האפליקציה."""
    inject_accessibility_widget()

    snippet = mock_iframe.call_args[0][0]
    assert "window.parent.document.head.appendChild" in snippet
    assert "window.parent.document.createElement" in snippet


@patch("src.gui.accessibility_widget.st.iframe")
def test_inject_accessibility_widget_guards_against_duplicate_injection(mock_iframe):
    """מוודא שה-snippet בודק אם הסקריפט כבר קיים לפני הזרקה חוזרת - חיוני כי Streamlit
    מריץ מחדש את כל הסקריפט בכל rerun (למשל לחיצת כפתור), לא רק בטעינה הראשונה."""
    inject_accessibility_widget()

    snippet = mock_iframe.call_args[0][0]
    assert f"getElementById('{_SCRIPT_ELEMENT_ID}')" in snippet


@patch("src.gui.accessibility_widget.st.iframe")
def test_inject_accessibility_widget_renders_near_invisible_iframe(mock_iframe):
    """מוודא שה-iframe כמעט ולא תופס מקום בעמוד (1x1, המינימום החוקי ב-st.iframe) -
    כל תפקידו הוא הזרקת JS, לא תצוגה. 0 אינו ערך חוקי (StreamlitInvalidWidthError)."""
    inject_accessibility_widget()

    _, kwargs = mock_iframe.call_args
    assert kwargs["height"] == 1
    assert kwargs["width"] == 1
