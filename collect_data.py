"""
YGA Sports — Amazon Competitor Data Collector
Uses curl_cffi to impersonate a real Chrome browser — works from cloud servers.
"""

import argparse
import json
import random
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from curl_cffi import requests as crequests
from bs4 import BeautifulSoup

# ─── CONFIG ───────────────────────────────────────────────────────────────────
DATA_FILE = Path(__file__).parent / "competitor_history.json"
TODAY     = str(date.today())

ASINS = [
    # ── Silent Basketball ──────────────────────────────────────────────────
    {"asin": "B0GWMKX9YG", "brand": "YGA Sports",       "group": "Silent Basketball", "is_mine": True},
    {"asin": "B0DS25MK1T", "brand": "ALDWDY",            "group": "Silent Basketball"},
    {"asin": "B0FBQX1GCR", "brand": "Muted Motion",      "group": "Silent Basketball"},
    {"asin": "B0F6L9LJL9", "brand": "LKTNLKT",           "group": "Silent Basketball"},
    {"asin": "B0FLJK2HWQ", "brand": "BOUNOVA",           "group": "Silent Basketball"},
    {"asin": "B0G2G8NQ3Y", "brand": "BYYNNE",            "group": "Silent Basketball"},
    # ── PUNCHO ────────────────────────────────────────────────────────────
    {"asin": "B0F6T2XLZR", "brand": "YGA Sports PUNCHO", "group": "PUNCHO", "is_mine": True},
    {"asin": "B0BKPM69F8", "brand": "Dino QPAU",         "group": "PUNCHO"},
    {"asin": "B0D6QT1WYS", "brand": "Red QPAU",          "group": "PUNCHO"},
    {"asin": "B0DFMMFMYC", "brand": "360 QPAU",          "group": "PUNCHO"},
    {"asin": "B0FHW391BS", "brand": "HopeRock",          "group": "PUNCHO"},
    {"asin": "B09JVGBFKH", "brand": "MARWAN",            "group": "PUNCHO"},
    # ── CHOMPY ────────────────────────────────────────────────────────────
    {"asin": "B0GNTJ9THL", "brand": "YGA Sports CHOMPY", "group": "CHOMPY", "is_mine": True},
    {"asin": "B0BKPM69F8", "brand": "Dino QPAU",         "group": "CHOMPY"},
    {"asin": "B0D6QT1WYS", "brand": "Red QPAU",          "group": "CHOMPY"},
    {"asin": "B0DFMMFMYC", "brand": "360 QPAU",          "group": "CHOMPY"},
    {"asin": "B0FS1341NF", "brand": "NIBBaNACAL",        "group": "CHOMPY"},
    {"asin": "B09JVGBFKH", "brand": "MARWAN",            "group": "CHOMPY"},
]

# ─── HTML PARSERS ─────────────────────────────────────────────────────────────
def _extract_bsr(soup) -> int | None:
    # Search any table row whose th/td contains "Best Sellers Rank"
    for row in soup.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) >= 2 and "Best Sellers Rank" in cells[0].get_text():
            m = re.search(r"#([\d,]+)", cells[1].get_text())
            if m:
                return int(m.group(1).replace(",", ""))
    # Fallback: search any list item
    for li in soup.find_all("li"):
        text = li.get_text(" ", strip=True)
        if "Best Sellers Rank" in text:
            m = re.search(r"#([\d,]+)", text)
            if m:
                return int(m.group(1).replace(",", ""))
    return None


def _extract_price(soup) -> float | None:
    for sel in [
        "#corePriceDisplay_desktop_feature_div .a-price",
        "#apex_desktop .a-price",
        "#price_inside_buybox",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        ".a-price",
    ]:
        el = soup.select_one(sel)
        if el:
            text = el.get_text(strip=True).replace(",", "")
            m = re.search(r"(\d+\.\d+)", text)
            if m:
                return float(m.group(1))
    return None


