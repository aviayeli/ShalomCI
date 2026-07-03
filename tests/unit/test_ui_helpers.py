from unittest.mock import patch

from src.gui.ui_helpers import _BLANK_BOM_TEMPLATE_CSV, render_welcome_header


@patch("src.gui.ui_helpers.st.download_button")
@patch("src.gui.ui_helpers.st.info")
def test_render_welcome_header_explains_data_sources_and_mpn_requirement(mock_info, mock_download):
    """מוודא שהודעת הפתיחה מזכירה את שלושת הספקים ואת דרישת עמודת ה-MPN המדויקת."""
    render_welcome_header()

    mock_info.assert_called_once()
    message = mock_info.call_args[0][0]
    assert "Mouser" in message
    assert "DigiKey" in message
    assert "Octopart" in message
    assert "MPN" in message


@patch("src.gui.ui_helpers.st.download_button")
@patch("src.gui.ui_helpers.st.info")
def test_render_welcome_header_offers_blank_template_download(mock_info, mock_download):
    """מוודא שכפתור ההורדה מציע תבנית CSV חוקית עם כותרת MPN בלבד."""
    render_welcome_header()

    mock_download.assert_called_once()
    _, kwargs = mock_download.call_args
    assert kwargs["data"] == _BLANK_BOM_TEMPLATE_CSV.encode("utf-8-sig")
    assert kwargs["file_name"].endswith(".csv")
    assert kwargs["mime"] == "text/csv"


def test_blank_bom_template_contains_only_mpn_header():
    """מוודא שהתבנית הריקה היא בדיוק כותרת עמודה אחת (MPN) ללא שורות דמה."""
    assert _BLANK_BOM_TEMPLATE_CSV == "MPN\n"
