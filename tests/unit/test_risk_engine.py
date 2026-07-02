import pytest

from src.core.risk_engine import RiskEngine


@pytest.fixture
def engine():
    return RiskEngine()


def test_component_scoring(engine):
    """מוודא שזיהוי הסיכון ברמת הרכיב מדויק גם עם טקסטים שונים."""
    test_data = [
        {"mpn": "A1", "lifecycle_status": "Active"},
        {"mpn": "A2", "lifecycle_status": "NRND (Not Recommended)"},
        {"mpn": "A3", "lifecycle_status": "Last time buy"},
        {"mpn": "A4", "lifecycle_status": "Obsolete part"},
        {"mpn": "A5", "lifecycle_status": "Allocation - 52 weeks"}
    ]

    result = engine.evaluate_components(test_data)

    assert result[0]["risk_score"] == 5  # Active
    assert result[1]["risk_score"] == 3  # NRND
    assert result[2]["risk_score"] == 2  # LTB
    assert result[3]["risk_score"] == 1  # Obsolete
    assert result[4]["risk_score"] == 4  # Allocation


def test_project_score_calculation(engine):
    """מוודא את חישוב הממוצע ברמת הפרויקט."""
    test_data = [
        {"risk_score": 5},
        {"risk_score": 1},
        {"risk_score": 3}
    ]

    # הממוצע של 5, 1, 3 הוא 3.0
    project_score = engine.calculate_project_score(test_data)
    assert project_score == 3.0


def test_empty_project_score(engine):
    assert engine.calculate_project_score([]) == 0.0
