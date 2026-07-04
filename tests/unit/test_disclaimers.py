from unittest.mock import patch

from src.gui.disclaimers import (
    _API_LIMITS_DISCLAIMER,
    _DISCLAIMER_EXPANDER_TITLE,
    _FOOTER_CAPTION,
    _NONCOMMERCIAL_DISCLAIMER,
    render_disclaimers,
    render_footer,
)


def test_api_limits_disclaimer_states_exact_mouser_quotas():
    """מוודא שגילוי מגבלות ה-API נושא את המספרים המדויקים התואמים ל-ApiGatekeeper."""
    assert "1,000" in _API_LIMITS_DISCLAIMER
    assert "30" in _API_LIMITS_DISCLAIMER
    assert "Mouser" in _API_LIMITS_DISCLAIMER


def test_api_limits_disclaimer_names_all_free_tier_providers_and_caching():
    """מוודא שהגילוי מזכיר את יתר הספקים ואת שימור השאילתות באמצעות מטמון."""
    assert "DigiKey" in _API_LIMITS_DISCLAIMER
    assert "Octopart" in _API_LIMITS_DISCLAIMER or "Nexar" in _API_LIMITS_DISCLAIMER
    assert "מטמון" in _API_LIMITS_DISCLAIMER


def test_noncommercial_disclaimer_states_personal_noncommercial_use():
    """מוודא שגילוי תנאי השימוש מגביל לשימוש אישי, פנימי ובלתי-מסחרי בלבד."""
    assert "מסחרי" in _NONCOMMERCIAL_DISCLAIMER
    assert "אישי" in _NONCOMMERCIAL_DISCLAIMER


def test_footer_caption_is_concise_noncommercial_and_quota_reminder():
    """מוודא שכיתוב התחתית התמציתי מזכיר גם אי-מסחריות וגם מכסות מוגבלות."""
    assert "מסחרי" in _FOOTER_CAPTION
    assert "API" in _FOOTER_CAPTION


@patch("src.gui.disclaimers.st.markdown")
@patch("src.gui.disclaimers.st.divider")
@patch("src.gui.disclaimers.st.expander")
def test_render_disclaimers_uses_collapsed_expander_with_both_disclaimers(mock_expander, mock_divider, mock_markdown):
    """מוודא ששני הגילויים מרונדרים בתוך expander מכווץ (expanded=False)."""
    render_disclaimers()

    mock_expander.assert_called_once()
    args, kwargs = mock_expander.call_args
    assert args[0] == _DISCLAIMER_EXPANDER_TITLE
    assert kwargs["expanded"] is False
    rendered = [c.args[0] for c in mock_markdown.call_args_list]
    assert _API_LIMITS_DISCLAIMER in rendered
    assert _NONCOMMERCIAL_DISCLAIMER in rendered


@patch("src.gui.disclaimers.st.caption")
@patch("src.gui.disclaimers.st.divider")
def test_render_footer_emits_single_caption_reminder(mock_divider, mock_caption):
    """מוודא שהתחתית מציגה כיתוב תמציתי יחיד עם התזכורת הקבועה."""
    render_footer()

    mock_caption.assert_called_once_with(_FOOTER_CAPTION)
