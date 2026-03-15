import asyncio
import random
import json
import sys
import re
import os
import traceback
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# Force UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def load_webshare_proxies():
    proxies = []
    # Check Environment Variable first (For Render/Docker)
    env_proxies = os.environ.get("PROXY_LIST")
    
    lines = []
    if env_proxies:
        lines = env_proxies.strip().split("\n")
    else:
        # Fallback to local file
        file_path = "Webshare 10 proxies.txt"
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding='utf-8') as f:
                    lines = f.readlines()
            except: pass

    for line in lines:
        line = line.strip()
        if not line or ":" not in line: continue
        parts = line.split(":")
        if len(parts) >= 4:
            proxies.append({
                "server": f"http://{parts[0]}:{parts[1]}",
                "username": parts[2],
                "password": parts[3]
            })
    return proxies
def extract_all_listings(html):
    if not html or len(html) < 200: return []
    soup = BeautifulSoup(html, "html.parser")
    all_found_properties = []

    # Strategy 1: Find real property containers (More inclusive selectors)
    containers = soup.find_all(['div', 'form', 'tr', 'article'], 
        class_=re.compile(r'd-displayContainer|d-item|property-card|j-container|listing-item|item-container', re.I))
    
    # Also look for role-based containers
    role_containers = soup.find_all('div', attrs={"role": "listitem"})
    all_containers = containers + role_containers

    for container in all_containers:
        block_text = container.get_text("\n", strip=True)
        if "$" in block_text:
            prop = parse_text_block(block_text)
            if prop: all_found_properties.extend(prop)
    
    # Strategy 2: Always run Fallback Anchor-Split to capture anything missed by containers
    full_text = soup.get_text("\n", strip=True)
    if "$" in full_text:
        # Split specifically by prices to create separate windows for each listing
        parts = re.split(r'(\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', full_text)
        for i in range(1, len(parts), 2):
            # Combine price and content up to the next price
            window = parts[i] + parts[i+1]
            prop = parse_text_block(window)
            if prop: all_found_properties.extend(prop)

    # FINAL DEDUP: High-Resolution Signature
    unique_list = []
    seen_sigs = set()
    for p in all_found_properties:
        clean_addr = re.sub(r'[^a-z0-9]', '', p['address'].lower())
        sig = f"{p['price']}_{clean_addr}"
        if sig in seen_sigs or p['price'] == "$0" or len(p['address']) < 4: continue
        unique_list.append(p)
        seen_sigs.add(sig)
    
    return unique_list

