from typing import Any, Dict

from src.services.gatekeeper import ApiGatekeeper


class MouserClient:
    """
    קליינט אינטגרציה רשמי מול מנוע החיפוש של Mouser.
    מנותב לחלוטין דרך שומר הסף.
    """
    BASE_URL = "https://api.mouser.com/api/v1/search/partnumber"

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
