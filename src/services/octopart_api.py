import asyncio
import logging
import time
from typing import Any, Dict

import httpx

from src.services.gatekeeper import ApiGatekeeper
from src.shared.translations import format_lead_time

logger = logging.getLogger(__name__)

# שאילתת GraphQL יחידה המשמשת גם לנתוני מלאי/מחיר וגם לחלופות (similarParts) - שדה
# התוצאה העליון "supSearch" תואם במתכוון למבנה שכבר מצופה על ידי CrossReferenceEngine.find_alternatives.
# הערה: "lifecycleStatus" הוסר בכוונה - שדה זה לא קיים בפועל על הטיפוס SupPart בסכימת Nexar
# (400 Bad Request: "The field 'lifecycleStatus' does not exist on the type 'SupPart'").
# Mouser כבר משמש כמקור היחיד למחזור חיים/ציון סיכון (מוצג פעם אחת בלבד ב-GUI) - לכן השדה
# כלל לא נכלל בתגובה, ראו OctopartClient.parse_extra_fields.
_PART_QUERY = """
query PartSearch($mpn: String!) {
  supSearch(q: $mpn, limit: 1) {
    results {
      part {
        mpn
        manufacturer { name }
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
    משמש הן לשליפת נתוני רכיב משלימים (מלאי/זמן אספקה/מחיר - ראו הערה לגבי מחזור חיים
    ב-_PART_QUERY) והן לחיפוש חלופות FFF (similarParts) עבור CrossReferenceEngine.find_alternatives.
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
        self._token_lock = asyncio.Lock()  # single-flight: מונע N בקשות טוקן מקבילות (stampede)

    async def _get_access_token(self) -> str:
        """שולף Access Token דרך זרימת Client Credentials מול Nexar, וממחזר אותו עד לפקיעת התוקף."""
        if self._access_token and time.monotonic() < self._token_expires_at:
            return self._access_token

        # נעילה + בדיקה כפולה (double-checked): רק בקשה אחת בפועל מרעננת את הטוקן (מסלול מהיר ללא נעילה למעלה)
        async with self._token_lock:
            if self._access_token and time.monotonic() < self._token_expires_at:
                return self._access_token

            try:
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
            except httpx.HTTPStatusError as e:
                self._log_http_error("OAuth2 token request", e)
                raise
            payload = response.json()
            self._access_token = payload["access_token"]
            expires_in = payload.get("expires_in", 3600)
            self._token_expires_at = time.monotonic() + expires_in - self.TOKEN_EXPIRY_MARGIN_SECONDS
            return self._access_token

    async def search_part(self, mpn: str) -> Dict[str, Any]:
        """מריץ את שאילתת ה-GraphQL עבור מק"ט נתון (Octopart/Nexar supSearch)."""
        token = await self._get_access_token()
        try:
            response = await self.gatekeeper.request(
                provider="octopart",
                method="POST",
                url=self.GRAPHQL_URL,
                json={"query": _PART_QUERY, "variables": {"mpn": mpn}},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0,
            )
        except httpx.HTTPStatusError as e:
            self._log_http_error(f"supSearch query for mpn={mpn}", e)
            raise
        return response.json()

    # find_alternatives (FFF) משתמש באותה שאילתה בדיוק - היא כבר כוללת similarParts.
    search_cross_reference = search_part

    @staticmethod
    def _log_http_error(context: str, e: httpx.HTTPStatusError) -> None:
        """מדפיס ללוג את גוף תגובת השגיאה הגולמי (response.text) - Nexar/GraphQL בדרך כלל
        מחזירים הודעת שגיאה מפורטת (למשל שם שדה שגוי בשאילתת supSearch) בגוף תגובת ה-400."""
        status = e.response.status_code if e.response is not None else "?"
        body = e.response.text if e.response is not None else "<no response body>"
        logger.error(f"Octopart API error ({context}) - HTTP {status}: {body}")

    @classmethod
    def parse_extra_fields(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """מחלץ שדות מורחבים ממבנה תגובת ה-GraphQL של Octopart: מלאי/מחיר כמספרים גולמיים
        (מהמוכר הראשון עם הצעה, להשוואת ספקים והצגה עם st.column_config) וזמן אספקה כטקסט
        עברי. מחזור חיים/ציון סיכון אינם נשלפים כאן - Mouser הוא המקור היחיד לכך (ראו גם
        הערה ב-_PART_QUERY לגבי lifecycleStatus), ומוצג פעם אחת בלבד ב-GUI.

        Nexar עשוי להחזיר null (לא רק מפתח חסר) בכל שלב במבנה - data/supSearch/results/
        part/sellers/offers/prices - ואף עבור איברים בודדים בתוך רשימה (למשל sellers: [null])
        כשלרכיב חסר מידע. .get(key, default) לא מספיק - הוא מגן רק על מפתח חסר, לא על ערך
        null מפורש - לכן "or {}"/"or []" ופילטור איברי None בכל שלב."""
        results = ((payload.get("data") or {}).get("supSearch") or {}).get("results") or []
        part = ((results[0] or {}).get("part") or {}) if results else {}

        offer = next(
            (o for seller in (part.get("sellers") or []) if seller
             for o in (seller.get("offers") or []) if o),
            None,
        )
        quantity = offer.get("inventoryLevel") if offer else None
        lead_days = offer.get("factoryLeadDays") if offer else None
        prices = [p for p in ((offer or {}).get("prices") or []) if p]
        unit_price = next((p.get("price") for p in prices if p.get("quantity") == 1), None)
        if unit_price is None and prices:
            unit_price = prices[0].get("price")

        return {
            "octopart_stock_qty": float(quantity) if quantity is not None else None,
            "octopart_price_value": float(unit_price) if unit_price is not None else None,
            "octopart_lead_time": format_lead_time(f"{lead_days} Days") if lead_days is not None else "זמן אספקה: לא ידוע",
        }
