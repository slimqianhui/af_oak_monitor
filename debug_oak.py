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
            view_all_buttons = await page.locator('button:has-text("View All"), a:has-text("View All")').all()
            for button in view_all_buttons:
                text = await button.text_content()
                if 'view all' in text.lower() and 'floor' in text.lower():
                    print("Clicking View All Floor Plans...")
                    await button.click()
                    await page.wait_for_timeout(2000)
                    break
        except Exception as e:
            print(f"Could not click button: {e}")
        
        content = await page.content()
        await browser.close()
        
        # Extract OAK floor plans using regex
        oak_pattern = r'floorplan-title[^>]*>.*?<p[^>]*class="floorplan-title-title[^>]*>.*?Oak.*?</p>.*?<p[^>]*class="floorplan-title-meta[^>]*>(.*?)</p>.*?Starting at:.*?<span[^>]*class="subheading[^>]*>(.*?)</span>'
        
        matches = re.finditer(oak_pattern, content, re.DOTALL | re.IGNORECASE)
        
        entries = []
        for i, match in enumerate(matches, 1):
            meta = match.group(1)
            price = match.group(2)
            
            # Clean up meta info
            meta_clean = re.sub(r'<[^>]+>', '', meta)
            meta_clean = ' | '.join(x.strip() for x in meta_clean.split() if x.strip())
            
            # Clean up price
            price_clean = re.sub(r'<[^>]+>|<!--.*?-->', '', price).strip()
            
            entries.append(f'OAK Unit {i}: {meta_clean} - Price: {price_clean}')
        
        print('\n=== OAK Floor Plans Available ===\n')
        if entries:
            for entry in entries:
                print(entry)
        else:
            print('No OAK units found with this pattern')
        
        # Also check for "Please Call"
        if "please call" in content.lower():
            oak_idx = content.lower().find("oak")
            next_plan = content.lower().find("floor plan", oak_idx + 3)
            if next_plan == -1:
                next_plan = len(content)
            
            oak_section = content[oak_idx:next_plan].lower()
            if "please call" in oak_section:
                print("\nNote: OAK section contains 'Please Call' - may indicate no availability")

asyncio.run(debug())
