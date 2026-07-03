import pandas as pd
import pytest

from src.gui.table_render import _mpn_bidi, _price_text, _risk_color, _stock_text


@pytest.mark.parametrize("value,expected", [
    (1.85, "₪ 1.85"),
    (1234.5, "₪ 1,234.50"),
    (None, "לא זמין"),
    (float("nan"), "לא זמין"),
])
def test_price_text_formats_currency_and_handles_missing(value, expected):
    assert _price_text(value) == expected


@pytest.mark.parametrize("value,expected", [
    (24755.0, "24,755"),
    (0.0, "0"),
    (None, "לא ידוע"),
    (float("nan"), "לא ידוע"),
])
def test_stock_text_formats_thousands_and_handles_missing(value, expected):
    assert _stock_text(value) == expected


@pytest.mark.parametrize("score,expected_css", [
    (1, "background-color: #FFCCCC"),
    (2, "background-color: #FFFFCC"),
    (3, "background-color: #FFFFCC"),
    (4, "background-color: #CCFFCC"),
    (5, "background-color: #CCFFCC"),
])
def test_risk_color_maps_score_to_traffic_light(score, expected_css):
    assert _risk_color(score) == expected_css


def test_price_and_stock_text_treat_pandas_na_as_missing():
    """מוודא שגם pd.NA (לא רק None/float('nan')) מזוהה כערך חסר, כפי שעלול להגיע מ-DataFrame אמיתי."""
    assert _price_text(pd.NA) == "לא זמין"
    assert _stock_text(pd.NA) == "לא ידוע"


def test_mpn_bidi_wraps_value_in_bdi_tag():
    """מוודא שהמק"ט נעטף ב-<bdi> כדי שלא יתהפך/יישבר בהקשר RTL."""
    assert _mpn_bidi("NE555P") == "<bdi>NE555P</bdi>"


def test_mpn_bidi_escapes_malicious_content_inside_the_tag():
    """מוודא שתוכן המק"ט עצמו מוברח נגד XSS, גם כשהוא עטוף ב-<bdi> לא-מוברח."""
    result = _mpn_bidi("<script>alert(1)</script>")
    assert result == "<bdi>&lt;script&gt;alert(1)&lt;/script&gt;</bdi>"
