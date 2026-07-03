import time
from typing import Any, Dict

from src.services.gatekeeper import ApiGatekeeper
from src.shared.translations import format_lead_time


class DigiKeyClient:
    """
    קליינט אינטגרציה רשמי מול DigiKey Product Information V4.
    מאמת מול DigiKey באמצעות OAuth2 Client Credentials, ומנותב לחלוטין דרך שומר הסף.
    """
    TOKEN_URL = "https://api.digikey.com/v1/oauth2/token"
    SEARCH_URL = "https://api.digikey.com/products/v4/search"
    VENDOR_NAME = "DigiKey"
    TOKEN_EXPIRY_MARGIN_SECONDS = 30

    def __init__(self, client_id: str, client_secret: str, gatekeeper: ApiGatekeeper):
        if not client_id or not client_secret:
            raise ValueError("DigiKey client ID and secret are required.")
        self.client_id = client_id
        self.client_secret = client_secret
        self.gatekeeper = gatekeeper
        self._access_token = None
        self._token_expires_at = 0.0

    async def _get_access_token(self) -> str:
        """שולף Access Token דרך זרימת Client Credentials, וממחזר אותו עד לפקיעת התוקף."""
        if self._access_token and time.monotonic() < self._token_expires_at:
            return self._access_token

        response = await self.gatekeeper.request(
            provider="digikey",
            method="POST",
            url=self.TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
            timeout=10.0,
        )
        payload = response.json()
        self._access_token = payload["access_token"]
        expires_in = payload.get("expires_in", 600)
        self._token_expires_at = time.monotonic() + expires_in - self.TOKEN_EXPIRY_MARGIN_SECONDS
        return self._access_token

    async def search_part(self, mpn: str) -> Dict[str, Any]:
        """מחפש פרטי רכיב לפי מק"ט יצרן (DigiKey Product Information V4 - ProductDetails)."""
        token = await self._get_access_token()
        response = await self.gatekeeper.request(
            provider="digikey",
            method="GET",
            url=f"{self.SEARCH_URL}/{mpn}/productdetails",
            headers={
                "Authorization": f"Bearer {token}",
                "X-DIGIKEY-Client-Id": self.client_id,
            },
            timeout=10.0,
        )
        return response.json()

    @classmethod
    def parse_extra_fields(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """מחלץ שדות מורחבים ממבנה תגובת ProductDetails של DigiKey: מלאי/מחיר כמספרים גולמיים
        (להשוואת ספקים והצגה עם st.column_config) וזמן אספקה כטקסט עברי. מחזור חיים/ציון סיכון
        אינם נשלפים כאן - Mouser הוא המקור היחיד לכך (מוצג פעם אחת בלבד ב-GUI)."""
        product = payload.get("Product") or {}
        quantity = product.get("QuantityAvailable")
        unit_price = product.get("UnitPrice")
        lead_weeks = product.get("ManufacturerLeadWeeks")

        return {
            "digikey_stock_qty": float(quantity) if quantity is not None else None,
            "digikey_price_value": float(unit_price) if unit_price is not None else None,
            "digikey_lead_time": format_lead_time(lead_weeks) if lead_weeks else "זמן אספקה: לא ידוע",
        }
