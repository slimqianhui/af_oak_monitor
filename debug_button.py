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
        
        # Find OAK section
        text = content.lower()
        oak_idx = text.find('oak')
        
        # Look for next floor plan that's NOT oak
        search_start = oak_idx + 3
        next_plan_idx = len(content)
        for i in range(5):
            temp_idx = text.find('floorplan-title', search_start)
            if temp_idx == -1:
                break
            # Check if this is a different floor plan
            temp_section = content[temp_idx:temp_idx+500]
            if 'oak' not in temp_section.lower():
                next_plan_idx = temp_idx
                break
            search_start = temp_idx + 1
        
        oak_section = content[oak_idx:next_plan_idx]
        
        print(f"OAK section length: {len(oak_section)} chars\n")
        
        # Search in full content for the button pattern
        print("=== Searching entire content for primary-action button ===\n")
        
        # Find all primary-action buttons
        button_pattern = r'primary-action[^>]*>[^<]*<div[^>]*>[^<]*<div[^>]*class="v-btn__content"[^>]*>(.*?)</div>'
        matches = re.finditer(button_pattern, content, re.DOTALL | re.IGNORECASE)
        
        all_buttons = []
        for i, match in enumerate(matches):
            button_text = match.group(1)
            button_text = re.sub(r'<[^>]+>', '', button_text)
            button_text = button_text.strip()
            all_buttons.append((i, button_text))
            print(f"Button {i}: {button_text}\n")
        
        if not all_buttons:
            print("No buttons found with primary-action pattern\n")
            print("=== Searching for 'view' and 'please call' in content ===\n")
            for keyword in ['view apartment', 'please call', 'view 1 apartment']:
                if keyword in content.lower():
                    idx = content.lower().find(keyword)
                    start = max(0, idx - 300)
                    end = min(len(content), idx + 500)
                    print(f"Found '{keyword}' at position {idx}:")
                    print(content[start:end])
                    print("\n" + "="*80 + "\n")

asyncio.run(debug())

