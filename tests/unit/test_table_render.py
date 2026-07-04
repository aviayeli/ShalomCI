import pandas as pd
import pytest

from src.gui.table_render import (_latin_ltr, _mpn_bidi, _price_text, _risk_color, _stock_text,
                                  _vendor_badge)


@pytest.mark.parametrize("value,expected", [
    (1.85, '<bdo dir="ltr">₪ 1.85</bdo>'),
    (1234.5, '<bdo dir="ltr">₪ 1,234.50</bdo>'),
    (None, "לא זמין"),
    (float("nan"), "לא זמין"),
])
def test_price_text_formats_currency_and_handles_missing(value, expected):
    """ערך מספרי נעטף ב-<bdo dir="ltr"> (בידוד Bidi לפי מערכת העיצוב); העברית "לא זמין"
    נשארת חשופה - כפיית LTR עליה הייתה מציגה אותה הפוך."""
    assert _price_text(value) == expected


@pytest.mark.parametrize("value,expected", [
    (24755.0, '<bdo dir="ltr">24,755</bdo>'),
    (0.0, '<bdo dir="ltr">0</bdo>'),
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


def test_mpn_bidi_wraps_value_in_bdo_tag():
    """מוודא שהמק"ט נעטף ב-<bdo dir="ltr"> (מערכת העיצוב; בעבר <bdi>) כדי שלא יתהפך בהקשר RTL."""
    assert _mpn_bidi("NE555P") == '<bdo dir="ltr">NE555P</bdo>'


def test_mpn_bidi_escapes_malicious_content_inside_the_tag():
    """מוודא שתוכן המק"ט עצמו מוברח נגד XSS, גם כשהוא עטוף ב-<bdo> לא-מוברח."""
    result = _mpn_bidi("<script>alert(1)</script>")
    assert result == '<bdo dir="ltr">&lt;script&gt;alert(1)&lt;/script&gt;</bdo>'


@pytest.mark.parametrize("value,expected", [
    ("12 Weeks", '<bdo dir="ltr">12 Weeks</bdo>'),
    ("2026-09-01", '<bdo dir="ltr">2026-09-01</bdo>'),
    ("LM358, SE555", '<bdo dir="ltr">LM358, SE555</bdo>'),
    ("זמן אספקה: לא ידוע", "זמן אספקה: לא ידוע"),
    ("אין", "אין"),
])
def test_latin_ltr_wraps_only_hebrew_free_values(value, expected):
    """טקסט לטיני/מספרי (זמני אספקה, תאריכים, רשימות מק"ט) נעטף ב-<bdo dir="ltr">; ערך המכיל
    ולו תו עברי אחד נשאר חשוף - כפיית LTR על עברית מרנדרת אותה הפוך."""
    assert _latin_ltr(value) == expected


def test_latin_ltr_escapes_malicious_content():
    """מוודא ש-_latin_ltr מבריח HTML בשני המסלולים (עטוף ולא-עטוף) - הוא מחליף את
    escape="html" של ה-Styler בעמודות שהוא מפרמט."""
    assert _latin_ltr("<script>x</script>") == '<bdo dir="ltr">&lt;script&gt;x&lt;/script&gt;</bdo>'
    assert _latin_ltr("עברית <b>") == "עברית &lt;b&gt;"


@pytest.mark.parametrize("vendor,slug", [
    ("Mouser", "mouser"),
    ("DigiKey", "digikey"),
    ("Octopart", "octopart"),
    ("לא ידוע", "unknown"),
])
def test_vendor_badge_wraps_value_in_per_vendor_pill(vendor, slug):
    """מוודא שכל ספק נעטף ב-span עם מחלקת ה-slug הייעודית שלו (או unknown לערך לא מוכר)."""
    result = _vendor_badge(vendor)
    assert result == f'<span class="vendor-badge vendor-badge-{slug}">{vendor}</span>'


def test_vendor_badge_escapes_malicious_content_inside_the_span():
    """מוודא שתוכן הספק מוברח נגד XSS בדיוק כמו ב-_mpn_bidi (format ללא escape="html")."""
    result = _vendor_badge("<script>alert(1)</script>")
    assert result == (
        '<span class="vendor-badge vendor-badge-unknown">'
        "&lt;script&gt;alert(1)&lt;/script&gt;</span>"
    )
