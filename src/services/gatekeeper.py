import asyncio
import logging
import time
from typing import Dict

import httpx

logger = logging.getLogger(__name__)


class RateLimitExhaustedError(Exception):
    """מיצוי מכסת קצב אמיתי (לא כשל רשת): כל הניסיונות החוזרים הסתיימו ב-429. נבדל מ-Exception
    הגנרי כדי שה-GUI יבחין בין 'נגמרה המכסה היומית/קרדיטים' לבין תקלת רשת ויציג התראה מתאימה."""

    def __init__(self, provider: str):
        self.provider = provider
        super().__init__(f"Rate limit quota exhausted for {provider}.")


class RateLimiter:
    """מנגנון Token Bucket לאכיפת מגבלות קצב (דקה/יום) כולל ניהול תור מקבילי."""

    def __init__(self, max_per_minute: int, max_per_day: int = 10000):
        self.max_per_minute = max_per_minute
        self.tokens = max_per_minute
        self.daily_tokens = max_per_day
        self.last_refill = time.monotonic()
        # סמפור המגביל מקסימום 5 קריאות סימולטניות כדי למנוע עומס רגעי (Burst)
        self.concurrency_lock = asyncio.Semaphore(5)

    async def acquire(self):
        """ממתין בסבלנות עד שיתפנה אסימון, גם ברמת הדקה וגם ברמת התור המקבילי."""
        await self.concurrency_lock.acquire()
        try:
            while True:
                now = time.monotonic()
                elapsed = now - self.last_refill

                # מילוי מחדש של אסימונים לפי הזמן שעבר
                refill_amount = elapsed * (self.max_per_minute / 60.0)
                if refill_amount > 0:
                    self.tokens = min(self.max_per_minute, self.tokens + refill_amount)
                    self.last_refill = now

                if self.tokens >= 1 and self.daily_tokens >= 1:
                    self.tokens -= 1
                    self.daily_tokens -= 1
                    return

                # אם אין אסימונים, המתן עשירית שנייה ובדוק שוב
                await asyncio.sleep(0.1)
        finally:
            self.concurrency_lock.release()


class ApiGatekeeper:
    """שומר הסף המרכזי. מנהל את כל בקשות הרשת היוצאות מהמערכת."""

    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {
            "mouser": RateLimiter(max_per_minute=30, max_per_day=1000),
            "octopart": RateLimiter(max_per_minute=50),
            "digikey": RateLimiter(max_per_minute=50)
        }
        self.client = httpx.AsyncClient()

    async def close(self):
        """סגירת חיבורי הרשת באופן יזום."""
        await self.client.aclose()

    async def request(self, provider: str, method: str, url: str, retries: int = 3, **kwargs) -> httpx.Response:
        """מבצע קריאת רשת מבוקרת הכוללת מגבלות קצב ומנגנון ניסיונות חוזרים (Exponential Backoff)."""
        limiter = self.limiters.get(provider.lower())
        if not limiter:
            raise ValueError(f"Provider '{provider}' is not supported by Gatekeeper.")

        delay = 1.0  # השהייה ראשונית של שנייה במקרה של חסימה
        # ה-429 מטופל ב-continue (לא דרך except), ולכן מיצוי הניסיונות "נופל" מהלולאה בשקט.
        # דגל זה מבחין בין fall-through שמקורו כולו ב-429 (מיצוי מכסה) לבין כשל רשת גנרי.
        last_failure_was_429 = False

        for attempt in range(retries):
            await limiter.acquire()
            try:
                response = await self.client.request(method, url, **kwargs)

                # טיפול אקטיבי בחסימת שרת
                if response.status_code == 429:
                    last_failure_was_429 = True
                    logger.warning(f"Rate limit hit (429) for {provider}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential Backoff
                    continue

                last_failure_was_429 = False

                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                # שגיאת לקוח (400/401/403/404 וכו', לא 429) היא תקלה בבקשה עצמה (למשל שאילתת
                # GraphQL שגויה) שלא תיפתר בניסיון חוזר - כישלון מהיר במקום Exponential Backoff
                # שחוסם באופן סינכרוני את כל תור העשרת ה-BOM (עד 200 רכיבים) לדקות ארוכות.
                if 400 <= status < 500:
                    logger.warning(f"Client error {status} from {provider}, failing fast (no retry): {e}")
                    raise
                if attempt == retries - 1:
                    raise e  # זריקת השגיאה אם חצינו את מכסת הניסיונות
                logger.warning(f"Server error: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
                delay *= 2
            except httpx.RequestError as e:
                if attempt == retries - 1:
                    raise e
                logger.warning(f"Network error: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
                delay *= 2

        # מיצוי הלולאה: אם הניסיון האחרון היה 429, זו מכסת קצב ממוצה (ולא כשל רשת) - נזרוק
        # שגיאה ייעודית כדי שה-GUI יציג התראת מכסה מובחנת. אחרת נשמור על ה-Exception הגנרי.
        if last_failure_was_429:
            raise RateLimitExhaustedError(provider)
        raise Exception(f"Failed to execute request to {provider} after {retries} retries.")
