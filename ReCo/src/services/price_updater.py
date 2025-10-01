# services/price_updater.py
from __future__ import annotations

import os, re, json, time, sqlite3, asyncio, contextlib, urllib.parse
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from statistics import median, mean
from urllib.parse import urlparse
from openai import OpenAI

# === 설정 ===============================================================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./used_pricer.db")
SERPAPI_KEY  = os.getenv("SERPAPI_KEY")        # 없으면 호출 시 에러
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")   # 없으면 휴리스틱
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
UPDATE_BATCH_LIMIT = int(os.getenv("UPDATE_BATCH_LIMIT", "100"))

# === 데이터 모델 =========================================================
@dataclass
class Listing:
    title: str
    url: str
    source: str
    price_krw: float

# === 검색어 정제 ========================================================
def extract_product_query(title: str, brand: Optional[str] = None) -> str:
    t = title.strip()
    if brand and brand.lower() not in t.lower():
        t = f"{brand} {t}"
    noise = [
        r"\[[^\]]+\]", r"\([^\)]+\)", r"무료배송", r"새상품", r"미개봉", r"쿠폰",
        r"번들", r"세트", r"사은품", r"[😊-🧿]", r"[^\w\s가-힣/+-]", r"\b중고\b",
        r"\b최저가\b", r"\b급처\b", r"\b당일배송\b"
    ]
    for p in noise:
        t = re.sub(p, " ", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+", " ", t).strip()
    if not OPENAI_API_KEY:
        return " ".join(t.split()[:6])
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = (
            "상품명에서 불필요한 정보를 제거하고 핵심 키워드만 남겨라. "
            "6단어 이내 한국어로.\n"
            f"원문: {title}"
        )
        res = client.responses.create(model=OPENAI_MODEL, input=prompt)
        return res.output_text.strip() or " ".join(t.split()[:6])
    except Exception:
        return " ".join(t.split()[:6])

# === 가격 파싱 유틸 ======================================================
_PRICE_RE = re.compile(r"([0-9][0-9,]{2,})\s*원|₩\s*([0-9][0-9,]{2,})")

def _parse_prices_from_texts(texts: List[str]) -> List[float]:
    out = []
    for t in texts:
        for m in _PRICE_RE.finditer(t):
            g = next(x for x in m.groups() if x)
            try:
                out.append(float(g.replace(",", "")))
            except Exception:
                pass
    return out

# === Joongna Provider (Playwright) =======================================
async def _joongna_query_playwright(query: str, max_wait: float = 8.0) -> List[float]:
    from playwright.async_api import async_playwright
    q = urllib.parse.quote(query)
    url = f"https://web.joongna.com/search-price?query={q}"
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=os.getenv("USER_AGENT", "Mozilla/5.0 used_pricer/0.1"),
            locale="ko-KR",
        )
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        texts: List[str] = []
        with contextlib.suppress(Exception):
            items = await page.locator("css=[class*='list'], [class*='card'], [role='list'], [role='grid']").all_inner_texts()
            texts.extend(items)
        with contextlib.suppress(Exception):
            summary = await page.locator("css=[class*='summary'], [class*='price'], [class*='stat']").all_inner_texts()
            texts.extend(summary)
        if not texts:
            with contextlib.suppress(Exception):
                body_text = await page.inner_text("body", timeout=int(max_wait*1000))
                texts.append(body_text)
        await browser.close()
    return _parse_prices_from_texts(texts)

def joongna_search_prices(query: str) -> List[float]:
    try:
        return asyncio.run(_joongna_query_playwright(query))
    except Exception:
        return []

# === SerpAPI Provider (폴백) =============================================
def serp_search(query: str, max_results: int = 30) -> List[Listing]:
    if not SERPAPI_KEY:
        return []
    import requests
    params = {
        "engine": "google",
        "q": f"{query} 중고 시세 site:joongna.com OR site:daangn.com OR site:bunjang.co.kr",
        "hl": "ko", "gl": "kr",
        "api_key": SERPAPI_KEY, "num": max(10, min(max_results, 50)),
    }
    r = requests.get("https://serpapi.com/search.json", params=params, timeout=20)
    data = r.json()
    out: List[Listing] = []
    for item in data.get("shopping_results", []):
        p = item.get("extracted_price") or _parse_prices_from_texts([item.get("price","")])
        if p:
            out.append(Listing(item.get("title",""), item.get("link",""), "shopping", float(p if isinstance(p,float) else p[0])))
    for item in data.get("organic_results", []):
        txt = item.get("title","") + " " + item.get("snippet","")
        prices = _parse_prices_from_texts([txt])
        if prices:
            out.append(Listing(item.get("title",""), item.get("link",""), "organic", prices[0]))
    return out

