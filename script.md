# Bright MLS Stealth Scraper: Complete Setup & Code Guide

This document outlines the complete procedure, architecture, and source code for the **Bright MLS Stealth Scraper**. This system uses a hybrid approach (Node.js + Python + Playwright) to bypass advanced bot detection and extract property data from top to bottom.

---

## 🛠️ 1. Prerequisites & Installation

Before running the script, you must install the following dependencies on your Windows machine:

### A. Install Python Dependencies
Open your terminal (PowerShell) and run:
```powershell
pip install playwright beautifulsoup4 fake-useragent
playwright install chromium
```

### B. Install Node.js Dependencies
In your project folder (`c:\Users\UMAR\Desktop\Python`), run:
```powershell
npm install express cors
```

---

## 📂 2. Project Structure
To function correctly, ensure the following files are in the same folder:
1. `mls_scraper.html` (The Web Interface)
2. `scraper_server.js` (The Node.js Backend Bridge)
3. `human_scraper.py` (The Python Extraction Engine)
4. `Webshare 10 proxies.txt` (Your proxy list)

---

## 🛡️ 3. Proxy Configuration
Create a file named `Webshare 10 proxies.txt` in the same directory. Paste your Webshare proxies in this exact format:
```text
ip:port:username:password
ip:port:username:password
... (up to 10)
```

---

## 🖥️ 4. The Source Code

