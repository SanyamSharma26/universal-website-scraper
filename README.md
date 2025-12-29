# Universal Website Scraper

A full-stack web scraping application that extracts structured data from any website, handling both static and JavaScript-rendered content.

## Features

- 🔍 **Universal Scraping**: Works with both static HTML and JavaScript-rendered pages
- 🤖 **Smart Fallback**: Automatically detects when JS rendering is needed
- 🎯 **Section-Aware Parsing**: Intelligently groups content into meaningful sections
- 🔄 **Interaction Support**: Handles tabs, "Load more" buttons, infinite scroll, and pagination
- 📊 **Structured Output**: Returns clean, well-structured JSON data
- 🎨 **Modern UI**: Clean, intuitive frontend for easy scraping
- 📥 **Export Capability**: Download scraped data as JSON

## Setup and Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Internet connection (for installing dependencies)

### Quick Start

1. Make the run script executable:
```bash
chmod +x run.sh
```

2. Run the application:
```bash
./run.sh
```

The script will:
- Create a virtual environment
- Install all dependencies
- Install Playwright browsers (Chromium)
- Start the server on `http://localhost:8000`

### Manual Setup (Alternative)

If you prefer to set up manually:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run the application
python main.py
```

## Usage

### Web Interface

1. Open your browser and navigate to `http://localhost:8000`
2. Enter a URL in the input field
3. Click "Scrape Website"
4. View the structured results
5. Download JSON if needed

### API Endpoints

#### Health Check
```bash
curl http://localhost:8000/healthz
```

Response:
```json
{
  "status": "ok"
}
```

#### Scrape URL
```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## Test URLs

The following URLs were used for testing and validation:

### 1. Wikipedia - Artificial Intelligence
**URL**: `https://en.wikipedia.org/wiki/Artificial_intelligence`

**Type**: Static HTML page

**Purpose**: Tests static scraping capabilities. Contains well-structured sections with headings, paragraphs, lists, tables, and images. Excellent for validating section extraction and metadata parsing.

**What it tests**:
- Static HTML parsing
- Section detection using landmarks (`<main>`, `<section>`)
- Metadata extraction (title, description, language, canonical)
- Content extraction (headings, text, links, images, lists, tables)
- Absolute URL conversion

### 2. Vercel Homepage
**URL**: `https://vercel.com/`

**Type**: JavaScript-heavy SPA with interactive elements

**Purpose**: Tests JS rendering capabilities and tab interactions. Contains dynamic content that requires JavaScript execution. Perfect for validating the static-to-JS fallback mechanism and click flow handling.

**What it tests**:
- JS rendering with Playwright
- Static-to-JS fallback detection
- Tab clicking (`[role="tab"]` elements)
- Network idle waiting
- Noise filtering (cookie banners, modals)
- Dynamic content extraction

### 3. Hacker News
**URL**: `https://news.ycombinator.com/`

**Type**: Paginated content (depth ≥ 3)

**Purpose**: Tests pagination handling. Contains "More" links at the bottom for navigating to additional pages. Validates the ability to follow links and aggregate content from multiple pages.

**What it tests**:
- Pagination link detection
- Following "Next" / "More" links
- Tracking visited pages
- Content aggregation across multiple pages
- Depth ≥ 3 navigation

## Architecture

### Technology Stack

- **Backend**: FastAPI (Python 3.10+)
- **Static Scraping**: httpx + selectolax
- **JS Rendering**: Playwright (Chromium)
- **Frontend**: Vanilla JavaScript with modern UI
- **Server**: uvicorn

### Core Components

1. **main.py**: FastAPI application with API endpoints and frontend serving
2. **scraper.py**: Core scraping logic with static and JS rendering capabilities
3. **Static scraping**: Fast HTML parsing for simple pages
4. **JS rendering**: Playwright-based rendering for complex SPAs

## Features Implemented

✅ Static HTML scraping  
✅ JavaScript rendering with Playwright  
✅ Smart fallback mechanism (static → JS)  
✅ Tab clicking support  
✅ "Load more" button clicking  
✅ Infinite scroll handling  
✅ Pagination (depth ≥ 3)  
✅ Section-aware content extraction  
✅ Metadata extraction (title, description, language, canonical)  
✅ Noise filtering (cookie banners, modals)  
✅ HTML truncation  
✅ Error handling and reporting  
✅ Interactive frontend UI  
✅ JSON download capability  

## Known Limitations

1. **Authentication**: Cannot access pages behind login walls
2. **Rate Limiting**: Some sites may block automated requests
3. **Complex SPAs**: Very complex single-page applications may require site-specific handling
4. **Dynamic Content**: Some lazy-loaded content may not be captured
5. **Anti-bot Protection**: Sites with aggressive bot detection may block requests

## Project Structure

```
.
├── main.py              # FastAPI application
├── scraper.py           # Core scraping logic
├── requirements.txt     # Python dependencies
├── run.sh              # Setup and run script
├── README.md           # This file
├── design_notes.md     # Design decisions and strategies
└── capabilities.json   # Feature implementation status
```

## Error Handling

The scraper gracefully handles errors and returns partial results when possible:

- Network timeouts
- Invalid URLs
- JavaScript rendering failures
- Missing content
- Blocked requests

Errors are reported in the `errors` array with message and phase information.

## Development

### Adding New Features

1. Modify `scraper.py` for new scraping capabilities
2. Update `main.py` for new API endpoints
3. Update frontend HTML in `main.py` for UI changes
4. Update `capabilities.json` to reflect new features

### Testing

Test with various website types:
- Static HTML sites
- JavaScript-heavy SPAs
- Sites with tabs and accordions
- Sites with infinite scroll
- Paginated content sites

## Troubleshooting

### Playwright Installation Issues

If Playwright browsers fail to install:

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2

# Then retry installation
playwright install chromium
playwright install-deps chromium
```

### Port Already in Use

If port 8000 is busy:

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Scraping Timeouts

If requests timeout frequently:

1. Check your internet connection
2. The target website may be slow or blocking automated requests
3. Increase timeout in `scraper.py` if needed

## License

This project is created as part of the Lyftr AI full-stack assignment.

## Support

For issues or questions, please contact the development team.