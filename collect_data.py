"""
YGA Sports — Amazon Competitor Data Collector
Runs daily, appends a snapshot to competitor_history.json.
"""

import argparse
import asyncio
import json
import random
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

# ─── CONFIG ───────────────────────────────────────────────────────────────────
DATA_FILE = Path(__file__).parent / "competitor_history.json"
TODAY     = str(date.today())

ASINS = [
    # ── Silent Basketball ──────────────────────────────────────────────────
    {"asin": "B0GWMKX9YG", "brand": "YGA Sports",    "group": "Silent Basketball", "is_mine": True},
    {"asin": "B0DS25MK1T", "brand": "ALDWDY",         "group": "Silent Basketball"},
    {"asin": "B0FBQX1GCR", "brand": "Muted Motion",   "group": "Silent Basketball"},
    {"asin": "B0F6L9LJL9", "brand": "LKTNLKT",        "group": "Silent Basketball"},
    {"asin": "B0FLJK2HWQ", "brand": "BOUNOVA",        "group": "Silent Basketball"},
    {"asin": "B0G2G8NQ3Y", "brand": "BYYNNE",         "group": "Silent Basketball"},
    # ── PUNCHO ────────────────────────────────────────────────────────────
    {"asin": "B0F6T2XLZR", "brand": "YGA Sports PUNCHO", "group": "PUNCHO", "is_mine": True},
    {"asin": "B0BKPM69F8", "brand": "Dino QPAU",      "group": "PUNCHO"},
    {"asin": "B0D6QT1WYS", "brand": "Red QPAU",       "group": "PUNCHO"},
    {"asin": "B0DFMMFMYC", "brand": "360 QPAU",       "group": "PUNCHO"},
    {"asin": "B0FHW391BS", "brand": "HopeRock",       "group": "PUNCHO"},
    {"asin": "B09JVGBFKH", "brand": "MARWAN",         "group": "PUNCHO"},
    # ── CHOMPY ────────────────────────────────────────────────────────────
    {"asin": "B0GNTJ9THL", "brand": "YGA Sports CHOMPY", "group": "CHOMPY", "is_mine": True},
    {"asin": "B0BKPM69F8", "brand": "Dino QPAU",      "group": "CHOMPY"},
    {"asin": "B0D6QT1WYS", "brand": "Red QPAU",       "group": "CHOMPY"},
    {"asin": "B0DFMMFMYC", "brand": "360 QPAU",       "group": "CHOMPY"},
    {"asin": "B0FS1341NF", "brand": "NIBBaNACAL",     "group": "CHOMPY"},
    {"asin": "B09JVGBFKH", "brand": "MARWAN",         "group": "CHOMPY"},
]

