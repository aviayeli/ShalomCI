import os

from dotenv import load_dotenv

from src.core.bom_parser import BomParser
from src.core.cross_ref import CrossReferenceEngine
from src.core.reporter import ExcelReporter
from src.core.risk_engine import RiskEngine
from src.data.case_manager import CaseManager
from src.services.digikey_api import DigiKeyClient
from src.services.gatekeeper import ApiGatekeeper
from src.services.mouser_api import MouserClient
from src.services.octopart_api import OctopartClient
from src.shared.translations import translate

load_dotenv()

# שדות מורחבים המגיעים מ-cross_ref (זמינים כרגע רק כשה-Gatekeeper מחובר בפועל ל-Mouser)
# יחד עם ערכי ברירת מחדל בעברית לרכיב שלא נמצא עבורו מידע.
EXTRA_FIELD_DEFAULTS = {
    "inventory": "לא ידוע",
    "lead_time": "זמן אספקה: לא ידוע",
    "price_per_unit": "לא זמין",
    "suggested_replacement": "אין",
    "rohs_status": "לא ידוע",
    "packaging": "לא ידוע",
}


class ShalomCI_SDK:
    """שכבת הגישה המרכזית (SDK) עבור מערכת ShalomCI."""

    def __init__(self, db_path: str = "cases.db", api_client=None, digikey_client=None, octopart_client=None):
        self.case_manager = CaseManager(db_path)
        self.bom_parser = BomParser()
        self.risk_engine = RiskEngine()
        self.gatekeeper = ApiGatekeeper()
        self.cross_ref = CrossReferenceEngine(
            api_client or self._build_default_client(),
            digikey_client=digikey_client or self._build_digikey_client(),
            octopart_client=octopart_client or self._build_octopart_client(),
        )
        self.reporter = ExcelReporter()
        self.is_initialized = False

    def _build_default_client(self):
        """בונה קליינט Mouser דרך ה-Gatekeeper אם מוגדר מפתח API בסביבה, אחרת חוזר ל-N/A."""
        api_key = os.getenv("MOUSER_API_KEY")
        if not api_key:
            return None
        return MouserClient(api_key=api_key, gatekeeper=self.gatekeeper)

    def _build_digikey_client(self):
        """בונה קליינט DigiKey דרך ה-Gatekeeper אם DIGIKEY_CLIENT_ID/SECRET מוגדרים בסביבה."""
        client_id = os.getenv("DIGIKEY_CLIENT_ID")
        client_secret = os.getenv("DIGIKEY_CLIENT_SECRET")
        if not client_id or not client_secret:
            return None
        return DigiKeyClient(client_id=client_id, client_secret=client_secret, gatekeeper=self.gatekeeper)

    def _build_octopart_client(self):
        """בונה קליינט Octopart/Nexar דרך ה-Gatekeeper אם OCTOPART_CLIENT_ID/SECRET מוגדרים בסביבה."""
        client_id = os.getenv("OCTOPART_CLIENT_ID")
        client_secret = os.getenv("OCTOPART_CLIENT_SECRET")
        if not client_id or not client_secret:
            return None
        return OctopartClient(client_id=client_id, client_secret=client_secret, gatekeeper=self.gatekeeper)

    async def initialize(self):
        await self.case_manager.init_db()
        self.is_initialized = True

    async def close(self):
        """סוגר חיבורי רשת פתוחים (Gatekeeper) בתום השימוש ב-SDK."""
        await self.gatekeeper.close()

    async def process_bom(self, file_path: str) -> list:
        return self.bom_parser.parse_file(file_path)

    async def enrich_components(self, bom_data: list):
        """משיכת נתונים מהספקים ועדכון כל רכיב."""
        print(f"DEBUG: מתחיל העשרה ל-{len(bom_data)} רכיבים...")
        for comp in bom_data:
            mpn = comp.get("mpn")
            if not mpn: continue

            # פנייה למנוע הצלבת הנתונים (שישתמש ב-API Key ששמנו ב-env)
            # נניח שהמנוע מחזיר דיקשנרי עם המידע
            data = await self.cross_ref.get_part_data(mpn)

            if data:
                comp["manufacturer"] = data.get("manufacturer", "Unknown")
                comp["lifecycle_status"] = data.get("lifecycle", "Unknown")
                # בהמשך נוסיף כאן לוגיקת חישוב ציון סיכון מורכבת
                comp["risk_score"] = data.get("risk_score", 3)
            else:
                comp["manufacturer"] = "N/A"
                comp["lifecycle_status"] = "N/A"
                comp["risk_score"] = 5

            for field, default in EXTRA_FIELD_DEFAULTS.items():
                comp[field] = (data or {}).get(field, default)

            # נתוני DigiKey/Octopart מוצגים side-by-side לצד Mouser - תמיד נשלפים בנפרד, גם אם
            # ה-Mouser lookup נכשל, ולעולם אינם משפיעים על risk_score/lifecycle_status.
            comp.update(await self.cross_ref.get_digikey_data(mpn))
            comp.update(await self.cross_ref.get_octopart_data(mpn))
        print("DEBUG: העשרה הסתיימה בהצלחה.")

    async def evaluate_risks(self, enriched_data: list) -> dict:
        # ציון הסיכון מחושב תחילה על בסיס lifecycle_status באנגלית (מפתחות ה-RiskEngine
        # תואמי-אנגלית) - רק לאחר מכן מתורגם השדה לעברית לצורך תצוגה ב-GUI/דוחות.
        evaluated = self.risk_engine.evaluate_components(enriched_data)
        project_score = self.risk_engine.calculate_project_score(evaluated)
        for comp in evaluated:
            comp["lifecycle_status"] = translate(comp.get("lifecycle_status", "Unknown"))
        return {"project_score": project_score, "components": evaluated}

    async def find_mitigations(self, evaluated_components: list, project_name: str = "Default Project") -> list:
        """
        מאתר חלופות לרכיבים מסוכנים.
        הלוגיקה הקריטית: אם רכיב יצא מפס הייצור (Obsolete - ציון 1) ואין לו חלופות,
        המערכת פותחת לו אוטומטית "תיק טיפול" בבסיס הנתונים לטיפול הנדסי.
        """
        for comp in evaluated_components:
            score = comp.get("risk_score", 5)
            comp["alternatives"] = []

            # חיפוש חלופות אך ורק אם הרכיב בסיכון מסוים (1, 2, או 3)
            if score <= 3:
                alts = await self.cross_ref.find_alternatives(comp.get("mpn", ""))
                comp["alternatives"] = alts

                # תנאי פתיחת קריאת Case
                if score == 1 and not alts:
                    await self.case_manager.open_case(comp.get("mpn", "Unknown"), project_name)

        return evaluated_components

    async def generate_report(self, final_data: list, output_path: str):
        self.reporter.generate_report(final_data, output_path)
