# Design Notes

## Static vs JS Fallback

**Strategy**: The scraper implements a two-stage approach with intelligent fallback logic.

1. **Static-First Approach**: Every scrape attempt begins with static HTML fetching using httpx and selectolax. This is fast and efficient for most content-heavy sites.

2. **Fallback Decision Heuristics**:
   - If fewer than 2 sections are extracted → trigger JS rendering
   - If total text content is less than 200 characters → trigger JS rendering
   - If static fetch encounters errors → skip JS (likely won't help)

3. **Rationale**: Modern JavaScript frameworks often render content client-side, leaving minimal HTML in the initial response. By checking section count and text content, we can detect when meaningful content is missing and switch to browser-based rendering.

## Wait Strategy for JS

- [x] Network idle
- [ ] Fixed sleep
- [x] Wait for selectors
- [ ] Combination approach

**Details**: When using Playwright, we wait for `networkidle` state during initial page load to ensure all resources are fetched. We then wait for the `body` selector to confirm DOM rendering. For interactions (clicks, scrolls), we use short fixed timeouts (1-2 seconds) to allow content to load after each action. This balanced approach ensures we capture dynamic content without excessive waiting.

## Click & Scroll Strategy

**Click flows implemented**:
1. **Tab Interactions**: Searches for elements with `[role="tab"]`, `button[aria-selected]`, and tab-related classes. Clicks up to 3 tabs sequentially with 1-second pauses between clicks.
2. **Load More Buttons**: Looks for buttons containing text like "Load more", "Show more", "View more" and clicks them up to 3 times, waiting 2 seconds after each click.

**Scroll / pagination approach**:
1. **Infinite Scroll**: Scrolls to the bottom of the page up to 3 times, waiting 2 seconds between scrolls. Tracks `document.body.scrollHeight` to detect when new content loads.
2. **Pagination Links**: Searches for "Next" links, ">" buttons, and `[rel="next"]` attributes. Follows up to 3 pages, tracking visited URLs to avoid loops.

**Stop conditions**:
- Maximum 3 scrolls for infinite scroll
- Maximum 3 pages for pagination
- 5-10 second timeouts for individual interactions
- 30-second overall page timeout
- Detection of no new content (height unchanged, no new URL)

## Section Grouping & Labels

**How sections are grouped**:
1. **Landmark-Based**: Primary strategy uses semantic HTML landmarks (`<main>`, `<header>`, `<nav>`, `<section>`, `<footer>`, `<article>`)
2. **Heading-Based Fallback**: If few landmarks found, parse by heading hierarchy (h1-h3), treating each heading and its following content as a section
3. **Body Fallback**: If no structure found, use entire body as single section

**Section type and label derivation**:
- **Type Detection**: Analyzes element classes and IDs for keywords:
  - "hero", "banner", "jumbotron" → `hero`
  - "nav", "menu" → `nav`
  - "footer" → `footer`
  - "faq", "question" → `faq`
  - "pricing", "price" → `pricing`
  - "grid", "gallery" → `grid`
  - Lists present → `list`
  - Default → `section`

- **Label Creation**:
  1. First heading text (if present) - truncated to 50 chars
  2. Type-based label + first 7 words of text content (e.g., "Section: Welcome to our platform")
  3. Fallback to simple type name (e.g., "Hero", "Navigation")

## Noise Filtering & Truncation

**What is filtered out**:
- Cookie consent banners: `[class*="cookie"]`, `[id*="cookie"]`
- Modal overlays: `[class*="modal"]`, `[class*="overlay"]`
- Popup notifications: `[class*="popup"]`
- Newsletter banners: `[class*="banner"]`
- General consent forms: `[class*="consent"]`

These elements are removed from the DOM before content extraction to prevent them from appearing in sections.

**HTML truncation**:
- **Threshold**: Each section's `rawHtml` is limited to 1000 characters
- **Method**: Simple string truncation with "..." suffix
- **Truncated Flag**: Set to `true` when HTML exceeds 1000 chars, `false` otherwise
- **Rationale**: Prevents massive JSON responses while preserving enough HTML for structure inspection. Full content is available through other fields (text, headings, links, etc.)

## Additional Implementation Details

### Error Handling
- All scraping operations wrapped in try-catch blocks
- Errors captured with message and phase (fetch, render, parse, js_scrape)
- Partial results returned when possible instead of complete failure
- Timeouts prevent indefinite hanging

### Link and Image Processing
- All relative URLs converted to absolute using `urljoin()`
- Base URL determined from scraped page URL
- Handles both href attributes and src attributes

### Content Extraction
- Text from `<p>` tags primarily, with `<div>` fallback
- Headings from h1-h6 hierarchy
- Lists from `<ul>` and `<ol>` with nested `<li>` items
- Tables extracted as 2D arrays of cell text
- Images include both src and alt attributes
- Links include both text and absolute href

### Performance Optimizations
- Static scraping first (fast path)
- JS rendering only when needed
- Limited section count for heading-based extraction (10 max)
- Limited text parts per section (10 paragraphs)
- Limited links, images per section
- Headless browser mode for Playwright
- Browser context closed after each scrape
