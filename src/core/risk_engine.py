from typing import Any, Dict, List


class RiskEngine:
    """
    מנוע חישוב סיכונים.
    מעניק ציון מ-1 (קריטי) עד 5 (בריא) לכל רכיב בנפרד ולעץ המוצר (BOM) כולו.
    """

    def __init__(self):
        # מילון דירוג. ערכים נמוכים יותר ידרסו קודם במקרה של התאמה (למשל eol חזק מ-active)
        self.status_scores = {
            "obsolete": 1,
            "eol": 1,
            "end of life": 1,
            "ltb": 2,
            "last time buy": 2,
            "nrnd": 3,
            "not recommended": 3,
            "allocation": 4,
            "active": 5,
            "maturity": 5
        }

    def _calculate_component_score(self, status: str) -> int:
        clean_status = str(status).lower().strip()
        for key, score in self.status_scores.items():
            if key in clean_status:
                return score
        return 0  # סטטוס לא ידוע - דורש בדיקה ידנית

    def evaluate_components(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """עובר על רשימת הרכיבים ומוסיף מפתח 'risk_score' לכל אחד."""
        for comp in components:
            status = comp.get("lifecycle_status", "Unknown")
            comp["risk_score"] = self._calculate_component_score(status)
        return components

    def calculate_project_score(self, components: List[Dict[str, Any]]) -> float:
        """
        מחשב את ציון הסיכון של הפרויקט כולו.
        ציון פרויקט שמרני: הממוצע מוטה כלפי מטה כדי לשקף חומרה של רכיבי שוקת שבורה (EOL).
        """
        scores = [comp.get("risk_score", 0) for comp in components if comp.get("risk_score", 0) > 0]
        if not scores:
            return 0.0

        # חישוב ממוצע (עגול ל-2 ספרות עשרוניות)
        return round(sum(scores) / len(scores), 2)
