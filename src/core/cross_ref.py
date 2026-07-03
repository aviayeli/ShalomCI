from typing import Any, Dict, List

import httpx

from src.services.digikey_api import DigiKeyClient
from src.services.mouser_api import MouserClient
from src.services.octopart_api import OctopartClient

# מסמן סטטוס ייעודי לשגיאת רשת אמיתית (ה-Gatekeeper מיצה את כל ניסיונות ה-Retry),
# בניגוד ל"Unknown"/"Error" עסקיים רגילים - כדי שממשק המשתמש (GUI) יוכל להבחין בין
# "לא מצאנו את הרכיב" לבין "לא הצלחנו בכלל להגיע ל-Mouser" ולהציג התראה מפורשת על כך.
NETWORK_ERROR_STATUS = "Network Error"

# ברירות מחדל בעברית לנתוני DigiKey/Octopart - מוצגים לצד Mouser (side-by-side), אינם
# משפיעים על risk_score המרכזי שממשיך להיות מחושב אך ורק מנתוני Mouser/lifecycle_status.
DIGIKEY_FIELD_DEFAULTS = {
    "digikey_lifecycle": "לא ידוע",
    "digikey_inventory": "DigiKey: לא ידוע",
    "digikey_lead_time": "זמן אספקה: לא ידוע",
    "digikey_price_per_unit": "לא זמין",
}
OCTOPART_FIELD_DEFAULTS = {
    "octopart_lifecycle": "לא ידוע",
    "octopart_inventory": "Octopart: לא ידוע",
    "octopart_lead_time": "זמן אספקה: לא ידוע",
    "octopart_price_per_unit": "לא זמין",
}


