import express from 'express';
import cors from 'cors';
import { exec } from 'child_process';
import util from 'util';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const execPromise = util.promisify(exec);
const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 3005;

// Root endpoint: Serve the actual Scraper HTML UI
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'mls_scraper.html'));
});

// Health Check: Verify Python and Browser environment
app.get('/health', async (req, res) => {
    try {
        const pythonCmd = process.env.RAILWAY_ENVIRONMENT_ID || process.env.RENDER ? "python3" : "python";
        const { stdout } = await execPromise(`${pythonCmd} --version`);
        res.json({ status: "ok", python: stdout.trim(), env: process.env.RAILWAY_ENVIRONMENT_ID ? "Railway" : "Local" });
    } catch (err) {
        res.status(500).json({ status: "error", error: "Python not found", details: err.message });
    }
});

app.post('/scrape', async (req, res) => {
    // Increase response timeout for this specific long-running request
    req.setTimeout(300000); // 5 minutes

    const { url } = req.body;
    if (!url) return res.status(400).json({ error: "URL is required" });

    console.log(`\n--------------------------------`);
    console.log(`📡 Incoming Scrape Request [${new Date().toLocaleTimeString()}]:`);
    console.log(`🔗 URL: ${url}`);
    console.log(`--------------------------------\n`);

    try {
        // Use python3 for linux-based servers like Railway/Render
        const pythonCmd = process.env.RENDER || process.env.RAILWAY_ENVIRONMENT_ID ? "python3" : "python";
        let command = `${pythonCmd} human_scraper.py "${url}"`;

        console.log(`🚀 Launching Python Stealth Engine [${pythonCmd}]...`);
        const { stdout, stderr } = await execPromise(command, { timeout: 240000 });

        if (stderr && !stdout) {
            console.error("❌ Python Engine Error:", stderr);
            return res.status(500).json({ error: "Scrape Failed", details: stderr });
        }

        // Robust JSON extraction: Find the last valid JSON block in the output
        const lines = stdout.split('\n');
        let result = null;
        
        for (let i = lines.length - 1; i >= 0; i--) {
            const line = lines[i].trim();
            if (line.startsWith('{') && line.endsWith('}')) {
                try {
                    result = JSON.parse(line);
                    if (result.success || result.error || result.count !== undefined) {
                        break; 
                    }
                } catch (e) {
                    // Try to extract JSON from within the line if it's not a pure JSON line
                    const match = line.match(/\{.*\}/);
                    if (match) {
                        try {
                            result = JSON.parse(match[0]);
                            break;
                        } catch (innerE) {}
                    }
                }
            }
        }

        if (!result) {
            console.error("❌ Failed to parse Engine Output. Raw Output Snippet:", stdout.slice(-200));
            return res.status(500).json({ 
                error: "No valid data returned from scraper engine.",
                debug: stdout.length > 500 ? stdout.slice(-200) : stdout
            });
        }

        // Add ngrok bypass header to ensure the response gets through
        res.setHeader('ngrok-skip-browser-warning', 'true');

        if (result.error) {
            console.warn(`🛑 Scrape Blocked: ${result.error}`);
            if (result.error.includes("403") || result.error.includes("blocking")) {
                return res.status(403).json(result);
            }
            return res.status(500).json(result);
        }

        console.log(`✅ Success! [${new Date().toLocaleTimeString()}] Captured ${result.count} properties.`);
        res.json(result);

    } catch (err) {
        console.error("🔥 Execution Failure:", err.message);
        res.status(500).json({ error: "Connection Failed", details: err.message });
    }
});

const server = app.listen(PORT, () => {
    console.log(`\n================================`);
    console.log(`  Hybrid Python-Node Scraper`);
    console.log(`  Running at Port: ${PORT}`);
    console.log(`================================\n`);
});

// Set global timeout for the server to 5 minutes
server.timeout = 300000;
