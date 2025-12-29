from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from datetime import datetime, timezone
import uvicorn
from pathlib import Path
import traceback
import logging

from scraper import WebScraper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Universal Website Scraper")

# Serve static files for frontend
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

try:
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
except:
    pass

class ScrapeRequest(BaseModel):
    url: HttpUrl

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check called")
    return {"status": "ok"}

@app.post("/scrape")
async def scrape_url(request: ScrapeRequest):
    """
    Scrape a website and return structured JSON data
    """
    url = str(request.url)
    logger.info(f"Scraping URL: {url}")
    
    # Validate URL scheme
    if not url.startswith(('http://', 'https://')):
        logger.error(f"Invalid URL scheme: {url}")
        raise HTTPException(
            status_code=400, 
            detail="Only http(s) URLs are supported"
        )
    
    scraper = WebScraper()
    try:
        logger.info("Starting scrape...")
        result = await scraper.scrape(url)
        logger.info(f"Scrape completed. Sections found: {len(result.get('sections', []))}")
        return {"result": result}
    except Exception as e:
        logger.error(f"Scraping error: {str(e)}")
        logger.error(traceback.format_exc())
        # Return partial data with error
        return JSONResponse(
            status_code=200,
            content={
                "result": {
                    "url": url,
                    "scrapedAt": datetime.now(timezone.utc).isoformat(),
                    "meta": {
                        "title": "",
                        "description": "",
                        "language": "en",
                        "canonical": None
                    },
                    "sections": [],
                    "interactions": {
                        "clicks": [],
                        "scrolls": 0,
                        "pages": [url]
                    },
                    "errors": [
                        {
                            "message": str(e),
                            "phase": "scrape",
                            "traceback": traceback.format_exc()
                        }
                    ]
                }
            }
        )

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend HTML"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Universal Website Scraper</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .scraper-box {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }
        
        .input-group {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        input[type="text"] {
            flex: 1;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        button {
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #667eea;
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error {
            background: #fee;
            border-left: 4px solid #f44;
            padding: 15px;
            border-radius: 4px;
            margin-top: 15px;
        }
        
        .debug-info {
            background: #f0f0f0;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            font-family: monospace;
            font-size: 12px;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .results {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        
        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .results-header h2 {
            color: #333;
        }
        
        .download-btn {
            padding: 10px 20px;
            font-size: 14px;
        }
        
        .meta-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .meta-info h3 {
            margin-bottom: 10px;
            color: #667eea;
        }
        
        .meta-row {
            display: grid;
            grid-template-columns: 150px 1fr;
            gap: 10px;
            margin-bottom: 8px;
        }
        
        .meta-label {
            font-weight: 600;
            color: #666;
        }
        
        .section-item {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-bottom: 15px;
            overflow: hidden;
        }
        
        .section-header {
            padding: 15px;
            background: #f8f9fa;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s;
        }
        
        .section-header:hover {
            background: #e9ecef;
        }
        
        .section-title {
            font-weight: 600;
            color: #333;
        }
        
        .section-type {
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .section-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }
        
        .section-content.active {
            max-height: 2000px;
            transition: max-height 0.5s ease-in;
        }
        
        .json-viewer {
            background: #282c34;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.5;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Universal Website Scraper</h1>
            <p>Extract structured data from any website</p>
        </div>
        
        <div class="scraper-box">
            <div class="input-group">
                <input 
                    type="text" 
                    id="urlInput" 
                    placeholder="Enter website URL (e.g., https://en.wikipedia.org/wiki/Artificial_intelligence)"
                    value=""
                >
                <button id="scrapeBtn" onclick="scrapeWebsite()">Scrape Website</button>
            </div>
            
            <div id="loading" class="loading" style="display: none;">
                <div class="spinner"></div>
                <p>Scraping website... This may take a moment.</p>
            </div>
            
            <div id="error" class="error" style="display: none;"></div>
            <div id="debugInfo" class="debug-info" style="display: none;"></div>
        </div>
        
        <div id="results" class="results" style="display: none;">
            <div class="results-header">
                <h2>Scrape Results</h2>
                <button class="download-btn" onclick="downloadJSON()">📥 Download JSON</button>
            </div>
            
            <div class="stats" id="stats"></div>
            
            <div class="meta-info" id="metaInfo"></div>
            
            <div class="sections">
                <h3 style="margin-bottom: 15px; color: #333;">Sections</h3>
                <div id="sectionsList"></div>
            </div>
        </div>
    </div>
    
    <script>
        let currentData = null;
        
        async function scrapeWebsite() {
            const urlInput = document.getElementById('urlInput');
            const scrapeBtn = document.getElementById('scrapeBtn');
            const loading = document.getElementById('loading');
            const error = document.getElementById('error');
            const debugInfo = document.getElementById('debugInfo');
            const results = document.getElementById('results');
            
            const url = urlInput.value.trim();
            
            if (!url) {
                showError('Please enter a URL');
                return;
            }
            
            // Reset UI
            error.style.display = 'none';
            debugInfo.style.display = 'none';
            results.style.display = 'none';
            loading.style.display = 'block';
            scrapeBtn.disabled = true;
            
            console.log('Starting scrape for:', url);
            
            try {
                const startTime = Date.now();
                
                const response = await fetch('/scrape', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url: url })
                });
                
                const duration = Date.now() - startTime;
                console.log('Response received in', duration, 'ms');
                console.log('Status:', response.status);
                
                const data = await response.json();
                console.log('Data:', data);
                
                currentData = data.result;
                
                // Show debug info
                debugInfo.innerHTML = `
                    <strong>Debug Info:</strong><br>
                    Duration: ${duration}ms<br>
                    Status: ${response.status}<br>
                    Sections: ${data.result.sections.length}<br>
                    Errors: ${data.result.errors.length}<br>
                    ${data.result.errors.length > 0 ? '<br><strong>Errors:</strong><br>' + JSON.stringify(data.result.errors, null, 2) : ''}
                `;
                debugInfo.style.display = 'block';
                
                displayResults(data.result);
                
            } catch (err) {
                console.error('Fetch error:', err);
                showError('Failed to scrape website: ' + err.message);
                debugInfo.innerHTML = `<strong>Error Details:</strong><br>${err.stack || err.message}`;
                debugInfo.style.display = 'block';
            } finally {
                loading.style.display = 'none';
                scrapeBtn.disabled = false;
            }
        }
        
        function showError(message) {
            const error = document.getElementById('error');
            error.textContent = message;
            error.style.display = 'block';
        }
        
        function displayResults(data) {
            const results = document.getElementById('results');
            results.style.display = 'block';
            
            // Display stats
            const stats = document.getElementById('stats');
            stats.innerHTML = `
                <div class="stat-box">
                    <div class="stat-value">${data.sections.length}</div>
                    <div class="stat-label">Sections Found</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">${data.interactions.clicks.length}</div>
                    <div class="stat-label">Clicks Performed</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">${data.interactions.scrolls}</div>
                    <div class="stat-label">Scrolls</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">${data.interactions.pages.length}</div>
                    <div class="stat-label">Pages Visited</div>
                </div>
            `;
            
            // Display meta info
            const metaInfo = document.getElementById('metaInfo');
            metaInfo.innerHTML = `
                <h3>Metadata</h3>
                <div class="meta-row">
                    <div class="meta-label">Title:</div>
                    <div>${escapeHtml(data.meta.title)}</div>
                </div>
                <div class="meta-row">
                    <div class="meta-label">Description:</div>
                    <div>${escapeHtml(data.meta.description)}</div>
                </div>
                <div class="meta-row">
                    <div class="meta-label">Language:</div>
                    <div>${data.meta.language}</div>
                </div>
                <div class="meta-row">
                    <div class="meta-label">Strategy:</div>
                    <div>${data.meta.strategy || 'N/A'}</div>
                </div>
                <div class="meta-row">
                    <div class="meta-label">Scraped At:</div>
                    <div>${new Date(data.scrapedAt).toLocaleString()}</div>
                </div>
            `;
            
            // Display sections
            const sectionsList = document.getElementById('sectionsList');
            if (data.sections.length === 0) {
                sectionsList.innerHTML = '<p style="color: #999; padding: 20px; text-align: center;">No sections found</p>';
            } else {
                sectionsList.innerHTML = data.sections.map((section, index) => `
                    <div class="section-item">
                        <div class="section-header" onclick="toggleSection(${index})">
                            <div>
                                <div class="section-title">${escapeHtml(section.label)}</div>
                            </div>
                            <span class="section-type">${section.type}</span>
                        </div>
                        <div class="section-content" id="section-${index}">
                            <div class="json-viewer">${escapeHtml(JSON.stringify(section, null, 2))}</div>
                        </div>
                    </div>
                `).join('');
            }
        }
        
        function toggleSection(index) {
            const content = document.getElementById(`section-${index}`);
            content.classList.toggle('active');
        }
        
        function downloadJSON() {
            if (!currentData) return;
            
            const dataStr = JSON.stringify(currentData, null, 2);
            const blob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `scrape-${Date.now()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Allow Enter key to trigger scrape
        document.getElementById('urlInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                scrapeWebsite();
            }
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    logger.info("Starting Universal Website Scraper...")
    logger.info("Server will be available at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)