def _extract_rating(soup) -> float | None:
    el = soup.select_one("#acrPopover")
    if el:
        m = re.search(r"([\d.]+)", el.get("title", ""))
        if m:
            return float(m.group(1))
    el = soup.select_one("span.a-icon-alt")
    if el:
        m = re.search(r"([\d.]+)", el.get_text())
        if m:
            return float(m.group(1))
    return None


def _extract_reviews(soup) -> int | None:
    el = soup.select_one("#acrCustomerReviewText")
    if el:
        m = re.search(r"([\d,]+)", el.get_text())
        if m:
            return int(m.group(1).replace(",", ""))
    return None


def _extract_oos(soup) -> bool:
    avail = soup.select_one("#availability")
    if avail:
        text = avail.get_text(strip=True).lower()
        if any(w in text for w in ["unavailable", "out of stock", "cannot"]):
            return True
    return False


def _empty_snapshot() -> dict:
    return {
        "date": TODAY, "bsr_main": None, "bsr_subcategory": None,
        "subcategory_name": None, "bsr_subcats": {}, "buy_box_price": None,
        "rating": None, "review_count": None, "is_oos": False,
    }

# ─── SCRAPER ──────────────────────────────────────────────────────────────────
def scrape_asin(session, asin: str, brand: str) -> dict:
    url = f"https://www.amazon.com/dp/{asin}?th=1&psc=1"
    print(f"  >> {brand} ({asin})")

    for attempt in range(3):
        try:
            resp = session.get(url, timeout=30, allow_redirects=True)
        except Exception as e:
            if attempt < 2:
                print(f"     Error, retrying... ({e})")
                time.sleep(random.uniform(5, 10))
                continue
            print(f"     Failed: {e}")
            return _empty_snapshot()

        if resp.status_code != 200:
            if attempt < 2:
                print(f"     HTTP {resp.status_code}, retrying...")
                time.sleep(random.uniform(5, 10))
                continue
            print(f"     HTTP {resp.status_code}, skipping.")
            return _empty_snapshot()

        soup = BeautifulSoup(resp.text, "html.parser")

        if soup.find("form", {"action": "/errors/validateCaptcha"}):
            if attempt < 2:
                wait = random.uniform(15, 25)
                print(f"     CAPTCHA, waiting {wait:.0f}s and retrying ({attempt+1}/3)...")
                time.sleep(wait)
                continue
            print("     CAPTCHA not resolved, skipping.")
            return _empty_snapshot()

        bsr    = _extract_bsr(soup)
        price  = _extract_price(soup)
        rating = _extract_rating(soup)
        reviews = _extract_reviews(soup)
        is_oos  = _extract_oos(soup)

        parts = []
        if bsr:    parts.append(f"BSR #{bsr:,}")
        if price:  parts.append(f"${price:.2f}")
        if is_oos: parts.append("OOS")
        print(f"     OK  {' | '.join(parts) or 'no data found'}")

        return {
            "date": TODAY, "bsr_main": bsr, "bsr_subcategory": None,
            "subcategory_name": None, "bsr_subcats": {}, "buy_box_price": price,
            "rating": rating, "review_count": reviews, "is_oos": is_oos,
        }

    return _empty_snapshot()

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
    data["asins"][asin]["snapshots"] = [
        s for s in data["asins"][asin]["snapshots"] if s["date"] != TODAY
    ]
    data["asins"][asin]["snapshots"].append(snapshot)

