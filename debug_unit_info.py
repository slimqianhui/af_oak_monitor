import asyncio
from playwright.async_api import async_playwright
import re

URL = 'https://www.ardenwoodforest.com/apartments/ca/fremont/floor-plans#/'

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # Click View All button
        try:
            buttons = await page.locator('button:has-text("View All"), a:has-text("View All")').all()
            for btn in buttons:
                text = await btn.text_content()
                if 'view all' in text.lower() and 'floor' in text.lower():
                    await btn.click()
                    await page.wait_for_timeout(2000)
                    break
        except:
            pass
        
        content = await page.content()
        await browser.close()
        
        # Find View 1 Apartment button and extract context
        idx = content.lower().find('view 1 apartment')
        if idx != -1:
            start = max(0, idx - 3000)
            end = min(len(content), idx + 200)
            
            print("=== Context around 'View 1 Apartment' (3000 chars before) ===\n")
            context = content[start:end]
            print(context)
            
            # Extract bed/bath/sqft info
            print("\n\n=== Extracted Unit Info ===\n")
            
            # Look for patterns like "2 Beds", "1 Bath", "961 Sq.Ft"
            patterns = [
                r'(\d+\s*Beds?)',
                r'(\d+\s*Baths?)',
                r'(\d+\s*Sq\.Ft)',
                r'Starting at:\s*\$[\d,]+',
                r'\$[\d,]+'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, context[-1000:], re.IGNORECASE)
                if match:
                    print(f"Found: {match.group(0)}")


asyncio.run(debug())
