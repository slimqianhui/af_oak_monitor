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
        await page.wait_for_timeout(8000)

        content = await page.content()

        await browser.close()

    text = content.lower()

    if "oak" not in text:
        print("OAK floor plan not found.")
        return []

    found = []

    lines = content.splitlines()

    capture = False

    for line in lines:
        lower = line.lower()

        if "oak" in lower:
            capture = True

        if capture:
            if (
                "available" in lower
                or "apply now" in lower
                or "unit" in lower
            ):
                clean_line = line.strip()

                if clean_line:
                    found.append(clean_line)

        # stop if another floor plan section begins
        if capture and "floor plan" in lower and "oak" not in lower:
            break

    unique = list(set(found))

    print(f"Found {len(unique)} possible available entries.")

    return unique


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