# ─── ALERTS ───────────────────────────────────────────────────────────────────
def print_alerts(data: dict):
    print("\n--- ALERTS ---------------------------------------------------")
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
            if recent and week_ago and (recent - week_ago) / week_ago * 100 >= 25:
                pct = (recent - week_ago) / week_ago * 100
                print(f"[!] [{group_name}] Your BSR worsened {pct:.0f}% ({week_ago:,} -> {recent:,})")
                found = True
        for item in members:
            if item.get("is_mine"):
                continue
            snaps = data["asins"].get(item["asin"], {}).get("snapshots", [])
            if len(snaps) >= 8:
                today_p = snaps[-1]["buy_box_price"]
                avg7 = sum(s["buy_box_price"] for s in snaps[-8:-1] if s["buy_box_price"]) / max(
                    1, sum(1 for s in snaps[-8:-1] if s["buy_box_price"]))
                if today_p and avg7 and (avg7 - today_p) / avg7 * 100 >= 10:
                    pct = (avg7 - today_p) / avg7 * 100
                    print(f"[?] [{group_name}] {item['brand']} dropped price {pct:.0f}% (${avg7:.2f} -> ${today_p:.2f})")
                    found = True
    if not found:
        print("[OK] No alerts today.")
    print("--------------------------------------------------------------\n")

# ─── GIT PUSH ─────────────────────────────────────────────────────────────────
def _git_push():
    repo = Path(__file__).parent
    try:
        subprocess.run(["git", "add", "competitor_history.json"], cwd=repo, check=True)
        result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo)
        if result.returncode == 0:
            print("[i]  No changes to push (data unchanged).\n")
            return
        subprocess.run(["git", "commit", "-m", f"data: {TODAY}"], cwd=repo, check=True)
        subprocess.run(["git", "pull", "--rebase", "--autostash"], cwd=repo, check=True)
        subprocess.run(["git", "push"], cwd=repo, check=True)
        print("[OK] Pushed to GitHub - dashboard updated.\n")
    except subprocess.CalledProcessError as e:
        print(f"[!]  Git push failed: {e}\n")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true", help="Ignored — kept for backwards compatibility")
    parser.add_argument("--no-push",  action="store_true", help="Skip git push (used by GitHub Actions)")
    args = parser.parse_args()

    print(f"\n{'='*55}")
    print(f"  YGA Competitor Tracker - {TODAY}")
    print(f"{'='*55}\n")

    data = load_history()

    # Skip if already collected valid data today
    if not args.no_push:
        already = sum(
            1 for asin_data in data["asins"].values()
            for s in asin_data["snapshots"]
            if s["date"] == TODAY and s["bsr_main"] is not None
        )
        if already >= 10:
            print(f"[OK] Already have data for {TODAY} ({already} ASINs). Skipping.\n")
            return

    seen, to_fetch = {}, []
    for item in ASINS:
        if item["asin"] not in seen:
            seen[item["asin"]] = item
            to_fetch.append(item)

    session = crequests.Session(impersonate="chrome124")
    session.headers.update({
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    })
    session.cookies.set("i18n-prefs", "USD",   domain=".amazon.com")
    session.cookies.set("lc-main",    "en_US", domain=".amazon.com")

    print("  [warm-up] Visiting amazon.com...")
    try:
        session.get("https://www.amazon.com", timeout=15)
        time.sleep(random.uniform(3, 6))
        print("  [warm-up] Done.\n")
    except Exception:
        print("  [warm-up] Skipped.\n")

    failed = []
    for item in to_fetch:
        snapshot = scrape_asin(session, item["asin"], item["brand"])
        for meta in ASINS:
            if meta["asin"] == item["asin"]:
                append_snapshot(data, meta, dict(snapshot))
        save_history(data)
        if snapshot["bsr_main"] is None and snapshot["buy_box_price"] is None:
            failed.append(item)
        time.sleep(random.uniform(4, 8))

    if failed:
        print(f"\n  [retry] {len(failed)} ASINs got no data, retrying after warm session...")
        time.sleep(random.uniform(10, 15))
        for item in failed:
            snapshot = scrape_asin(session, item["asin"], item["brand"])
            for meta in ASINS:
                if meta["asin"] == item["asin"]:
                    append_snapshot(data, meta, dict(snapshot))
            save_history(data)
            time.sleep(random.uniform(4, 8))

    print_alerts(data)
    print(f"[OK] Done. Data saved to {DATA_FILE}\n")
    if not args.no_push:
        _git_push()


if __name__ == "__main__":
    main()
