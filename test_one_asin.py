"""Quick test — scrape all 3 'mine' ASINs and print results."""
import asyncio, json, sys, io
from playwright.async_api import async_playwright
from collect_data import scrape_asin, ASINS

async def main():
    mine_asins = [a for a in ASINS if a.get("is_mine")]
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/New_York",
        )
        await ctx.add_cookies([
            {"name": "i18n-prefs", "value": "USD",   "domain": ".amazon.com", "path": "/"},
            {"name": "lc-main",    "value": "en_US", "domain": ".amazon.com", "path": "/"},
        ])
        page = await ctx.new_page()
        for item in mine_asins:
            print(f"\n=== {item['brand']} ({item['asin']}) ===")
            result = await scrape_asin(page, item["asin"], item["brand"])
            print(json.dumps(result, indent=2))
            await asyncio.sleep(2)
        await browser.close()

asyncio.run(main())
