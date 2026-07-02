import pandas as pd
import pytest

from src.core.bom_parser import BomParser


@pytest.fixture
def parser():
    return BomParser()


def test_parse_valid_excel(parser, tmp_path):
    """מוודא שהמנוע מזהה עמודות מלוכלכות באקסל ומחלץ את המק"ט כראוי."""
    # יצירת DataFrame דמה
    df = pd.DataFrame({
        "  Part Number ": ["NE555P", "LM324", ""],
        "Mfg. Name": ["TI", "ST", "Unknown"],
        "Quantity": [10, 50, 0]
    })

    file_path = tmp_path / "dirty_bom.xlsx"
    df.to_excel(file_path, index=False)

    components = parser.parse_file(str(file_path))

    assert len(components) == 2, "השורות הריקות אמורות להיות מסוננות"
    assert components[0]["mpn"] == "NE555P"
    assert components[0]["manufacturer"] == "TI"


def test_parse_missing_mpn_column(parser, tmp_path):
    """מוודא זריקת שגיאה כאשר עמודת ה-MPN חסרה לחלוטין."""
    df = pd.DataFrame({"Description": ["Resistor"], "Price": [0.1]})
    file_path = tmp_path / "bad_bom.csv"
    df.to_csv(file_path, index=False)

    with pytest.raises(ValueError, match="Could not identify MPN column"):
        parser.parse_file(str(file_path))
