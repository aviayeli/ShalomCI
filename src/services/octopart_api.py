import time
from typing import Any, Dict

from src.services.gatekeeper import ApiGatekeeper
from src.shared.translations import format_inventory, format_lead_time, translate

# שאילתת GraphQL יחידה המשמשת גם לנתוני מלאי/מחיר וגם לחלופות (similarParts) - שדה
# התוצאה העליון "supSearch" תואם במתכוון למבנה שכבר מצופה על ידי CrossReferenceEngine.find_alternatives.
_PART_QUERY = """
query PartSearch($mpn: String!) {
  supSearch(q: $mpn, limit: 1) {
    results {
      part {
        mpn
        manufacturer { name }
        lifecycleStatus
        similarParts { mpn manufacturer { name } }
        sellers {
          company { name }
          offers { inventoryLevel factoryLeadDays prices { price currency quantity } }
        }
      }
    }
  }
}
"""


class OctopartClient:
    """
    קליינט אינטגרציה רשמי מול Octopart/Nexar Supply GraphQL API.
    מאמת מול Nexar Identity Server (OAuth2 Client Credentials), ומנותב לחלוטין דרך שומר הסף.
    משמש הן לשליפת נתוני רכיב משלימים (מחזור חיים/מלאי/זמן אספקה/מחיר) והן לחיפוש
    חלופות FFF (similarParts) עבור CrossReferenceEngine.find_alternatives.
    """
    TOKEN_URL = "https://identity.nexar.com/connect/token"
    GRAPHQL_URL = "https://api.nexar.com/graphql"
    VENDOR_NAME = "Octopart"
    TOKEN_EXPIRY_MARGIN_SECONDS = 30

    def __init__(self, client_id: str, client_secret: str, gatekeeper: ApiGatekeeper):
        if not client_id or not client_secret:
            raise ValueError("Octopart client ID and secret are required.")
        self.client_id = client_id
        self.client_secret = client_secret
        self.gatekeeper = gatekeeper
        self._access_token = None
        self._token_expires_at = 0.0

    async def _get_access_token(self) -> str:
        """שולף Access Token דרך זרימת Client Credentials מול Nexar, וממחזר אותו עד לפקיעת התוקף."""
        if self._access_token and time.monotonic() < self._token_expires_at:
            return self._access_token

        response = await self.gatekeeper.request(
            provider="octopart",
            method="POST",
            url=self.TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
                "scope": "supply.domain",
            },
            timeout=10.0,
        )
        payload = response.json()
        self._access_token = payload["access_token"]
        expires_in = payload.get("expires_in", 3600)
        self._token_expires_at = time.monotonic() + expires_in - self.TOKEN_EXPIRY_MARGIN_SECONDS
        return self._access_token

    async def search_part(self, mpn: str) -> Dict[str, Any]:
        """מריץ את שאילתת ה-GraphQL עבור מק"ט נתון (Octopart/Nexar supSearch)."""
        token = await self._get_access_token()
        response = await self.gatekeeper.request(
            provider="octopart",
            method="POST",
            url=self.GRAPHQL_URL,
            json={"query": _PART_QUERY, "variables": {"mpn": mpn}},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        return response.json()

    # find_alternatives (FFF) משתמש באותה שאילתה בדיוק - היא כבר כוללת similarParts.
    search_cross_reference = search_part

    @classmethod
    def parse_extra_fields(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """מחלץ ומתרגם שדות מורחבים ממבנה תגובת ה-GraphQL של Octopart (מחזור חיים,
        מלאי וזמן אספקה מהמוכר הראשון עם הצעה, ומחיר יחידה) לתצוגה בעברית לצד Mouser/DigiKey."""
        results = ((payload.get("data") or {}).get("supSearch") or {}).get("results") or []
        part = (results[0].get("part") or {}) if results else {}
        lifecycle = part.get("lifecycleStatus")

        offer = next(
            (o for seller in (part.get("sellers") or []) for o in (seller.get("offers") or [])), None
        )
        quantity = offer.get("inventoryLevel") if offer else None
        lead_days = offer.get("factoryLeadDays") if offer else None
        prices = (offer or {}).get("prices") or []
        unit_price = next((p.get("price") for p in prices if p.get("quantity") == 1), None)
        if unit_price is None and prices:
            unit_price = prices[0].get("price")

        return {
            "octopart_lifecycle": translate(lifecycle) if lifecycle else "לא ידוע",
            "octopart_inventory": (
                format_inventory(cls.VENDOR_NAME, f"{quantity:,}") if quantity is not None
                else f"{cls.VENDOR_NAME}: לא ידוע"
            ),
            "octopart_lead_time": format_lead_time(f"{lead_days} Days") if lead_days is not None else "זמן אספקה: לא ידוע",
            "octopart_price_per_unit": f"${unit_price:.2f}" if unit_price is not None else "לא זמין",
        }
