import asyncio
import json
import os
import smtplib
from email.mime.text import MIMEText
from playwright.async_api import async_playwright

URL = "https://www.ardenwoodforest.com/apartments/ca/fremont/floor-plans#/"

# ===== Email Config =====
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = os.environ["SENDER_EMAIL"]
SENDER_PASSWORD = os.environ["SENDER_PASSWORD"]

# Multiple emails supported:
# example:
# a@gmail.com,b@gmail.com
RECEIVER_EMAIL = os.environ["RECEIVER_EMAIL"]

# ===== Local state =====
STATE_FILE = "known_units.json"


async def fetch_oak_available():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        page = await browser.new_page()

        print("Opening website...")

        await page.goto(URL, wait_until="networkidle")

        # Wait for dynamic content
        await page.wait_for_timeout(3000)

        # Click "View All Floor Plans" button to expand hidden floor plans
        try:
            view_all_buttons = await page.locator('button:has-text("View All"), a:has-text("View All")').all()
            for button in view_all_buttons:
                text = await button.text_content()
                if "view all" in text.lower() and "floor" in text.lower():
                    print("Clicking 'View All Floor Plans' button...")
                    await button.click()
                    await page.wait_for_timeout(2000)
                    break
        except Exception as e:
            print(f"Note: Could not click 'View All' button: {e}")

        # Now look for the OAK section and click on it to expand details
        try:
            print("Looking for OAK floor plan...")
            oak_title = await page.locator("text=Oak").first.locator("..")
            await oak_title.scroll_into_view_if_needed()
            await page.wait_for_timeout(500)
            
            # Click on the OAK card to expand it
            oak_card = await page.locator(".floorplan").filter(has=page.locator("text=Oak")).first
            await oak_card.click()
            await page.wait_for_timeout(1000)
        except Exception as e:
            print(f"Note: Could not click OAK card: {e}")

        content = await page.content()

        await browser.close()

    text = content.lower()

    if "oak" not in text:
        print("OAK floor plan not found.")
        return []

    # Find all CTA buttons and their corresponding floor plans
    import re
    
    # Pattern to find floor plan title + button combo
    oak_button_pattern = r'floorplan-title[^>]*>.*?<p[^>]*class="floorplan-title-title[^>]*>\s*Oak\s*</p>.*?cta-btn[^>]*>.*?<div[^>]*class="v-btn__content"[^>]*>(.*?)</div>'
    
    match = re.search(oak_button_pattern, content, re.DOTALL | re.IGNORECASE)
    
    if not match:
        print("OAK floor plan not found.")
        return []
    
    button_text = match.group(1)
    # Clean HTML
    button_text = re.sub(r'<[^>]+>', '', button_text)
    button_text = button_text.strip()
    
    print(f"OAK Button Text: {button_text}")
    
    # Check button status
    button_lower = button_text.lower()
    if "please call" in button_lower:
        print("OAK floor plan: No availability")
        return []
    elif "view" in button_lower and "apartment" in button_lower:
        print(f"OAK floor plan: {button_text}")
        
        # Extract OAK section details - look specifically after the OAK title and before the button
        oak_title_pattern = r'floorplan-title[^>]*>.*?<p[^>]*class="floorplan-title-title[^>]*>\s*Oak\s*</p>(.*?)cta-btn'
        oak_match = re.search(oak_title_pattern, content, re.DOTALL | re.IGNORECASE)
        
        if oak_match:
            oak_details = oak_match.group(1)
            
            # Extract specs: beds, baths, sqft, price
            specs = []
            
            # Find bed info
            bed_match = re.search(r'(\d+)\s*Beds?', oak_details, re.IGNORECASE)
            if bed_match:
                specs.append(f"{bed_match.group(1)} Bed{'s' if int(bed_match.group(1)) > 1 else ''}")
            
            # Find bath info
            bath_match = re.search(r'(\d+)\s*Baths?', oak_details, re.IGNORECASE)
            if bath_match:
                specs.append(f"{bath_match.group(1)} Bath{'s' if int(bath_match.group(1)) > 1 else ''}")
            
            # Find sqft info
            sqft_match = re.search(r'(\d+)\s*Sq\.Ft', oak_details, re.IGNORECASE)
            if sqft_match:
                specs.append(f"{sqft_match.group(1)} Sq.Ft")
            
            # Find price info
            price_match = re.search(r'Starting at:.*?\$[\d,]+', oak_details, re.IGNORECASE | re.DOTALL)
            if price_match:
                price_text = price_match.group(0)
                price_text = re.sub(r'<[^>]+>|<!--.*?-->', '', price_text)
                price_text = re.sub(r'\s+', ' ', price_text).strip()
                specs.append(price_text)
            
            if specs:
                print(f"  Details: {' | '.join(specs)}")
        
        # Return the button text (e.g., "View 1 Apartment" or "View 2 Apartments")
        return [button_text]
    else:
        print(f"OAK floor plan: Unknown status - {button_text}")
        return []


def load_known():
    if not os.path.exists(STATE_FILE):
        return []

    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_known(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)


def send_email(units):
    body = "OAK floor plan may now be available.\n\n"

    for unit in units:
        body += f"- {unit}\n"

    body += f"\nCheck here:\n{URL}"

    msg = MIMEText(body)

    msg["Subject"] = "OAK Apartment Available"
    msg["From"] = SENDER_EMAIL

    receivers = [
        x.strip()
        for x in RECEIVER_EMAIL.split(",")
        if x.strip()
    ]

    msg["To"] = ", ".join(receivers)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()

        server.login(
            SENDER_EMAIL,
            SENDER_PASSWORD
        )

        server.sendmail(
            SENDER_EMAIL,
            receivers,
            msg.as_string()
        )

    print("Email notification sent!")


async def main():
    current = await fetch_oak_available()

    if not current:
        print("No availability found.")
        return

    known = load_known()

    new_units = [
        x for x in current
        if x not in known
    ]

    if new_units:
        print("New availability detected!")

        send_email(new_units)

        updated = list(set(known + new_units))

        save_known(updated)

    else:
        print("No new units detected.")


if __name__ == "__main__":
    asyncio.run(main())