### A. Frontend: `mls_scraper.html`
This is your modern UI for controlling the scraper.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MLS Property Extractor</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #030712;
            --card: #111827;
            --accent: #6366f1;
            --accent-glow: rgba(99, 102, 241, 0.2);
            --text: #f9fafb;
            --text-muted: #9ca3af;
            --success: #10b981;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Plus Jakarta Sans', sans-serif; 
            background: var(--bg); 
            color: var(--text);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            padding: 40px 20px;
        }

        .container {
            width: 100%;
            max-width: 800px;
        }

        header { text-align: center; margin-bottom: 40px; }
        h1 { font-size: 2.5rem; font-weight: 800; margin-bottom: 10px; background: linear-gradient(to right, #818cf8, #c084fc); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
        p { color: var(--text-muted); }

        .search-box {
            background: var(--card);
            padding: 30px;
            border-radius: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
            margin-bottom: 30px;
        }

        .mode-toggle {
            display: flex;
            background: rgba(255, 255, 255, 0.05);
            padding: 4px;
            border-radius: 10px;
            margin-bottom: 20px;
            width: fit-content;
        }

        .mode-btn {
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: 0.2s;
            color: var(--text-muted);
        }

        .mode-btn.active {
            background: var(--accent);
            color: white;
        }

        .input-group {
            display: flex;
            gap: 12px;
        }

        .manual-input {
            display: none;
            flex-direction: column;
            gap: 12px;
        }

        textarea {
            width: 100%;
            height: 120px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 16px;
            border-radius: 12px;
            color: white;
            font-family: inherit;
            resize: none;
            outline: none;
        }

        textarea:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 4px var(--accent-glow);
        }

        input {
            flex: 1;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 16px 20px;
            border-radius: 12px;
            color: white;
            font-size: 1rem;
            outline: none;
            transition: 0.2s;
        }

        input:focus {
            border-color: var(--accent);
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 0 4px var(--accent-glow);
        }

        button {
            background: var(--accent);
            color: white;
            border: none;
            padding: 0 30px;
            border-radius: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: 0.2s;
        }

        button.main-btn {
            height: 54px;
        }

        button:hover { opacity: 0.9; transform: translateY(-1px); }
        button:disabled { opacity: 0.5; cursor: not-allowed; }

        .results {
            display: none;
            animation: fadeIn 0.4s ease-out;
        }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        .property-header {
            background: linear-gradient(135deg, #1e1b4b, #111827);
            padding: 24px;
            border-radius: 20px;
            border: 1px solid rgba(99, 102, 241, 0.2);
            margin-bottom: 20px;
        }

        .price { font-size: 2rem; font-weight: 800; color: var(--success); }
        .addr { font-size: 1.1rem; color: var(--text-muted); margin-top: 4px; }

        .details-grid {
            display: grid;
            grid-template-columns: 1fr; /* Stacked for better readability */
            gap: 12px;
        }

        .detail-item {
            background: var(--card);
            padding: 16px;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
        .value { font-weight: 600; }

        .loader {
            display: none;
            text-align: center;
            padding: 40px;
        }

        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid rgba(99, 102, 241, 0.1);
            border-top: 4px solid var(--accent);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }

        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>MLS Scraper</h1>
            <p>Paste a Bright MLS link or HTML code to extract all building data</p>
        </header>

        <div class="search-box">
            <div class="mode-toggle">
                <div class="mode-btn active" id="btn-auto" onclick="setMode('auto')">Python Engine (Auto)</div>
                <div class="mode-btn" id="btn-manual" onclick="setMode('manual')">Paste HTML</div>
            </div>

            <div id="auto-group" class="input-group" style="flex-direction: column; gap: 15px;">
                <input type="text" id="mls-url" placeholder="Paste Link..." value="https://matrix.brightmls.com/DAE.asp?ID=0-6721608503-10&eml=c2FsZXNAdXBvbnRoZXJvb2ZzLmNvbQ==" style="width: 100%;">
                
                <div style="display: flex; flex-direction: column; gap: 10px; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 8px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <input type="checkbox" id="use-proxy" style="width: auto; height: auto; cursor: pointer;">
                        <label for="use-proxy" style="font-size: 0.85rem; cursor: pointer; color: var(--accent);">Use Webshare High-Quality Proxies</label>
                    </div>
                </div>
                
                <button class="main-btn" id="scrape-btn" onclick="startScrape()" style="width: 100%;">Start Human-Like Extraction</button>
            </div>

            <div id="manual-group" class="manual-input">
                <p style="font-size: 0.8rem; margin-bottom: 8px; color: var(--accent);">Use this if the Auto Scan keeps failing</p>
                <p style="font-size: 0.8rem; margin-bottom: 8px;">1. Open link in browser. 2. Ctrl+U (View Source). 3. Copy/Paste code here.</p>
                <textarea id="mls-html" placeholder="Paste HTML Source Code here..." style="height: 200px;"></textarea>
                <button class="main-btn" onclick="processManualHtml()" style="margin-top: 10px;">Process HTML Manually</button>
            </div>
        </div>

        <div class="loader" id="loader">
            <div class="spinner"></div>
            <p id="loader-text">Scanning property details... hold on tight.</p>
        </div>

        <div class="results" id="results">
            <div class="details-grid" id="res-grid">
                <!-- Items injected here -->
            </div>
        </div>
    </div>

    <script>
        let currentMode = 'auto';

        function setMode(mode) {
            currentMode = mode;
            document.getElementById('btn-auto').classList.toggle('active', mode === 'auto');
            document.getElementById('btn-manual').classList.toggle('active', mode === 'manual');
            document.getElementById('auto-group').style.display = mode === 'auto' ? 'flex' : 'none';
            document.getElementById('manual-group').style.display = mode === 'manual' ? 'flex' : 'none';
        }

        function displayData(data) {
            const grid = document.getElementById('res-grid');
            grid.innerHTML = ''; 

            const rawListings = data.all_data || [data.data]; 
            
            const listings = rawListings.filter(p => 
                p.price !== "$0" && 
                p.address.toLowerCase() !== "address" && 
                p.address.toLowerCase() !== "check source"
            );

            listings.forEach(prop => {
                const card = document.createElement('div');
                card.className = 'property-header'; 
                card.style.marginBottom = "20px";
                card.innerHTML = `
                    <div class="price">${prop.price}</div>
                    <div class="addr">${prop.address}</div>
                    <div style="font-size: 0.8rem; color: #9ca3af; margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 5px;">
                        <div><b>MLS:</b> ${prop.mls}</div>
                        <div><b>Status:</b> ${prop.status}</div>
                        <div><b>Type:</b> ${prop.type}</div>
                        <div><b>Beds/Baths:</b> ${prop.beds || 'N/A'} / ${prop.baths || 'N/A'}</div>
                        <div><b>City:</b> ${prop.city}</div>
                        <div><b>SqFt:</b> ${prop.sqft}</div>
                    </div>
                `;
                grid.appendChild(card);
            });

            document.getElementById('results').style.display = 'block';
        }

        async function startScrape() {
            const url = document.getElementById('mls-url').value;
            const useProxy = document.getElementById('use-proxy').checked;
            
            if (!url) return alert("Please enter a URL");

            const btn = document.getElementById('scrape-btn');
            const loader = document.getElementById('loader');
            const lText = document.getElementById('loader-text');
            const results = document.getElementById('results');

            btn.disabled = true;
            results.style.display = 'none';
            loader.style.display = 'block';
            lText.innerHTML = "Verifying Webshare Proxies... <br><span style='font-size:0.7rem; color:var(--accent)'>This takes ~45s to bypass advanced security.</span>";

            try {
                const response = await fetch('http://localhost:3005/scrape', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url, useProxy })
                });

                const data = await response.json();
                if (data.status === "error" || data.error) throw new Error(data.message || data.error);
                if (data && data.success && data.all_data) {
                    displayData(data);
                } else {
                    throw new Error("Received invalid data structure from server");
                }
            } catch (err) {
                alert("Scrape Failed: " + err.message);
            } finally {
                btn.disabled = false;
                loader.style.display = 'none';
            }
        }

        function processManualHtml() {
            const html = document.getElementById('mls-html').value;
            if (!html) return alert("Please paste HTML source code");

            try {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, "text/html");
                const text = doc.body.innerText;

                const mlsRegex = /([A-Z]{4}\d{7})/g;
                const matches = [...text.matchAll(mlsRegex)];
                
                if (matches.length === 0) throw new Error("No MLS numbers found.");

                const all_data = matches.map((match, index) => {
                    const mls = match[0];
                    const start = Math.max(0, match.index - 500);
                    const end = index + 1 < matches.length ? matches[index + 1].index : text.length;
                    const block = text.substring(start, end);

                    const priceMatch = block.match(/\$\d{1,3}(,\d{3})*(\.\d{2})?/);
                    
                    const addrMatch = block.match(/(\d{1,5}\s+[A-Z0-9\.\s-]{3,40}(St|Rd|Ave|Blvd|Dr|Ln|Way|Ct|Pl|Cir|Cambr|Pike|Hwy)[^$]*)/i);
                    let address = addrMatch ? addrMatch[1].split("$")[0].trim() : 'Address in Source';
                    
                    address = address.replace(/^\d{4}\s*[-–—\s]+/g, '').trim();
                    address = address.replace(/(Residential|3Beds|\w+Beds).*$/i, '').trim();

                    const statusMatch = block.match(/(Coming Soon|Active Under Contract|Active|Pending|Closed|Withdrawn)/i);
                    const bedsMatch = block.match(/(?:Beds\s*:?\s*|(\d+)\s*Beds)(\d+)?/i);
                    const bathsMatch = block.match(/(?:Baths\s*:?\s*|(\d+\/?\d*)\s*Baths)(\d+\/?\d*)?/i);
                    const sqftMatch = block.match(/(?:SQFT\s*:?\s*|([\d,]+)\s*SqFt)([\d,]+)?/i);

                    return {
                        price: priceMatch ? priceMatch[0] : 'N/A',
                        address: address,
                        mls: mls,
                        status: statusMatch ? statusMatch[0] : 'Pending',
                        type: 'Residential',
                        city: 'Philadelphia, PA',
                        sqft: sqftMatch ? (sqftMatch[1] || sqftMatch[2]) : 'N/A',
                        beds: bedsMatch ? (bedsMatch[1] || bedsMatch[2]) : 'N/A',
                        baths: bathsMatch ? (bathsMatch[1] || bathsMatch[2]) : 'N/A',
                        sender: 'Manual Import'
                    };
                });

                const unique = Array.from(new Set(all_data.map(p => p.mls))).map(mls => all_data.find(p => p.mls === mls));
                displayData({ all_data: unique });
            } catch (err) {
                alert("Processing Error: " + err.message);
            }
        }
    </script>