# === 통계/할인율 계산 =====================================================
def iqr_filter(values: List[float]) -> List[float]:
    if not values: return []
    s = sorted(values); n = len(s)
    if n < 4: return s
    q1, q3 = median(s[: n//2]), median(s[(n+1)//2 :])
    iqr = q3 - q1; lo, hi = q1 - 1.5*iqr, q3 + 1.5*iqr
    return [x for x in s if lo <= x <= hi]

def summarize_used(values: List[float]) -> Tuple[float,float]:
    f = iqr_filter(values)
    return (float(mean(f)), float(median(f))) if f else (0.0,0.0)

def compute_discounts(my_price: float, used_avg: float, used_p50: float) -> Dict[str,float]:
    def d(a,b): return round((b-a)/b,4) if b>0 else 0.0
    return {"discount_vs_used_avg": d(my_price, used_avg),
            "discount_vs_used_p50": d(my_price, used_p50)}

# === DB 어댑터 ===========================================================
class DB:
    def __init__(self, url: str):
        self.scheme = urlparse(url).scheme.split("+")[0]
        if self.scheme=="sqlite":
            path = url.split(":///")[-1]
            self.conn = sqlite3.connect(path, isolation_level=None)
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.kind="sqlite"
        else:
            import pymysql
            p = urlparse(url)
            self.conn = pymysql.connect(
                host=p.hostname, port=p.port or 3306,
                user=p.username, password=p.password,
                database=(p.path or "/")[1:] or None,
                charset="utf8mb4", autocommit=True,
                cursorclass=pymysql.cursors.DictCursor)
            self.kind="mysql"
    def ensure_schema(self):
        if self.kind=="sqlite":
            self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS items(
                id INTEGER PRIMARY KEY, name TEXT, brand TEXT,
                price REAL, is_active INTEGER DEFAULT 1,
                market_price_used_avg REAL, market_price_used_p50 REAL,
                discount_vs_used_avg REAL, discount_vs_used_p50 REAL,
                last_pricing_updated_at TEXT
            );
            """)
        # listing_cache 생략 가능
    def fetch_items_to_update(self, limit:int)->List[Dict[str,Any]]:
        q="SELECT id,name,brand,price FROM items WHERE is_active=1 LIMIT ?"
        cur=self.conn.execute(q,(limit,))
        cols=[c[0] for c in cur.description]
        return [dict(zip(cols,row)) for row in cur.fetchall()]
    def update_item_pricing(self, item_id:int, metrics:Dict[str,Any]):
        now=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        q="""UPDATE items SET market_price_used_avg=?, market_price_used_p50=?,
        discount_vs_used_avg=?, discount_vs_used_p50=?, last_pricing_updated_at=? WHERE id=?"""
        self.conn.execute(q,(metrics.get("used_avg"),metrics.get("used_p50"),
                             metrics.get("discount_vs_used_avg"),metrics.get("discount_vs_used_p50"),
                             now,item_id))

# === 서비스 ===============================================================
class PriceUpdater:
    def __init__(self, db: Optional[DB]=None):
        self.db=db or DB(DATABASE_URL)
        self.db.ensure_schema()
    def update_item_once(self,item:Dict[str,Any])->Dict[str,float]:
        q=extract_product_query(item["name"],brand=item.get("brand"))
        prices=joongna_search_prices(q)
        if len(prices)<5:
            serp=serp_search(q)
            prices.extend([ls.price_krw for ls in serp])
        used_avg,used_p50=summarize_used(prices)
        metrics={"used_avg":used_avg,"used_p50":used_p50}
        metrics.update(compute_discounts(item["price"],used_avg,used_p50))
        self.db.update_item_pricing(item["id"],metrics)
        return metrics
    def run_batch(self,limit:int=UPDATE_BATCH_LIMIT)->List[Dict[str,Any]]:
        items=self.db.fetch_items_to_update(limit)
        return [{"id":it["id"],**self.update_item_once(it)} for it in items]

# === CLI =================================================================
if __name__=="__main__":
    import argparse,sys
    ap=argparse.ArgumentParser()
    ap.add_argument("--limit",type=int,default=UPDATE_BATCH_LIMIT)
    args=ap.parse_args()
    svc=PriceUpdater()
    try:
        res=svc.run_batch(limit=args.limit)
        sys.stdout.write(json.dumps(res,ensure_ascii=False,indent=2))
    except Exception as e:
        sys.stderr.write(f"[ERROR] {e}\n"); sys.exit(1)