def parse_text_block(text):
    # Anchor: Price
    price_match = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
    if not price_match: return []
    price_val = price_match.group(0)
    
    # Anchor: MLS
    mls_match = re.search(r'([A-Z]{3,4}\d{7})', text)
    mls_val = mls_match.group(1) if mls_match else f"MLS-TBD-{random.randint(1000,9999)}"

    # REFINED ADDRESS SCANNER: Surgical Precision Logic
    address = "Address Pending"
    
    # 1. Primary: Match from Bullet (•) until City/Type/Price marker
    bullet_pattern = r'(?:•|·)\s*([^\n$|]{5,100}?(?=Philadelphia|Residential|Beds|bd|Baths|ba|\$))'
    addr_match = re.search(bullet_pattern, text, re.I)
    
    if not addr_match:
        # 2. Fallback: Search for Number + Street pattern after price
        standard_pattern = r'(\d{1,6}[\d-]*\s+[A-Z0-9\s\.\-#,]{2,70}?(?=Philadelphia|Residential|Beds|bd|Baths|ba|\$))'
        addr_match = re.search(standard_pattern, text, re.I)

    if addr_match:
        address = addr_match.group(1).strip()
    
    # ADVANCED NOISE REDUCTION: Strip years, garage info, and description garbage
    if address != "Address Pending":
        # 1. Surgical Trim: Find the REAL start (Digit + Space + Capital Letter)
        # This cuts off noise like "1925 - - " or "1925 Attached Garage..."
        trim_match = re.search(r'(\d{1,6}[\d-]*\s+[A-Z].*)', address)
        if trim_match:
            address = trim_match.group(1).strip()
        
        # 2. Handle common Matrix separators like " - - " or " - " if still present
        if " - - " in address:
            address = address.split(" - - ")[-1].strip()
        
        # 3. Split by known noise words and price/city markers
        address = re.split(r'Philadelphia|Residential|Beds|bd|Baths|ba|\$|\||\s{2,}', address, flags=re.I)[0].strip()
        
        # 4. Final price/symbol sweep
        address = re.sub(r'\$\d{1,3}(,\d{3})*(\.\d{2})?', '', address).strip()
        address = re.sub(r'^[^a-zA-Z0-9#]+', '', address).strip()

    # Noise Shield: Absolute Trash Filter
    noise_words = ["welcome", "listing", "spacious", "offer", "home", "beautiful", "acres", "filters", "criteria", "driveway"]
    if any(noise in address.lower() for noise in noise_words) or len(address) < 4:
        # Emergency Recovery: Look for digit + name + suffix
        recovery = re.search(r'(\d{1,6}\s+[A-Z][A-Za-z0-9\-\s]{1,30}?\s+(?:St|Rd|Ave|Blvd|Dr|Ln|Way|Ct|Pl|Cir|Pike|Hwy))', text)
        if recovery and not any(n in recovery.group(1).lower() for n in noise_words):
             address = recovery.group(1).strip()
        else:
            return []

    def find_safe(patterns):
        for p in patterns:
            m = re.search(p, text, re.I)
            if m: return m.group(1).strip() if m.groups() else m.group(0).strip()
        return "N/A"

    beds = find_safe([r'(\d+)\s*(?:Beds|bd)', r'Beds\s*:\s*(\d+)'])
    baths = find_safe([r'(\d+/?\d*)\s*(?:Baths|ba)', r'Baths\s*:\s*(\d+/?\d*)'])
    sqft = find_safe([r'([\d,]+)\s*(?:SqFt|Sq\s*Ft|sq\s*ft)', r'SqFt\s*:\s*([\d,]+)'])

    status = "Active"
    for kw in ["Pending", "Coming Soon", "Active Under Contract", "Closed", "Withdrawn"]:
        if kw.lower() in text[:400].lower():
            status = kw
            break

    if address == "Address Pending" or len(address) < 4: return []

    return [{
        "subject": "Single Family Listing",
        "sender": "AJ Cerullo", 
        "price": price_val,
        "type": "Residential",
        "address": address,
        "city": "Philadelphia, PA" if "philadelphia" in text.lower() else "Local",
        "sqft": sqft,
        "mls": mls_val,
        "status": status,
        "beds": beds,
        "baths": baths
    }]

def clean_address_string(address):
    if not address: return "Address Pending"
    address = re.split(r'Philadelphia|Residential|\||\$|\d+\s*(?:beds|bd|baths|ba)', address, flags=re.I)[0].strip()
    address = re.sub(r'^[^a-zA-Z0-9#]+', '', address).strip()
    return address

