from unittest.mock import MagicMock, patch

from src.gui.ui_helpers import (
    _BLANK_BOM_TEMPLATE_CSV,
    RTL_CSS,
    render_summary_metrics,
    render_welcome_header,
)


def test_rtl_css_exempts_material_icon_font_to_prevent_duplicate_caption():
    """מוודא שה-CSS מחזיר את פונט האייקונים (Material Symbols) - התיקון לכיתוב הכפול."""
    assert '[data-testid="stIconMaterial"]' in RTL_CSS
    assert "'Material Symbols Rounded' !important" in RTL_CSS


def test_rtl_css_hebraizes_uploader_dropzone_scoped_to_testids():
    """מוודא שההנחיות עברותו דרך ה-test-ids המדויקים של Streamlit 1.58 (ללא selector כללי)."""
    assert '[data-testid="stFileUploaderDropzoneInstructions"]::after' in RTL_CSS
    assert "גררו קובץ לכאן או לחצו לבחירה" in RTL_CSS
    assert '[data-testid="stFileUploaderDropzone"] button' in RTL_CSS


@patch("src.gui.ui_helpers.st.download_button")
@patch("src.gui.ui_helpers.st.markdown")
@patch("src.gui.ui_helpers.st.expander")
def test_render_welcome_header_explains_data_sources_and_mpn_requirement(mock_expander, mock_markdown, mock_download):
    """מוודא שהסבר הפתיחה (בתוך expander) מזכיר את שלושת הספקים ואת דרישת עמודת ה-MPN."""
    render_welcome_header(expanded=True)

    mock_markdown.assert_called_once()
    message = mock_markdown.call_args[0][0]
    assert "Mouser" in message
    assert "DigiKey" in message
    assert "Octopart" in message
    assert "MPN" in message


@patch("src.gui.ui_helpers.st.download_button")
@patch("src.gui.ui_helpers.st.markdown")
@patch("src.gui.ui_helpers.st.expander")
def test_render_welcome_header_uses_collapsible_expander(mock_expander, mock_markdown, mock_download):
    """מוודא שההסבר מרונדר כ-st.expander מתקפל, עם מצב expanded לפי הפרמטר שהתקבל."""
    render_welcome_header(expanded=False)

    mock_expander.assert_called_once()
    _, kwargs = mock_expander.call_args
    assert kwargs["expanded"] is False


@patch("src.gui.ui_helpers.st.download_button")
@patch("src.gui.ui_helpers.st.markdown")
@patch("src.gui.ui_helpers.st.expander")
def test_render_welcome_header_offers_blank_template_download(mock_expander, mock_markdown, mock_download):
    """מוודא שכפתור ההורדה מציע תבנית CSV חוקית עם כותרת MPN בלבד."""
    render_welcome_header(expanded=True)

    mock_download.assert_called_once()
    _, kwargs = mock_download.call_args
    assert kwargs["data"] == _BLANK_BOM_TEMPLATE_CSV.encode("utf-8-sig")
    assert kwargs["file_name"].endswith(".csv")
    assert kwargs["mime"] == "text/csv"


def test_blank_bom_template_contains_only_mpn_header():
    """מוודא שהתבנית הריקה היא בדיוק כותרת עמודה אחת (MPN) ללא שורות דמה."""
    assert _BLANK_BOM_TEMPLATE_CSV == "MPN\n"


@patch("src.gui.ui_helpers.st.columns")
def test_render_summary_metrics_renders_five_metrics_with_counts_and_score(mock_columns):
    """מוודא ש-render_summary_metrics מציג 5 מדדים: הספירות מ-dict הסיכום + ציון סיכון כללי."""
    cols = [MagicMock() for _ in range(5)]
    mock_columns.return_value = cols

    render_summary_metrics({"total": 5, "critical": 1, "warning": 2, "healthy": 2}, 3.4)

    mock_columns.assert_called_once_with(5)
    assert cols[0].metric.call_args[0] == ("סה\"כ רכיבים", 5)
    assert cols[1].metric.call_args[0] == ("סיכון קריטי", 1)
    assert cols[2].metric.call_args[0] == ("אזהרה", 2)
    assert cols[3].metric.call_args[0] == ("תקינים", 2)
    assert cols[4].metric.call_args[0] == ("ציון סיכון כללי", "\u20663.4 / 5.0\u2069")
    assert cols[4].metric.call_args[1]["help"]