# ─── SCRAPER ──────────────────────────────────────────────────────────────────
async def scrape_asin(page, asin: str, brand: str) -> dict:
    url = f"https://www.amazon.com/dp/{asin}?th=1&psc=1"
    print(f"  >> {brand} ({asin})")

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(2_500)
    except PWTimeout:
        print(f"     TIMEOUT loading page")
        return _empty_snapshot()

    # ── CAPTCHA check ──────────────────────────────────────────────────────
    if await page.locator("form[action='/errors/validateCaptcha']").count():
        print("     CAPTCHA! Solve it in the browser window. Waiting 60s...")
        try:
            await page.wait_for_url(lambda u: "captcha" not in u, timeout=60_000)
            await page.wait_for_timeout(2_000)
        except PWTimeout:
            print("     CAPTCHA not solved in time, skipping.")
            return _empty_snapshot()

    # ── BSR ────────────────────────────────────────────────────────────────
    bsr_main    = None
    bsr_sub     = None
    sub_name    = None
    bsr_subcats = {}   # {"Basketballs": 51, "Focus Bags": 12, ...}

    # BSR lives in a table row on most Amazon pages
    bsr_text = ""
    for sel in [
        "tr:has-text('Best Sellers Rank') td",
        "tr:has-text('Best Sellers Rank')",
        "li:has-text('Best Sellers Rank')",
        "#detailBulletsWrapper_feature_div",
        "#productDetails_db_sections",
    ]:
        el = page.locator(sel).first
        if await el.count():
            candidate = await el.inner_text()
            if re.search(r"#[\d,]+", candidate):
                bsr_text = candidate
                break

    if bsr_text:
        matches = re.findall(r"#\s*([\d,]+)\s+in\s+([^\n#(]+)", bsr_text)
        if matches:
            bsr_main = int(matches[0][0].replace(",", ""))
            # Collect every subcategory rank (everything after the main rank)
            for rank_str, cat_name in matches[1:]:
                bsr_subcats[cat_name.strip()] = int(rank_str.replace(",", ""))
            # Legacy scalar fields: first subcategory found
            if bsr_subcats:
                sub_name = next(iter(bsr_subcats))
                bsr_sub  = bsr_subcats[sub_name]

    # ── PRICE ──────────────────────────────────────────────────────────────
    price = None
    price_selectors = [
        "#corePrice_feature_div .a-offscreen",
        ".priceToPay .a-offscreen",
        "#corePriceDisplay_desktop_feature_div .a-offscreen",
        ".a-price .a-offscreen",
        "#priceblock_ourprice",
        "#price_inside_buybox",
    ]
    for sel in price_selectors:
        els = page.locator(sel)
        count = await els.count()
        for i in range(count):
            raw = await els.nth(i).inner_text()
            raw = raw.replace(",", "").strip()
            m = re.search(r"\d+\.\d{2}", raw)
            if m:
                price = float(m.group())
                break
        if price:
            break

    # ── OOS ────────────────────────────────────────────────────────────────
    is_oos = False
    avail = page.locator("#availability span").first
    if await avail.count():
        avail_text = (await avail.inner_text()).lower()
        is_oos = any(w in avail_text for w in ["unavailable", "out of stock", "currently unavailable"])

    # ── RATING & REVIEWS ───────────────────────────────────────────────────
    rating       = None
    review_count = None
    rating_el = page.locator("#acrPopover").first
    if await rating_el.count():
        m = re.search(r"([\d.]+)\s+out", await rating_el.get_attribute("title") or "")
        if m:
            rating = float(m.group(1))
    review_el = page.locator("#acrCustomerReviewText").first
    if await review_el.count():
        m = re.search(r"([\d,]+)", await review_el.inner_text())
        if m:
            review_count = int(m.group(1).replace(",", ""))

    snapshot = {
        "date":             TODAY,
        "bsr_main":         bsr_main,
        "bsr_subcategory":  bsr_sub,
        "subcategory_name": sub_name,
        "bsr_subcats":      bsr_subcats,  # all subcategory ranks as dict
        "buy_box_price":    price,
        "rating":           rating,
        "review_count":     review_count,
        "is_oos":           is_oos,
    }

    status = []
    if bsr_main:  status.append(f"BSR #{bsr_main:,}")
    if price:     status.append(f"${price:.2f}")
    if is_oos:    status.append("OOS")
    print(f"     OK  {' | '.join(status) or 'no data found'}")
    return snapshot


def _empty_snapshot() -> dict:
    return {
        "date": TODAY, "bsr_main": None, "bsr_subcategory": None,
        "subcategory_name": None, "buy_box_price": None,
        "rating": None, "review_count": None, "is_oos": False,
    }

# ─── PERSISTENCE ──────────────────────────────────────────────────────────────
def load_history() -> dict:
    if DATA_FILE.exists():
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"asins": {}}