</body>
</html>
```

### B. Backend: `scraper_server.js`
This Node.js server acts as the bridge between your website and the Python engine.

```javascript
import express from 'express';
import cors from 'cors';
import { exec } from 'child_process';
import util from 'util';

const execPromise = util.promisify(exec);
const app = express();
app.use(cors());
app.use(express.json());

const PORT = 3005;

app.get('/', (req, res) => {
    res.send(`
        <div style="font-family: sans-serif; text-align: center; padding: 50px; background: #0f172a; color: white; height: 100vh;">
            <h1 style="color: #8b5cf6;">🚀 Scraper Server is Online</h1>
            <p>This server handles the Python extraction engine.</p>
            <p>Please open <b>mls_scraper.html</b> in your browser to use the app.</p>
        </div>
    `);
});

app.post('/scrape', async (req, res) => {
    const { url, useProxy } = req.body;
    if (!url) return res.status(400).json({ error: "URL is required" });

    console.log(`📡 Delegating scrape to Python Engine: ${url}`);
    
    try {
        let command = `python human_scraper.py "${url}"`;
        if (useProxy) command += " --proxy";
        
        const { stdout, stderr } = await execPromise(command, { timeout: 120000 });
        
        if (stderr && !stdout) return res.status(500).json({ error: "Python Engine Error: " + stderr });

        const jsonMatch = stdout.match(/\{.*\}/s);
        if (!jsonMatch) return res.status(500).json({ error: "Failed to parse Python response" });

        const result = JSON.parse(jsonMatch[0]);
        if (result.error) return res.status(500).json({ error: result.error });

        res.json(result);

    } catch (err) {
        res.status(500).json({ status: "error", message: "Engine Failure: " + err.message });
    }
});

