from typing import Dict, List, Optional

import pandas as pd


class BomParser:
    """
    מנוע קליטה ופירוק של עצי מוצר (BOM) מבוסס pandas.
    יודע להתמודד עם קבצי Excel ו-CSV בעלי עמודות לא אחידות.
    """

    def __init__(self):
        # מילון כינויים לזיהוי חכם של עמודות הליבה
        self.mpn_aliases = ['mpn', 'part number', 'mfg part number', 'manufacturer part', 'part_number', 'mfr. part']
        self.mfg_aliases = ['mfg', 'manufacturer', 'brand', 'make']

    def _find_column(self, columns: List[str], aliases: List[str]) -> Optional[str]:
        """מחפש עמודה שמתאימה לאחד הכינויים (Case-insensitive)."""
        for col in columns:
            clean_col = str(col).lower().strip()
            if any(alias in clean_col for alias in aliases):
                return col
        return None

    def parse_file(self, file_path: str) -> List[Dict[str, str]]:
        """קורא את הקובץ ומחזיר רשימת רכיבים מנורמלת."""
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format. Please provide .csv or .xlsx")

        mpn_col = self._find_column(df.columns, self.mpn_aliases)
        mfg_col = self._find_column(df.columns, self.mfg_aliases)

        if not mpn_col:
            raise ValueError("Could not identify MPN column in the provided file.")

        components = []
        for _, row in df.iterrows():
            mpn = str(row[mpn_col]).strip()
            # סינון שורות ריקות או שגיאות קריאה של pandas
            if mpn.lower() == 'nan' or not mpn:
                continue

            comp = {"mpn": mpn}
            if mfg_col:
                mfg_val = str(row[mfg_col]).strip()
                comp["manufacturer"] = mfg_val if mfg_val.lower() != 'nan' else ""

            components.append(comp)

        return components
