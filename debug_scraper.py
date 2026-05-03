"""Diagnostic — prints exactly what each selector finds on the page."""
import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright

ASIN = "B0GWMKX9YG"   # YGA Silent Basketball
OUT  = Path(__file__).parent / "debug_output.txt"

async def main():
    lines = []
    def log(s=""):
        print(s.encode("ascii", "replace").decode())
        lines.append(s)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        await ctx.add_cookies([
            {"name": "i18n-prefs", "value": "USD",   "domain": ".amazon.com", "path": "/"},
            {"name": "lc-main",    "value": "en_US", "domain": ".amazon.com", "path": "/"},
        ])
        page = await ctx.new_page()
        url = f"https://www.amazon.com/dp/{ASIN}?th=1&psc=1"
        log(f"Loading: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        log(f"Final URL: {page.url}")

        # ── CAPTCHA? ──
        if "captcha" in page.url.lower():
            log("BLOCKED: CAPTCHA page")
            await browser.close()
            OUT.write_text("\n".join(lines))
            return

        # ── Page title ──
        log(f"Title: {await page.title()}")
        log()

        # ── BSR selectors ──
        log("=== BSR SELECTORS ===")
        bsr_selectors = [
            "#detailBulletsWrapper_feature_div",
            "#productDetails_db_sections",
            "#detailBullets_feature_div",
            "#productDetails_detailBullets_sections",
            "li:has-text('Best Sellers Rank')",
            "tr:has-text('Best Sellers Rank')",
            "#detailBullets_feature_div li",
        ]
        for sel in bsr_selectors:
            els = page.locator(sel)
            count = await els.count()
            log(f"\n[{sel}] → found: {count}")
            if count:
                text = await els.first.inner_text()
                log(f"  TEXT: {repr(text[:300])}")

        # ── Search for "Best Sellers Rank" anywhere ──
        log("\n=== FULL TEXT SEARCH FOR 'Best Sellers' ===")
        body = await page.locator("body").inner_text()
        idx = body.lower().find("best seller")
        if idx >= 0:
            log(f"Found at char {idx}: {repr(body[max(0,idx-20):idx+150])}")
        else:
            log("NOT FOUND in body text")

        # ── PRICE selectors ──
        log("\n=== PRICE SELECTORS ===")
        price_selectors = [
            "#corePriceDisplay_desktop_feature_div .a-offscreen",
            "#apex_desktop .a-offscreen",
            ".a-price .a-offscreen",
            "#priceblock_ourprice",
            "#price_inside_buybox",
            "#corePrice_feature_div .a-offscreen",
            ".priceToPay .a-offscreen",
        ]
        for sel in price_selectors:
            els = page.locator(sel)
            count = await els.count()
            if count:
                texts = []
                for i in range(min(count, 3)):
                    texts.append(repr(await els.nth(i).inner_text()))
                log(f"[{sel}] → {count} found: {', '.join(texts)}")

        await browser.close()

    OUT.write_text("\n".join(lines), encoding="utf-8")
    log(f"\nSaved to {OUT}")

asyncio.run(main())
