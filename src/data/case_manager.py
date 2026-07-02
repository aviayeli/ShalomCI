from datetime import datetime

import aiosqlite


class CaseManager:
    """
    מנהל תיקי טיפול (Cases) עבור רכיבים שהוגדרו כ-Obsolete ואין להם חלופה אוטומטית.
    """
    def __init__(self, db_path: str = "cases.db"):
        self.db_path = db_path

    async def init_db(self):
        """מאתחל את טבלת התיקים אם אינה קיימת."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mpn TEXT NOT NULL,
                    project_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP
                )
            """)
            await db.commit()

    async def open_case(self, mpn: str, project_name: str) -> int:
        """פותח תיק חדש לרכיב בעייתי ומחזיר את מזהה התיק."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO cases (mpn, project_name, status, created_at) VALUES (?, ?, ?, ?)",
                (mpn, project_name, "Open", datetime.now())
            )
            await db.commit()
            return cursor.lastrowid

    async def list_open_cases(self) -> list[dict]:
        """מחזיר רשימה של כל התיקים הפתוחים."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM cases WHERE status = 'Open'") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def close_case(self, case_id: int):
        """סוגר תיק פתוח (מעביר לסטטוס Closed)."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE cases SET status = 'Closed' WHERE id = ?", (case_id,))
            await db.commit()