app.listen(PORT, () => {
    console.log(`\n================================`);
    console.log(`  Hybrid Python-Node Scraper`);
    console.log(`  Running at http://localhost:3005`);
    console.log(`================================\n`);
});
```

### C. Extraction Engine: `human_scraper.py`
The "brain" of the scraper that uses Playwright with Ultra-Stealth technology.

```python
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
    file_path = "Webshare 10 proxies.txt"
    if not os.path.exists(file_path): return proxies
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line: continue
                parts = line.split(":")
                if len(parts) >= 4:
                    proxies.append({
                        "server": f"http://{parts[0]}:{parts[1]}",
                        "username": parts[2],
                        "password": parts[3]
                    })
    except: pass
    return proxies

def extract_all_listings(html):
    if not html or len(html) < 200: return []
    soup = BeautifulSoup(html, "html.parser")
    all_found_properties = []
    containers = soup.find_all(class_=re.compile(r'd-displayContainer|d-item|d-form|property-card', re.I))
    
    if not containers or len(containers) < 2:
        text = soup.get_text(" \n ", strip=True)
        mls_matches = list(re.finditer(r'MLS\s*#?\s*:\s*([A-Z]{4}\d{7})', text, re.I))
        if mls_matches:
            blocks = []
            for i in range(len(mls_matches)):
                lookback = 1000 if i == 0 else 400
                start = max(0, mls_matches[i].start() - lookback)
                end = mls_matches[i+1].start() if i+1 < len(mls_matches) else len(text)
                blocks.append(text[start:end])
            for block in blocks:
                all_found_properties.extend(parse_text_block(block))
    else:
        for area in containers:
            area_text = area.get_text(" ", strip=True)
            all_found_properties.extend(parse_text_block(area_text))

    unique_list = []
    seen = set()
    for p in all_found_properties:
        if p['mls'] in seen or p['price'] == "$0" or p['address'].lower() == "address": continue
        unique_list.append(p)
        seen.add(p['mls'])
    return unique_list