class CrossReferenceEngine:
    """
    מנוע לאיתור חלופות (FFF - Form, Fit, Function) ונתוני רכיבים.
    פועל באמצעות קליינט ראשי (Mouser) המנותב דרך Gatekeeper, וכן (אופציונלית) קליינטי
    DigiKey ו-Octopart נפרדים להעשרה משלימה של אותו רכיב side-by-side. חיפוש חלופות FFF
    (find_alternatives) מעדיף את קליינט Octopart, שהוא ספק הקרוס-רפרנס הטבעי.
    """

    def __init__(self, api_client=None, digikey_client: DigiKeyClient = None, octopart_client: OctopartClient = None):
        self.api_client = api_client
        self.digikey_client = digikey_client
        self.octopart_client = octopart_client

    async def get_part_data(self, mpn: str) -> Dict[str, Any]:
        """
        שליפת נתונים בסיסיים על רכיב (יצרן, סטטוס חיים, ציון סיכון).
        מבנה התגובה תואם ל-REST API של Mouser (SearchResults.Parts).
        """
        if not self.api_client:
            return {"manufacturer": "N/A", "lifecycle": "N/A", "risk_score": 5}

        try:
            # פנייה ל-API לקבלת פרטי הרכיב
            result = await self.api_client.search_part(mpn)

            # חילוץ הנתונים ממבנה תגובת Mouser
            # שימו לב: Mouser מחזירה את המפתח "SearchResults" עם ערך None (לא חסר!) במקרה
            # של שגיאה (למשל מפתח API לא תקין) - לכן לא ניתן לסמוך על ברירת המחדל של .get() בלבד.
            parts = (result.get("SearchResults") or {}).get("Parts") or []
            if not parts:
                return {"manufacturer": "Unknown", "lifecycle": "Unknown", "risk_score": 5}

            part = parts[0]

            # מיפוי השדות
            lifecycle = part.get("LifecycleStatus") or "Unknown"
            # לוגיקת ציון סיכון: 1 ל-EOL, 3 ל-NRND, 5 לתקין
            risk_map = {"EOL": 1, "NRND": 3, "Active": 5, "New Product": 5}

            result = {
                "manufacturer": part.get("Manufacturer", "Unknown"),
                "lifecycle": lifecycle,
                "risk_score": risk_map.get(lifecycle, 3)
            }
            # שדות מורחבים (מלאי, זמן אספקה, מחיר וכו') זמינים כרגע רק עבור Mouser -
            # בדיקת isinstance מפורשת (ולא duck-typing) כדי לא "לתפוס" מוקים גנריים בבדיקות.
            if isinstance(self.api_client, MouserClient):
                result.update(MouserClient.parse_extra_fields(part))
            return result
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            # ה-Gatekeeper כבר מיצה את כל ניסיונות ה-Retry - זו שגיאת רשת אמיתית ולא רכיב לא ידוע.
            print(f"DEBUG: שגיאת רשת בשליפת נתוני רכיב {mpn}: {e}")
            return {"manufacturer": NETWORK_ERROR_STATUS, "lifecycle": NETWORK_ERROR_STATUS, "risk_score": 0}
        except Exception as e:
            print(f"DEBUG: שגיאה בשליפת נתוני רכיב {mpn}: {e}")
            return {"manufacturer": "Error", "lifecycle": "Error", "risk_score": 5}

    async def _get_secondary_vendor_data(self, client, parser, defaults: dict, vendor: str, mpn: str) -> Dict[str, Any]:
        """
        שליפה גנרית של נתוני ספק משני (DigiKey/Octopart) המוצגים side-by-side ב-GUI, תמיד
        מנותבת דרך ה-Gatekeeper של הקליינט עצמו. אינה משפיעה על risk_score המרכזי - כשל/העדר
        קליינט מחזירים ברירות מחדל בעברית, לא זורקים (זהה במבנה לשני הספקים - ראו get_digikey_data/get_octopart_data).
        """
        if not client:
            return dict(defaults)
        try:
            payload = await client.search_part(mpn)
            return parser(payload)
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            print(f"DEBUG: שגיאת רשת בשליפת נתוני {vendor} עבור {mpn}: {e}")
            return dict(defaults)
        except Exception as e:
            print(f"DEBUG: שגיאה בשליפת נתוני {vendor} עבור {mpn}: {e}")
            return dict(defaults)

    async def get_digikey_data(self, mpn: str) -> Dict[str, Any]:
        """שליפת נתוני DigiKey משלימים (מחזור חיים, מלאי, זמן אספקה, מחיר)."""
        return await self._get_secondary_vendor_data(
            self.digikey_client, DigiKeyClient.parse_extra_fields, DIGIKEY_FIELD_DEFAULTS, "DigiKey", mpn
        )

    async def get_octopart_data(self, mpn: str) -> Dict[str, Any]:
        """שליפת נתוני Octopart משלימים (מלאי, זמן אספקה, מחיר; מחזור חיים תמיד 'לא ידוע')."""
        return await self._get_secondary_vendor_data(
            self.octopart_client, OctopartClient.parse_extra_fields, OCTOPART_FIELD_DEFAULTS, "Octopart", mpn
        )

    async def find_alternatives(self, mpn: str) -> List[Dict[str, Any]]:
        """
        מחפש חלופות (FFF) לרכיב מסוים.
        מעדיף את קליינט ה-Octopart (ספק הקרוס-רפרנס הטבעי); נופל בחזרה ל-api_client הראשי
        רק אם הוא עצמו תומך בקרוס-רפרנס (לצורכי בדיקות/הזרקה ידנית). Mouser/DigiKey הרגילים
        אינם תומכים בכך.
        """
        client = self.octopart_client or self.api_client
        if not client or not hasattr(client, "search_cross_reference"):
            return []

        try:
            result = await client.search_cross_reference(mpn)

            # חילוץ בטוח מתוך מבנה GraphQL - Nexar עשוי להחזיר null (לא רק מפתח חסר) עבור
            # data/supSearch/results/part/similarParts, ואף עבור איברים בודדים בתוך רשימה
            # (למשל results: [null]) כשלרכיב מסוים חסר מידע. .get(key, default) לא מספיק
            # כאן - הוא מגן רק על מפתח חסר, לא על ערך null מפורש - לכן "or {}"/"or []" בכל שלב.
            sup_search = ((result or {}).get("data") or {}).get("supSearch") or {}
            parts = sup_search.get("results") or []
            if not parts:
                return []

            first_part = (parts[0] or {}).get("part") or {}
            similar_parts = first_part.get("similarParts") or []
            return [sp for sp in similar_parts if sp]
        except Exception as e:
            print(f"DEBUG: שגיאה באיתור חלופות עבור {mpn}: {e}")
            return []
