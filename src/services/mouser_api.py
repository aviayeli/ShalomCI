from typing import Any, Dict

from src.services.gatekeeper import ApiGatekeeper
from src.shared.translations import extract_number, format_lead_time, translate


class MouserClient:
    """
    קליינט אינטגרציה רשמי מול מנוע החיפוש של Mouser.
    מנותב לחלוטין דרך שומר הסף.
    """
    BASE_URL = "https://api.mouser.com/api/v1/search/partnumber"
    VENDOR_NAME = "Mouser"

    def __init__(self, api_key: str, gatekeeper: ApiGatekeeper):
        if not api_key:
            raise ValueError("Mouser API key is required.")
        self.api_key = api_key
        self.gatekeeper = gatekeeper

    async def search_part(self, mpn: str) -> Dict[str, Any]:
        """מחפש נתוני רכיב לפי מק"ט יצרן."""
        payload = {
            "SearchByPartRequest": {
                "mouserPartNumber": mpn,
                "partSearchOptions": "string"
            }
        }
        url = f"{self.BASE_URL}?apiKey={self.api_key}"

        # שיגור הקריאה דרך ה-Gatekeeper
        response = await self.gatekeeper.request(
            provider="mouser",
            method="POST",
            url=url,
            json=payload,
            timeout=10.0
        )

        return response.json()

    @classmethod
    def parse_extra_fields(cls, part: Dict[str, Any]) -> Dict[str, Any]:
        """מחלץ שדות מורחבים ממבנה חלק גולמי של Mouser: מלאי/מחיר כמספרים גולמיים (להשוואת
        ספקים והצגה עם st.column_config), וזמן אספקה/חלופה מוצעת/RoHS/אריזה כטקסט עברי."""
        price_breaks = part.get("PriceBreaks") or []
        unit_price = next((pb.get("Price") for pb in price_breaks if pb.get("Quantity") == 1), None)

        attributes = part.get("ProductAttributes") or []
        packaging = next(
            (a.get("AttributeValue") for a in attributes if a.get("AttributeName") == "Packaging"), None
        )

        return {
            "mouser_stock_qty": extract_number(part.get("Availability")),
            "mouser_price_value": extract_number(unit_price),
            "lead_time": format_lead_time(part.get("LeadTime")),
            "suggested_replacement": part.get("SuggestedReplacement") or "אין",
            "rohs_status": translate(part.get("ROHSStatus")),
            "packaging": packaging or "לא ידוע",
        }