def parse_text_block(text):
    price_match = re.search(r'\$\d{1,3}(,\d{3})*(\.\d{2})?', text)
    if not price_match or "$0" == price_match.group(0): return []
    price_val = price_match.group(0)
    mls_match = re.search(r'([A-Z]{4}\d{7})', text)
    if not mls_match: return []

    def find_pattern(patterns, source=text):
        for p in patterns:
            m = re.search(p, source, re.I)
            if m: return m.group(1).strip()
        return "N/A"

    address = find_pattern([
        r'(\d{1,5}\s+[A-Z0-9\.\s-]{3,40}(St|Rd|Ave|Blvd|Dr|Ln|Way|Ct|Pl|Cir|Cambr|Pike|Hwy)\s*,?\s*[A-Z\s]{4,20}\s*,\s*PA\s+\d{5})',
        r'(\d{1,5}\s+[A-Z0-9\.\s-]{3,40}(St|Rd|Ave|Blvd|Dr|Ln|Way|Ct|Pl|Cir|Cambr))'
    ])
    if address != "N/A":
        address = address.split("$")[0].strip()
        address = re.sub(r'^\d{4}\s*[-–—\s]+', '', address).strip()

    status = find_pattern([r'(Coming Soon|Active Under Contract|Active|Pending|Closed|Withdrawn)'])
    beds = find_pattern([r'(\d+)\s*Beds', r'Beds\s*:?\s*(\d+)'])
    baths = find_pattern([r'(\d+/?\d*)\s*Baths', r'Baths\s*:?\s*(\d+/?\d*)'])
    sqft = find_pattern([r'([\d,]+)\s*SqFt', r'SQFT\s*:?\s*([\d,]+)'])

    prop_data = {
        "subject": "Single Family Listing",
        "sender": "AJ Cerullo", 
        "price": price_val,
        "type": "Residential" if "Residential" in text else find_pattern([r'Property Type\s*:\s*(\w+)'], text),
        "address": address if len(address) > 5 else "Address in Source",
        "city": "Philadelphia, PA",
        "sqft": sqft,
        "mls": mls_match.group(1),
        "status": status if status != "N/A" else "Active",
        "beds": beds,
        "baths": baths
    }
    if prop_data['price'] == "$0" or prop_data['address'].lower() == "address": return []
    return [prop_data]

async def perform_scrape(p_instance, url, proxy_config=None):
    ua = UserAgent()
    print("STATUS: Data-Hunter Engine active. Starting full-length scan...", file=sys.stderr)
    browser = await p_instance.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled", "--no-sandbox"], proxy=proxy_config)

    try:
        context = await browser.new_context(user_agent=ua.chrome)
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = await context.new_page()
        page.set_default_timeout(60000)
        try: await page.goto(url, wait_until="networkidle", timeout=60000)
        except: print("STATUS: Network idle timed out, proceeding...", file=sys.stderr)

        all_results = []
        seen_mls = set()
        print("STATUS: Performing Deep Sweep from Top to Bottom...", file=sys.stderr)
        
        for i in range(15):
            current_html = await page.content()
            for frame in page.frames:
                try: current_html += await frame.content()
                except: continue
            
            new_listings = extract_all_listings(current_html)
            for listing in new_listings:
                if listing['mls'] not in seen_mls:
                    all_results.append(listing)
                    seen_mls.add(listing['mls'])

            await page.mouse.wheel(0, 1500)
            await asyncio.sleep(1.5)
            if i % 5 == 0: print(f"STATUS: Scanned position {i+1}/15. Found {len(all_results)} listings...", file=sys.stderr)

        if all_results:
            print(f"STATUS: Sweep complete! Total Unique Listings: {len(all_results)}", file=sys.stderr)
            await asyncio.sleep(2)
            await browser.close()
            return all_results
        await browser.close()
        return []
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        if browser: await browser.close()
        return []

async def main():
    try:
        if len(sys.argv) < 2: return
        url = sys.argv[1]
        use_proxy = "--proxy" in sys.argv
        async with async_playwright() as p:
            proxy_pool = load_webshare_proxies() if use_proxy else []
            if proxy_pool: random.shuffle(proxy_pool)
            proxy = proxy_pool[0] if use_proxy and proxy_pool else None
            results = await perform_scrape(p, url, proxy)
            if results: print(json.dumps({"success": True, "count": len(results), "data": results[0], "all_data": results}))
            else: print(json.dumps({"error": "No property data detected."}))
    except Exception: print(json.dumps({"error": "Engine Fail"}))

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🚀 5. How to Run the Scraper