async def perform_scrape(p_instance, url, proxy_config=None):
    ua = UserAgent()
    print("STATUS: Data-Hunter Engine active. Starting full-length scan...", file=sys.stderr)
    is_server = "SPACE_ID" in os.environ or "RENDER" in os.environ
    
    browser = None
    try:
        browser = await p_instance.chromium.launch(
            headless=True if is_server else False, 
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage", "--no-zygote"], 
            proxy=proxy_config
        )

        context = await browser.new_context(user_agent=ua.chrome)
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = await context.new_page()
        await page.set_viewport_size({"width": 1280, "height": 900})
        
        print(f"STATUS: Accessing Portal...", file=sys.stderr)
        
        # 403 Stealth Retry Loop
        max_retries = 3
        success = False
        for attempt in range(max_retries):
            try:
                # 1. Advanced Stealth Context
                ua_str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                context = await browser.new_context(
                    user_agent=ua_str,
                    viewport={"width": random.randint(1280, 1920), "height": random.randint(720, 1080)},
                    device_scale_factor=1,
                    is_mobile=False,
                    has_touch=False
                )
                page = await context.new_page()
                
                # 2. Automation Mask: Wipe webdriver footprint
                await page.add_init_script("""() => {
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                }""")
                
                print(f"STATUS: Accessing Portal (Attempt {attempt+1})...", file=sys.stderr)
                response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(random.uniform(5, 8)) # Human jitter
                
                # 3. Block Detection
                page_content = await page.content()
                if response.status == 403 or "Forbidden" in page_content or "Access Denied" in page_content:
                    print(f"WARNING: Attempt {attempt+1} blocked (403). Changing fingerprint...", file=sys.stderr)
                    await context.close()
                    continue
                
                success = True
                break
            except Exception as e:
                print(f"DEBUG: Attempt {attempt+1} fail: {str(e)}", file=sys.stderr)
                await asyncio.sleep(2)

        if not success:
            raise Exception("The portal is currently blocking access (403 Forbidden). Try using a Proxy or wait a few minutes.")

        # Verification step: ensure frames exist
        await asyncio.sleep(5)

        all_results = []
        
        print("STATUS: Initiating Persistent Data Mining Scan...", file=sys.stderr)
        await page.mouse.move(1000, 500)
        await page.mouse.click(1000, 500)

        for i in range(30):
            # 1. Physical & JS Scroll
            await page.mouse.wheel(0, 1800)
            await page.evaluate("""() => {
                const els = Array.from(document.querySelectorAll('div, section, main')).filter(e => e.scrollHeight > e.clientHeight);
                els.forEach(e => { if(e.getBoundingClientRect().left > 400) e.scrollBy(0, 1500); });
                window.scrollBy(0, 1200);
            }""")

            # 2. Aggressive "See More" Probing (Clicks every stage if found)
            try:
                found_button = False
                for target in [page] + page.frames:
                    # Expanded selector list for all Bright MLS variants
                    selectors = [
                        "button:has-text('See More Results')", 
                        "a:has-text('See More Results')", 
                        "div.d-more", "a.d-more", 
                        "button.d-more", "[data-role='more-results']"
                    ]
                    for sel in selectors:
                        try:
                            btn = await target.query_selector(sel)
                            if btn and await btn.is_visible():
                                await btn.scroll_into_view_if_needed()
                                await btn.click()
                                found_button = True
                                print(f"STATUS: 'See More' clicked in {target.name or 'Main Frame'}. Expanding pool...", file=sys.stderr)
                                await asyncio.sleep(4) # Allow time for heavy content to load
                                break
                        except: continue
                    if found_button: break 
            except: pass

            # 3. Continuous Snapshot Capture (Captured every stage for 100% coverage)
            snap_html = await page.content()
            for frame in page.frames:
                try:
                    f_html = await frame.content()
                    if len(f_html) > 500: snap_html += "\n" + f_html
                except: continue
            
            new_listings = extract_all_listings(snap_html)
            all_results.extend(new_listings)
            
            # 4. Live Deduplication (High-Resolution Signature)
            unique_found = []
            seen_sigs = set()
            for r in all_results:
                clean_addr = re.sub(r'[^a-z0-9]', '', r['address'].lower())
                sig = f"{r['price']}_{clean_addr}"
                if sig not in seen_sigs:
                    unique_found.append(r)
                    seen_sigs.add(sig)
            all_results = unique_found
            
            await asyncio.sleep(0.5)
            if i % 3 == 0: print(f"STATUS: Mining Stage {i+1}/30 (Found: {len(all_results)} listings)...", file=sys.stderr)

        print(f"STATUS: Finalizing {len(all_results)} listings...", file=sys.stderr)
        return all_results

    except Exception as e:
        print(f"ERROR: {traceback.format_exc()}", file=sys.stderr)
        return []
    finally:
        if browser: await browser.close()

async def main():
    try:
        url = sys.argv[1] if len(sys.argv) > 1 else ""
        if not url: return
        use_proxy = "--proxy" in sys.argv
        
        async with async_playwright() as p:
            proxy_pool = load_webshare_proxies() if use_proxy else []
            proxy = random.choice(proxy_pool) if proxy_pool else None
            results = await perform_scrape(p, url, proxy)
            if results and isinstance(results, list):
                print(json.dumps({"success": True, "count": len(results), "data": results[0], "all_data": results}))
            else:
                print(json.dumps({"error": "No properties found."}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    asyncio.run(main())
