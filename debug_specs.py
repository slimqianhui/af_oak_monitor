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
        
        # Find OAK section - search backward from the button
        oak_button_idx = content.lower().find('view 1 apartment')
        if oak_button_idx == -1:
            oak_button_idx = content.lower().find('please call')
        
        # Go back to find the OAK floor plan title
        search_back = oak_button_idx
        oak_start = 0
        for i in range(5):
            temp_idx = content.lower().rfind('floorplan-title', 0, search_back)
            if temp_idx == -1:
                break
            temp_section = content[temp_idx:temp_idx+500]
            if 'oak' in temp_section.lower():
                oak_start = temp_idx
                break
            search_back = temp_idx - 1
        
        # The section goes from oak_start to next floor plan or button
        oak_section = content[oak_start:oak_button_idx]
        
        print(f"=== OAK Section Length: {len(oak_section)} chars ===\n")
        
        print("=== Searching for specs ===\n")
        
        # Extract specs
        bed_match = re.search(r'(\d+)\s*Beds?', oak_section, re.IGNORECASE)
        print(f"Beds: {bed_match.group(1) if bed_match else 'NOT FOUND'}")
        
        bath_match = re.search(r'(\d+)\s*Baths?', oak_section, re.IGNORECASE)
        print(f"Baths: {bath_match.group(1) if bath_match else 'NOT FOUND'}")
        
        sqft_match = re.search(r'(\d+)\s*Sq\.Ft', oak_section, re.IGNORECASE)
        print(f"SqFt: {sqft_match.group(1) if sqft_match else 'NOT FOUND'}")
        
        price_match = re.search(r'\$[\d,]+', oak_section, re.IGNORECASE)
        print(f"Price: {price_match.group(0) if price_match else 'NOT FOUND'}")
        
        # Try different price pattern
        price_match2 = re.search(r'Starting at:.*?\$[\d,]+', oak_section, re.IGNORECASE | re.DOTALL)
        if price_match2:
            price_text = price_match2.group(0)
            price_text = re.sub(r'<[^>]+>|<!--.*?-->', '', price_text)
            print(f"Price (full): {price_text.strip()}")

asyncio.run(debug())