### Step 1: Start the Backend Server
Open PowerShell in your folder and run:
```powershell
node scraper_server.js
```

### Step 2: Open the Interface
1. Right-click `mls_scraper.html` in your folder.
2. Select **"Open with Live Server"** (or just double-click to open in Chrome).

### Step 3: Start Scraping
1. Paste your **Bright MLS Link**.
2. Check the box **"Use Webshare High-Quality Proxies"**.
3. Click **"Start Human-Like Extraction"**.

---

## 📡 6. Direct API Usage (cURL)

You can also trigger a scrape directly from your terminal or another application by sending a POST request to the local server.

### Example cURL Command:
Open a new PowerShell or Command Prompt and run:

```bash
curl -X POST http://localhost:3005/scrape `
     -H "Content-Type: application/json" `
     -d '{"url": "YOUR_BRIGHT_MLS_LINK_HERE", "useProxy": true}'
```

*(Note: Replace `YOUR_BRIGHT_MLS_LINK_HERE` with your actual MLS portal URL. If using standard Command Prompt, remove the backticks `` ` `` and put the command on one line.)*

---

## 🌍 7. Deploying to Render.com (Online Hosting)

Since Bright MLS requires a real browser, we use **Docker** to deploy this to Render.com as a **Web Service**.

### Step 1: Prepare your Code
Ensure you have the following files in your folder (I have already created them for you):
*   `Dockerfile`
*   `.dockerignore`
*   `package.json` (with `"start"` script)
*   `scraper_server.js` (configured to use `$PORT`)

### Step 2: Push to GitHub
1.  Create a new repository on [GitHub](https://github.com).
2.  Upload all your files from `c:\Users\UMAR\Desktop\Python` to that repository. (Do not upload `node_modules`).

### Step 3: Deploy on Render
1.  Log in to [dashboard.render.com](https://dashboard.render.com).
2.  Click **"New +"** -> **"Web Service"**.
3.  Connect your GitHub repository.
4.  **Configuration**:
    *   **Name**: `mls-scraper`
    *   **Runtime**: Select **"Docker"** (Important!)
    *   **Region**: Select the one closest to you.
    *   **Instance Type**: The "Free" tier might be too slow for Playwright; if it crashes, consider the **"Starter ($7/mo)"** plan for actual scraping work.
5.  Click **"Deploy Web Service"**.

### Step 4: Use it!
Once the deployment is finished, Render will give you a URL like `https://mls-scraper.onrender.com`.
You can open this link in any browser on your phone or computer to use the scraper.

---

## 🚀 8. Deploying to Hugging Face Spaces (BEST Performance - 16GB RAM)

Since scraping requires a lot of memory, Hugging Face is the best **Free** option because it gives you a massive **16GB of RAM**.

### Step 1: Set up the Space
1.  Go to [huggingface.co/spaces](https://huggingface.co/spaces) and log in.
2.  Click **"Create new Space"**.
3.  **Owner**: Your username.
4.  **Space Name**: `mls-data-hunter`
5.  **SDK**: Select **"Docker"** -> **"Blank"**.
6.  **Public/Private**: Select your preference.
7.  Click **"Create Space"**.

### Step 2: Upload Files (Web Method)
1.  On your new Space page, click the **"Files"** tab at the top.
2.  Click **"Add file"** -> **"Upload files"**.
3.  Drag and drop the following files from your folder:
    *   `Dockerfile`
    *   `scraper_server.js`
    *   `human_scraper.py`
    *   `mls_scraper.html`
    *   `package.json`
    *   `Webshare 10 proxies.txt`
4.  Type a commit message like "Initial upload" and click **"Commit changes to main"**.

### Step 3: Wait for Build
1.  Click the **"App"** tab at the top.
2.  You will see a log while Hugging Face builds your Docker container.
3.  Once it says **"Running"**, your scraper is live!

### Step 4: Access your URL
Your app will be embedded in the Hugging Face page. To get the "Direct Link":
1.  Click the **"⋮" (three dots)** at the top right of the App view.
2.  Click **"Embed this Space"**.
3.  Copy the **"Direct URL"**.
