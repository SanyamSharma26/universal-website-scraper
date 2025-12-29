import asyncio
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any, Optional
import httpx
from selectolax.parser import HTMLParser
import random

# Try to import Playwright
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: Playwright not available. Install with: pip install playwright && playwright install chromium")

class WebScraper:
    def __init__(self):
        self.timeout = 30000  # 30 seconds
        self.max_scrolls = 3
        self.max_pages = 3
        
        # Realistic browser user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ]
        
    async def scrape(self, url: str) -> Dict[str, Any]:
        """Main scraping function"""
        result = {
            "url": url,
            "scrapedAt": datetime.now(timezone.utc).isoformat(),
            "meta": {
                "title": "",
                "description": "",
                "language": "en",
                "canonical": None,
                "strategy": "static"
            },
            "sections": [],
            "interactions": {
                "clicks": [],
                "scrolls": 0,
                "pages": [url]
            },
            "errors": []
        }
        
        try:
            # Determine scraping strategy based on URL
            domain = urlparse(url).netloc.lower()
            force_js = self._should_force_js(domain)
            
            if force_js and PLAYWRIGHT_AVAILABLE:
                # Skip static, go directly to JS for known JS-heavy sites
                result["meta"]["strategy"] = "js"
                js_result = await self._js_scrape(url)
                result.update(js_result)
            else:
                # Try static scraping first
                static_result = await self._static_scrape(url)
                result.update(static_result)
                
                # Check if we need JS rendering fallback
                needs_js = self._needs_js_rendering(result)
                
                if needs_js and PLAYWRIGHT_AVAILABLE:
                    result["meta"]["strategy"] = "js"
                    result["errors"].append({
                        "message": "Static scraping insufficient, using JS rendering",
                        "phase": "fallback_decision"
                    })
                    
                    # Try JS rendering
                    js_result = await self._js_scrape(url)
                    
                    # Merge results, preferring JS results
                    if js_result.get("sections") and len(js_result["sections"]) > len(result.get("sections", [])):
                        result["sections"] = js_result["sections"]
                    if js_result.get("meta", {}).get("title"):
                        result["meta"].update(js_result["meta"])
                        result["meta"]["strategy"] = "js"
                    if js_result.get("interactions"):
                        result["interactions"] = js_result["interactions"]
                    if js_result.get("errors"):
                        result["errors"].extend(js_result["errors"])
                elif needs_js and not PLAYWRIGHT_AVAILABLE:
                    result["errors"].append({
                        "message": "JS rendering recommended but Playwright not installed. Run: pip install playwright && playwright install chromium",
                        "phase": "playwright_check"
                    })
                
        except Exception as e:
            result["errors"].append({
                "message": str(e),
                "phase": "scrape"
            })
            
        return result
    
    def _should_force_js(self, domain: str) -> bool:
        """Determine if site should always use JS rendering"""
        js_heavy_domains = [
            'wikipedia.org',      # Wikipedia blocks static scraping
            'wikimedia.org',
            'medium.com',
            'vercel.com',
            'twitter.com',
            'x.com',
            'reddit.com',
            'linkedin.com',
            'instagram.com',
            'facebook.com',
            'youtube.com',
            'netflix.com',
            'airbnb.com',
            'uber.com'
        ]
        return any(d in domain for d in js_heavy_domains)
    
    def _needs_js_rendering(self, result: Dict[str, Any]) -> bool:
        """Heuristic to determine if JS rendering is needed"""
        sections = result.get("sections", [])
        errors = result.get("errors", [])
        
        # Don't retry JS if we got blocked (403, 429, etc.)
        blocked_errors = ['403', '429', 'Forbidden', 'Too Many Requests']
        if any(any(block in str(e.get("message", "")) for block in blocked_errors) for e in errors):
            return False
        
        # If fewer than 2 sections, likely JS-rendered
        if len(sections) < 2:
            return True
        
        # Calculate total text content
        total_text = sum(len(s.get("content", {}).get("text", "")) for s in sections)
        
        # If less than 200 characters total, likely JS-rendered
        if total_text < 200:
            return True
        
        return False
    
    def _get_random_user_agent(self) -> str:
        """Get a random realistic user agent"""
        return random.choice(self.user_agents)
    
    async def _static_scrape(self, url: str) -> Dict[str, Any]:
        """Perform static HTML scraping with enhanced headers"""
        result = {
            "meta": {"strategy": "static"},
            "sections": [],
            "interactions": {
                "clicks": [],
                "scrolls": 0,
                "pages": [url]
            },
            "errors": []
        }
        
        try:
            # Enhanced headers to avoid blocking
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
            
            # Add small random delay to appear more human-like
            await asyncio.sleep(random.uniform(0.1, 0.3))
            
            async with httpx.AsyncClient(
                follow_redirects=True, 
                timeout=30.0, 
                headers=headers,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text
                
            parser = HTMLParser(html)
            
            # Extract metadata
            result["meta"] = self._extract_meta(parser, url)
            result["meta"]["strategy"] = "static"
            
            # Extract sections
            result["sections"] = self._extract_sections(parser, url)
            
        except httpx.HTTPStatusError as e:
            result["errors"].append({
                "message": f"HTTP {e.response.status_code}: {e.response.reason_phrase}",
                "phase": "fetch",
                "suggestion": "Site may be blocking automated requests. Try JS rendering."
            })
        except httpx.TimeoutException:
            result["errors"].append({
                "message": "Request timed out after 30 seconds",
                "phase": "fetch"
            })
        except Exception as e:
            result["errors"].append({
                "message": str(e),
                "phase": "fetch"
            })
            
        return result
    
    async def _js_scrape(self, url: str) -> Dict[str, Any]:
        """Perform JavaScript rendering with Playwright - STEALTH MODE"""
        result = {
            "meta": {"strategy": "js"},
            "sections": [],
            "interactions": {
                "clicks": [],
                "scrolls": 0,
                "pages": [url]
            },
            "errors": []
        }
        
        if not PLAYWRIGHT_AVAILABLE:
            result["errors"].append({
                "message": "Playwright not installed. Run: pip install playwright && playwright install chromium",
                "phase": "playwright_check"
            })
            return result
        
        try:
            async with async_playwright() as p:
                # Launch browser with stealth settings
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                    ]
                )
                
                # Create context with realistic settings
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=self._get_random_user_agent(),
                    locale='en-US',
                    timezone_id='America/New_York',
                    permissions=['geolocation'],
                    geolocation={'latitude': 40.7128, 'longitude': -74.0060},
                    color_scheme='light',
                    extra_http_headers={
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'DNT': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Upgrade-Insecure-Requests': '1',
                    }
                )
                
                page = await context.new_page()
                
                # Remove webdriver detection
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => false
                    });
                    
                    // Remove automation indicators
                    window.navigator.chrome = {
                        runtime: {}
                    };
                    
                    // Mock plugins
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    
                    // Mock languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                """)
                
                try:
                    # Navigate to page
                    await page.goto(url, wait_until="networkidle", timeout=self.timeout)
                    
                    # Random human-like delay
                    await page.wait_for_timeout(random.randint(500, 1500))
                    
                    # Wait for body to ensure rendering
                    await page.wait_for_selector("body", timeout=10000)
                    
                    # Remove noise elements
                    await self._remove_noise(page)
                    
                    # Perform interactions
                    await self._perform_clicks(page, result)
                    await self._perform_scrolls(page, result)
                    await self._follow_pagination(page, result, url)
                    
                    # Get final HTML
                    html = await page.content()
                    parser = HTMLParser(html)
                    
                    # Extract metadata and sections
                    result["meta"] = self._extract_meta(parser, url)
                    result["meta"]["strategy"] = "js"
                    result["sections"] = self._extract_sections(parser, url)
                    
                except PlaywrightTimeout as e:
                    result["errors"].append({
                        "message": f"Timeout: {str(e)}",
                        "phase": "render"
                    })
                except Exception as e:
                    result["errors"].append({
                        "message": str(e),
                        "phase": "js_scrape"
                    })
                finally:
                    await browser.close()
                    
        except Exception as e:
            result["errors"].append({
                "message": str(e),
                "phase": "playwright"
            })
            
        return result
    
    async def _remove_noise(self, page):
        """Remove noise elements like cookie banners, modals"""
        noise_selectors = [
            '[class*="cookie"]',
            '[id*="cookie"]',
            '[class*="modal"]',
            '[class*="overlay"]',
            '[class*="popup"]',
            '[class*="consent"]',
            '[aria-label*="cookie" i]',
            '[aria-label*="consent" i]',
            '.gdpr',
            '#gdpr',
        ]
        
        for selector in noise_selectors:
            try:
                await page.evaluate(f'''
                    document.querySelectorAll('{selector}').forEach(el => el.remove());
                ''')
            except:
                pass
    
    async def _perform_clicks(self, page, result: Dict[str, Any]):
        """Perform click interactions (tabs, load more buttons)"""
        clicks = []
        
        # Try clicking tabs
        tab_selectors = [
            '[role="tab"]',
            'button[aria-selected]',
            '.tab:not(.active)',
            '.tabs button',
            '[data-tab]'
        ]
        
        for selector in tab_selectors:
            try:
                tabs = await page.query_selector_all(selector)
                for i, tab in enumerate(tabs[:3]):  # Click up to 3 tabs
                    try:
                        await tab.scroll_into_view_if_needed()
                        await page.wait_for_timeout(random.randint(300, 700))
                        await tab.click(timeout=5000)
                        clicks.append(f"{selector}:nth({i})")
                        await page.wait_for_timeout(random.randint(800, 1500))
                    except:
                        pass
                if tabs:
                    break
            except:
                pass
        
        # Try clicking "Load more" buttons
        load_more_selectors = [
            'button:has-text("Load more")',
            'button:has-text("Show more")',
            'button:has-text("View more")',
            'button:has-text("Read more")',
            'a:has-text("Load more")',
            '[class*="load-more"]',
            '[class*="show-more"]',
        ]
        
        for selector in load_more_selectors:
            try:
                for i in range(3):
                    button = await page.query_selector(selector)
                    if button and await button.is_visible():
                        await button.scroll_into_view_if_needed()
                        await page.wait_for_timeout(random.randint(300, 700))
                        await button.click(timeout=5000)
                        clicks.append(f"{selector}:click({i})")
                        await page.wait_for_timeout(random.randint(1500, 2500))
                    else:
                        break
            except:
                pass
        
        result["interactions"]["clicks"] = clicks
    
    async def _perform_scrolls(self, page, result: Dict[str, Any]):
        """Perform scroll interactions for infinite scroll - HUMAN-LIKE"""
        scrolls = 0
        
        try:
            for i in range(self.max_scrolls):
                prev_height = await page.evaluate('document.body.scrollHeight')
                
                # Scroll in chunks like a human
                current_position = await page.evaluate('window.pageYOffset')
                target_position = await page.evaluate('document.body.scrollHeight')
                
                # Smooth scroll in steps
                steps = random.randint(3, 5)
                for step in range(steps):
                    scroll_amount = (target_position - current_position) / (steps - step)
                    await page.evaluate(f'window.scrollBy(0, {scroll_amount})')
                    await page.wait_for_timeout(random.randint(200, 500))
                
                # Wait for content to load
                await page.wait_for_timeout(random.randint(1500, 2500))
                
                new_height = await page.evaluate('document.body.scrollHeight')
                scrolls += 1
                
                # Stop if no new content loaded
                if new_height == prev_height:
                    break
                    
        except Exception as e:
            result["errors"].append({
                "message": f"Scroll error: {str(e)}",
                "phase": "scroll"
            })
        
        result["interactions"]["scrolls"] = scrolls
    
    async def _follow_pagination(self, page, result: Dict[str, Any], base_url: str):
        """Follow pagination links to depth >= 3"""
        visited_pages = [base_url]
        
        try:
            for page_num in range(self.max_pages - 1):
                next_selectors = [
                    'a:has-text("Next")',
                    'a:has-text(">")',
                    'a:has-text("→")',
                    'a[rel="next"]',
                    'a[aria-label*="next" i]',
                    '[class*="next"]:not([class*="disabled"])',
                    '[class*="pagination"] a:last-child',
                    'button:has-text("More")',
                ]
                
                next_link = None
                for selector in next_selectors:
                    try:
                        next_link = await page.query_selector(selector)
                        if next_link and await next_link.is_visible():
                            break
                        next_link = None
                    except:
                        pass
                
                if not next_link:
                    break
                
                href = await next_link.get_attribute('href')
                if href:
                    next_url = urljoin(str(page.url), href)
                    if next_url not in visited_pages:
                        visited_pages.append(next_url)
                
                try:
                    # Human-like delay before clicking
                    await page.wait_for_timeout(random.randint(500, 1000))
                    await next_link.scroll_into_view_if_needed()
                    await next_link.click(timeout=5000)
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    await page.wait_for_timeout(random.randint(1000, 2000))
                except:
                    break
                    
        except Exception as e:
            result["errors"].append({
                "message": f"Pagination error: {str(e)}",
                "phase": "pagination"
            })
        
        result["interactions"]["pages"] = visited_pages
    
    def _extract_meta(self, parser: HTMLParser, url: str) -> Dict[str, Any]:
        """Extract page metadata"""
        meta = {
            "title": "",
            "description": "",
            "language": "en",
            "canonical": None
        }
        
        # Title - try multiple sources
        title_tag = parser.css_first("title")
        if title_tag:
            meta["title"] = title_tag.text(strip=True)
        
        if not meta["title"]:
            og_title = parser.css_first('meta[property="og:title"]')
            if og_title:
                meta["title"] = og_title.attributes.get("content", "")
        
        if not meta["title"]:
            twitter_title = parser.css_first('meta[name="twitter:title"]')
            if twitter_title:
                meta["title"] = twitter_title.attributes.get("content", "")
        
        # Description - try multiple sources
        desc_tag = parser.css_first('meta[name="description"]')
        if desc_tag:
            meta["description"] = desc_tag.attributes.get("content", "")
        
        if not meta["description"]:
            og_desc = parser.css_first('meta[property="og:description"]')
            if og_desc:
                meta["description"] = og_desc.attributes.get("content", "")
        
        if not meta["description"]:
            twitter_desc = parser.css_first('meta[name="twitter:description"]')
            if twitter_desc:
                meta["description"] = twitter_desc.attributes.get("content", "")
        
        # Language
        html_tag = parser.css_first("html")
        if html_tag:
            lang = html_tag.attributes.get("lang", "en")
            meta["language"] = lang.split("-")[0] if lang else "en"
        
        # Canonical
        canonical_tag = parser.css_first('link[rel="canonical"]')
        if canonical_tag:
            canonical_url = canonical_tag.attributes.get("href", "")
            meta["canonical"] = urljoin(url, canonical_url) if canonical_url else None
        
        return meta
    
    def _extract_sections(self, parser: HTMLParser, url: str) -> List[Dict[str, Any]]:
        """Extract content sections from HTML"""
        sections = []
        
        # Find main content landmarks
        landmarks = []
        
        main = parser.css_first("main")
        if main:
            landmarks.append(("main", main))
        
        # Look for article container (common in Medium, blogs)
        article = parser.css_first("article")
        if article:
            landmarks.append(("article", article))
        
        header = parser.css_first("header")
        if header:
            landmarks.append(("header", header))
        
        nav = parser.css_first("nav")
        if nav:
            landmarks.append(("nav", nav))
        
        footer = parser.css_first("footer")
        if footer:
            landmarks.append(("footer", footer))
        
        # Get all sections
        for section_elem in parser.css("section"):
            landmarks.append(("section", section_elem))
        
        # If no landmarks, try articles
        if len(landmarks) < 3:
            for article_elem in parser.css("article"):
                if article_elem not in [l[1] for l in landmarks]:
                    landmarks.append(("article", article_elem))
        
        # Fallback to body
        if not landmarks:
            body = parser.css_first("body")
            if body:
                landmarks.append(("body", body))
        
        # Process each landmark
        for idx, (landmark_type, element) in enumerate(landmarks):
            section = self._process_section(element, landmark_type, idx, url)
            if section and (section["content"]["text"] or section["content"]["headings"]):
                sections.append(section)
        
        # If we got very few sections, try heading-based extraction
        if len(sections) < 3:
            heading_sections = self._extract_by_headings(parser, url)
            sections.extend(heading_sections)
        
        # Remove duplicates based on content similarity
        sections = self._deduplicate_sections(sections)
        
        return sections
    
    def _deduplicate_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate sections based on content similarity"""
        if len(sections) <= 1:
            return sections
        
        unique_sections = []
        seen_texts = set()
        
        for section in sections:
            text = section.get("content", {}).get("text", "")
            # Create a simple fingerprint
            fingerprint = text[:100].lower().strip()
            
            if fingerprint and fingerprint not in seen_texts:
                seen_texts.add(fingerprint)
                unique_sections.append(section)
            elif not fingerprint and section.get("content", {}).get("headings"):
                # Keep sections with headings even if no text
                unique_sections.append(section)
        
        return unique_sections
    
    def _process_section(self, element, section_type: str, idx: int, url: str) -> Optional[Dict[str, Any]]:
        """Process a single section element"""
        content = {
            "headings": [],
            "text": "",
            "links": [],
            "images": [],
            "lists": [],
            "tables": []
        }
        
        # Headings
        for level in range(1, 7):
            for heading in element.css(f"h{level}"):
                text = heading.text(strip=True)
                if text and len(text) > 0:
                    content["headings"].append(text)
        
        # Text content - paragraphs
        text_parts = []
        for p in element.css("p"):
            text = p.text(strip=True)
            if text and len(text) > 10:  # Ignore very short paragraphs
                text_parts.append(text)
        
        # If no paragraphs, try divs
        if len(text_parts) < 2:
            for div in element.css("div"):
                text = div.text(strip=True)
                if text and len(text) > 30:
                    text_parts.append(text)
                    if len(text_parts) >= 5:
                        break
        
        content["text"] = " ".join(text_parts[:15])  # Increased limit
        
        # Links
        for link in element.css("a"):
            href = link.attributes.get("href", "")
            text = link.text(strip=True)
            if href and text:
                absolute_url = urljoin(url, href)
                content["links"].append({
                    "text": text[:100],  # Limit text length
                    "href": absolute_url
                })
                if len(content["links"]) >= 20:  # Limit links
                    break
        
        # Images
        for img in element.css("img"):
            src = img.attributes.get("src", "") or img.attributes.get("data-src", "")
            alt = img.attributes.get("alt", "")
            if src:
                absolute_src = urljoin(url, src)
                content["images"].append({
                    "src": absolute_src,
                    "alt": alt
                })
                if len(content["images"]) >= 10:  # Limit images
                    break
        
        # Lists
        for ul in element.css("ul, ol"):
            items = []
            for li in ul.css("li"):
                text = li.text(strip=True)
                if text:
                    items.append(text[:200])  # Limit item length
            if items:
                content["lists"].append(items[:20])  # Limit items per list
            if len(content["lists"]) >= 5:  # Limit lists
                break
        
        # Tables
        for table in element.css("table"):
            table_data = []
            for row in table.css("tr"):
                row_data = []
                for cell in row.css("td, th"):
                    row_data.append(cell.text(strip=True)[:100])
                if row_data:
                    table_data.append(row_data)
                if len(table_data) >= 20:  # Limit rows
                    break
            if table_data:
                content["tables"].append(table_data)
            if len(content["tables"]) >= 3:  # Limit tables
                break
        
        # Determine section type
        detected_type = self._detect_section_type(element, content)
        if section_type == "header":
            detected_type = "hero"
        elif section_type == "nav":
            detected_type = "nav"
        elif section_type == "footer":
            detected_type = "footer"
        elif section_type == "article":
            detected_type = "section"
        
        # Create label
        label = self._create_label(content, detected_type)
        
        # Get raw HTML (truncated)
        raw_html = element.html if hasattr(element, 'html') else str(element)
        truncated = len(raw_html) > 1000
        if truncated:
            raw_html = raw_html[:1000] + "..."
        
        return {
            "id": f"{detected_type}-{idx}",
            "type": detected_type,
            "label": label,
            "sourceUrl": url,
            "content": content,
            "rawHtml": raw_html,
            "truncated": truncated
        }
    
    def _extract_by_headings(self, parser: HTMLParser, url: str) -> List[Dict[str, Any]]:
        """Extract sections based on heading structure"""
        sections = []
        body = parser.css_first("body")
        if not body:
            return sections
        
        headings = body.css("h1, h2, h3")
        
        for idx, heading in enumerate(headings[:15]):  # Increased limit
            content_elements = []
            current = heading.next
            
            while current and current.tag not in ["h1", "h2", "h3"]:
                content_elements.append(current)
                current = current.next
                if len(content_elements) > 15:
                    break
            
            section_html = f"<section>{heading.html}"
            for elem in content_elements:
                section_html += elem.html
            section_html += "</section>"
            
            virtual_parser = HTMLParser(section_html)
            virtual_section = virtual_parser.css_first("section")
            
            if virtual_section:
                section = self._process_section(virtual_section, "section", len(sections), url)
                if section and (section["content"]["text"] or section["content"]["headings"]):
                    sections.append(section)
        
        return sections
    
    def _detect_section_type(self, element, content: Dict[str, Any]) -> str:
        """Detect the type of section"""
        classes = " ".join(element.attributes.get("class", "").split()).lower()
        element_id = element.attributes.get("id", "").lower()
        combined = classes + " " + element_id
        
        if any(word in combined for word in ["hero", "banner", "jumbotron", "masthead"]):
            return "hero"
        elif any(word in combined for word in ["nav", "menu", "navigation", "navbar"]):
            return "nav"
        elif any(word in combined for word in ["footer", "foot"]):
            return "footer"
        elif any(word in combined for word in ["faq", "question", "accordion"]):
            return "faq"
        elif any(word in combined for word in ["pricing", "price", "plan", "tier"]):
            return "pricing"
        elif any(word in combined for word in ["grid", "gallery", "cards"]):
            return "grid"
        elif len(content["lists"]) > 0:
            return "list"
        
        return "section"
    
    def _create_label(self, content: Dict[str, Any], section_type: str) -> str:
        """Create a human-readable label for the section"""
        if content["headings"]:
            return content["headings"][0][:80]  # Increased limit
        
        type_labels = {
            "hero": "Hero",
            "nav": "Navigation",
            "footer": "Footer",
            "faq": "FAQ",
            "pricing": "Pricing",
            "grid": "Grid",
            "list": "List",
            "section": "Section",
            "article": "Article"
        }
        
        base_label = type_labels.get(section_type, "Section")
        
        if content["text"]:
            words = content["text"].split()[:10]  # Increased words
            context = " ".join(words)
            if len(context) > 15:
                return f"{base_label}: {context}"
        
        return base_label