def save_history(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def append_snapshot(data: dict, asin_meta: dict, snapshot: dict):
    asin = asin_meta["asin"]
    if asin not in data["asins"]:
        data["asins"][asin] = {
            "brand":        asin_meta["brand"],
            "is_mine":      asin_meta.get("is_mine", False),
            "parent_group": asin_meta["group"],
            "snapshots":    [],
        }
    # Remove existing snapshot for today if re-running
    data["asins"][asin]["snapshots"] = [
        s for s in data["asins"][asin]["snapshots"] if s["date"] != TODAY
    ]
    data["asins"][asin]["snapshots"].append(snapshot)


# ─── ALERTS SUMMARY ───────────────────────────────────────────────────────────
def print_alerts(data: dict):
    print("\n─── ALERTS ──────────────────────────────────────────")
    found = False
    groups = {}
    for item in ASINS:
        groups.setdefault(item["group"], []).append(item)

    for group_name, members in groups.items():
        mine = next((m for m in members if m.get("is_mine")), None)
        if not mine:
            continue
        mine_snaps = data["asins"].get(mine["asin"], {}).get("snapshots", [])
        if len(mine_snaps) >= 7:
            recent   = mine_snaps[-1]["bsr_main"]
            week_ago = mine_snaps[-7]["bsr_main"]
            if recent and week_ago:
                pct = (recent - week_ago) / week_ago * 100
                if pct >= 25:
                    print(f"🔴  [{group_name}] Your BSR worsened {pct:.0f}% ({week_ago:,} → {recent:,})")
                    found = True
        for item in members:
            if item.get("is_mine"):
                continue
            snaps = data["asins"].get(item["asin"], {}).get("snapshots", [])
            if len(snaps) >= 8:
                today_p = snaps[-1]["buy_box_price"]
                avg7    = sum(s["buy_box_price"] for s in snaps[-8:-1]
                              if s["buy_box_price"]) / max(1, sum(
                              1 for s in snaps[-8:-1] if s["buy_box_price"]))
                if today_p and avg7 and (avg7 - today_p) / avg7 * 100 >= 10:
                    pct = (avg7 - today_p) / avg7 * 100
                    print(f"🟡  [{group_name}] {item['brand']} dropped price {pct:.0f}% (${avg7:.2f} → ${today_p:.2f})")
                    found = True
    if not found:
        print("✅  No alerts today.")
    print("─────────────────────────────────────────────────────\n")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true", help="Run browser headlessly (for scheduled tasks)")
    args = parser.parse_args()
    headless = args.headless

    print(f"\n{'='*55}")
    print(f"  YGA Competitor Tracker — {TODAY}")
    print(f"  Mode: {'headless' if headless else 'visible'}")
    print(f"{'='*55}\n")

    data = load_history()

    # Deduplicate ASINS list (some ASINs appear in 2 groups)
    seen     = {}
    to_fetch = []
    for item in ASINS:
        if item["asin"] not in seen:
            seen[item["asin"]] = item
            to_fetch.append(item)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars",
                "--window-size=1280,900",
            ],
        )
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/New_York",
        )
        # Force USD currency regardless of IP location
        await ctx.add_cookies([
            {"name": "i18n-prefs",  "value": "USD",    "domain": ".amazon.com", "path": "/"},
            {"name": "lc-main",     "value": "en_US",  "domain": ".amazon.com", "path": "/"},
        ])
        page = await ctx.new_page()

        for item in to_fetch:
            snapshot = await scrape_asin(page, item["asin"], item["brand"])
            # Add snapshot to all groups this ASIN belongs to
            for meta in ASINS:
                if meta["asin"] == item["asin"]:
                    append_snapshot(data, meta, dict(snapshot))
            save_history(data)           # save after each ASIN
            delay = random.uniform(6, 12)
            await asyncio.sleep(delay)

        await browser.close()

    print_alerts(data)
    print(f"✅  Done. Data saved to {DATA_FILE}\n")
    _git_push()


def _git_push():
    repo = Path(__file__).parent
    try:
        subprocess.run(["git", "add", "competitor_history.json"], cwd=repo, check=True)
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"], cwd=repo
        )
        if result.returncode == 0:
            print("ℹ️   No changes to push (data unchanged).\n")
            return
        subprocess.run(
            ["git", "commit", "-m", f"data: {TODAY}"],
            cwd=repo, check=True,
        )
        subprocess.run(["git", "push"], cwd=repo, check=True)
        print("✅  Pushed to GitHub — dashboard updated.\n")
    except subprocess.CalledProcessError as e:
        print(f"⚠️   Git push failed: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())
