from typing import Any, Dict

from src.services.gatekeeper import ApiGatekeeper
from src.shared.translations import format_inventory, format_lead_time, translate


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
        """מחלץ ומתרגם שדות מורחבים ממבנה חלק גולמי של Mouser (מלאי, זמן אספקה, מחיר,
        חלופה מוצעת, RoHS ואריזה) לצורך הצגה בעברית ב-GUI ובדוחות."""
        price_breaks = part.get("PriceBreaks") or []
        unit_price = next((pb.get("Price") for pb in price_breaks if pb.get("Quantity") == 1), None)

        attributes = part.get("ProductAttributes") or []
        packaging = next(
            (a.get("AttributeValue") for a in attributes if a.get("AttributeName") == "Packaging"), None
        )

        return {
            "inventory": format_inventory(cls.VENDOR_NAME, part.get("Availability")),
            "lead_time": format_lead_time(part.get("LeadTime")),
            "price_per_unit": unit_price or "לא זמין",
            "suggested_replacement": part.get("SuggestedReplacement") or "אין",
            "rohs_status": translate(part.get("ROHSStatus")),
            "packaging": packaging or "לא ידוע",
        }
