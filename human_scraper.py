import asyncio
import random
import json
import sys
import re
import os
import traceback
import gc
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# Force UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def extract_all_listings(html):
    if not html or len(html) < 200: return []
    soup = BeautifulSoup(html, "html.parser")
    all_found_properties = []

    # Strategy 1: Find real property containers (More inclusive selectors)
    containers = soup.find_all(['div', 'form', 'tr', 'article', 'section'], 
        class_=re.compile(r'd-displayContainer|d-item|property-card|j-container|listing-item|item-container|result-item|listing-card', re.I))
    
    # Also look for role-based containers and generic matrix items
    role_containers = soup.find_all(['div', 'tr'], attrs={"role": ["listitem", "row"]})
    matrix_items = soup.find_all('div', id=re.compile(r'd-item', re.I))
    all_containers = containers + role_containers + matrix_items

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

async def perform_scrape(p_instance, url):
    ua = UserAgent()
    print("STATUS: Data-Hunter Engine active. Starting full-length scan...", file=sys.stderr)
    
    all_results = []
    
    browser = None
    try:
        browser = await p_instance.chromium.launch_persistent_context(
            user_data_dir=os.path.abspath("browser_profile"),
            headless=False, # Extensions ONLY work in non-headless mode
            args=[
                f"--disable-extensions-except={os.path.abspath('browser_ext/browsec')}",
                f"--load-extension={os.path.abspath('browser_ext/browsec')}",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        # 403 Stealth Retry Loop
        max_retries = 3
        success = False
        
        # 0. AUTOMATIC VPN ACTIVATION
        print("STATUS: Triggering Automatic VPN Shield...", file=sys.stderr)
        try:
            # Using the ID found on system: omghfjlpggmjjaagoclmmobgdodcjboh
            await page.goto("chrome-extension://omghfjlpggmjjaagoclmmobgdodcjboh/popup/popup.html", timeout=15000)
            await asyncio.sleep(5) 
            
            # Step 0: Bypass Terms & Conditions if present
            try:
                # The Accept button is an input[type='button'] inside the shadow root of first-start-agree-terms-conditions
                terms_accept = await page.query_selector("first-start-agree-terms-conditions >> input[type='button']")
                if terms_accept:
                    print("STATUS: Accepting VPN Terms & Conditions...", file=sys.stderr)
                    await terms_accept.click()
                    await asyncio.sleep(2)
            except: pass

            # Step 1: Handle Start Tips (Onboarding Tooltips)
            try:
                tips_close = await page.query_selector("first-start-tips-start-vpn >> .Close")
                if tips_close:
                    print("STATUS: Dismissing onboarding tips...", file=sys.stderr)
                    await tips_close.click()
                    await asyncio.sleep(1)
            except: pass

            # Step 2: Ensure Location is United States
            is_active = await page.query_selector("text=Your privacy is protected")
            is_us = await page.query_selector("text=United States")
            
            if is_active and is_us:
                print("STATUS: VPN Shield already active and set to United States.", file=sys.stderr)
            else:
                print("STATUS: Selecting United States location...", file=sys.stderr)
                # Try to open location list
                change_btn = await page.query_selector("text=Change")
                if not change_btn:
                    change_btn = await page.query_selector("active-country")
                
                if change_btn:
                    await change_btn.click()
                    await asyncio.sleep(2)
                    # Select US from list
                    us_option = await page.query_selector("text=United States")
                    if us_option:
                        await us_option.click()
                        await asyncio.sleep(5)
                
                # If not active yet, click the big button
                if not await page.query_selector("text=Your privacy is protected"):
                    start_btn = await page.query_selector("text=Protect me")
                    if start_btn:
                        await start_btn.click()
                        await asyncio.sleep(5)
            
            # Final verification
            if await page.query_selector("text=Your privacy is protected"):
                 print("STATUS: VPN Shield Secured.", file=sys.stderr)
            else:
                 print("WARNING: VPN Shield status uncertain.", file=sys.stderr)
            
            await asyncio.sleep(2)
        except Exception as vpn_e:
            print(f"WARNING: VPN Auto-Start failed: {str(vpn_e)}", file=sys.stderr)

        for attempt in range(max_retries):
            # We don't need proxy_pool anymore as we use the extension
            try:
                # 2. Automation Mask 
                await page.add_init_script("""() => {
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                }""")
                
                print(f"STATUS: Accessing Portal (Attempt {attempt+1} via VPN/Direct)...", file=sys.stderr)
                
                # Verify Location
                try:
                    ip_check = await page.goto("https://ipapi.co/json/", timeout=10000)
                    if ip_check and ip_check.status == 200:
                        ip_data = await ip_check.json()
                        print(f"STATUS: Verified Location: {ip_data.get('city')}, {ip_data.get('country_name')} (IP: {ip_data.get('ip')})", file=sys.stderr)
                except:
                    print("STATUS: Could not verify location via IP API, proceeding anyway...", file=sys.stderr)

                response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(random.uniform(2, 4))
                
                # Humanize: Move mouse around
                await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
                await asyncio.sleep(random.uniform(1, 2))

                if not response:
                    print(f"WARNING: No response from attempt {attempt+1}. Body might be empty.", file=sys.stderr)
                    await context.close()
                    continue

                print(f"DEBUG: Page Status: {response.status}", file=sys.stderr)
                
                if response.status == 402:
                    print(f"ERROR: Proxy returned 402 (Payment Required). Rotating...", file=sys.stderr)
                    continue
                
                # 3. Block Detection & Content Verification
                page_content = await page.content()
                page_title = await page.title()
                
                # REFINED BLOCK DETECTION: Check for both status codes AND body text
                is_blocked = (response.status == 403 or 
                              "Forbidden" in page_content or 
                              "Access Denied" in page_content or 
                              "security challenge" in page_content.lower())
                
                if is_blocked:
                    print(f"WARNING: Attempt {attempt+1} blocked (403/Security). Rotating proxy...", file=sys.stderr)
                    await context.close()
                    continue
                
                # Check for "Empty" results vs "Blocked" results
                if "No results matching" in page_content or "No properties found" in page_content:
                     print(f"INFO: Portal reached. Page says: '{page_title}'. Search actually seems empty.", file=sys.stderr)
                
                success = True
                break
            except Exception as e:
                print(f"DEBUG: Attempt {attempt+1} fail: {str(e)}", file=sys.stderr)
                await asyncio.sleep(2)

        if not success:
            raise Exception("The portal is currently blocking all attempts. Check your proxies or wait.")

        # Verification step: ensure frames exist
        await asyncio.sleep(6)

        all_results = []
        
        print("STATUS: Initiating Persistent Data Mining Scan...", file=sys.stderr)
        await page.mouse.move(1000, 500)
        await page.mouse.click(1000, 500)

        for i in range(12): # Reduced from 30 for RAM safety
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
            # Only check frames if memory isn't too tight; keep it simple
            if len(page.frames) < 5:
                for frame in page.frames:
                    if frame == page.main_frame: continue
                    try:
                        f_html = await frame.content()
                        if len(f_html) > 500: snap_html += "\n" + f_html
                    except: continue
            
            new_listings = extract_all_listings(snap_html)
            
            # Help GC
            snap_html = None
            gc.collect()
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
            if i % 3 == 0: print(f"STATUS: Mining Stage {i+1}/20 (Found: {len(all_results)} listings)...", file=sys.stderr)
            if i >= 9: break # Cap at 10 stages for memory safety
            if len(all_results) >= 50: break # Result cap for RAM safety

        print(f"STATUS: Finalizing {len(all_results)} listings...", file=sys.stderr)
        return all_results

    except Exception as e:
        err_msg = str(e)
        print(f"ERROR Cache: {err_msg}", file=sys.stderr)
        # If the browser crashed (Page crashed / Target closed) but we found results, return them!
        if all_results and len(all_results) > 0:
            print(f"WARNING: Browser crashed or timed out, but salvaged {len(all_results)} listings.", file=sys.stderr)
            return all_results
        
        print(f"ERROR Details: {traceback.format_exc()}", file=sys.stderr)
        return []
    finally:
        if browser: await browser.close()

async def main():
    try:
        url = sys.argv[1] if len(sys.argv) > 1 else ""
        if not url: return
        async with async_playwright() as p:
            # VPN is handled inside perform_scrape via Browsec extension
            results = await perform_scrape(p, url)
            if results and isinstance(results, list):
                print(json.dumps({"success": True, "count": len(results), "data": results[0], "all_data": results}))
            else:
                print(json.dumps({"error": "No properties found.", "debug": "Check server logs for title/content snippets."}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    asyncio.run(main())
