# Troubleshooting Guide

This guide helps resolve common issues when setting up and running the Universal Website Scraper.

## Installation Issues

### Issue: `run.sh` Permission Denied

**Symptoms**: Error message "Permission denied" when running `./run.sh`

**Solution**:
```bash
chmod +x run.sh
./run.sh
```

### Issue: Python Not Found

**Symptoms**: Error message "python3: command not found"

**Solution**:
- **Ubuntu/Debian**: `sudo apt-get install python3 python3-pip python3-venv`
- **macOS**: `brew install python3`
- **Windows**: Download from [python.org](https://www.python.org/downloads/)

### Issue: Playwright Browser Installation Fails

**Symptoms**: Errors during `playwright install chromium`

**Solution**:
```bash
# Activate virtual environment first
source venv/bin/activate

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2

# Then retry Playwright installation
playwright install chromium
playwright install-deps chromium
```

## Runtime Issues

### Issue: Server Won't Start (Port in Use)

**Symptoms**: Error "Address already in use" or port 8000 is busy

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process (replace PID with actual process ID)
kill -9 PID

# Or use a different port by modifying main.py:
# uvicorn.run(app, host="0.0.0.0", port=8001)
```

### Issue: Scraping Times Out

**Symptoms**: Requests hang or timeout after 30 seconds

**Solution**:
1. Check your internet connection
2. The target website may be slow or blocking automated requests
3. Increase timeout in `scraper.py`:
```python
self.timeout = 60000  # Change from 30000 to 60000 (60 seconds)
```

### Issue: JS Rendering Fails

**Symptoms**: No content extracted from JS-heavy sites

**Solution**:
1. Ensure Playwright browsers are installed:
```bash
playwright install chromium
```

2. Check if the site blocks automation:
```python
# In scraper.py, add to browser context:
context = await browser.new_context(
    viewport={"width": 1920, "height": 1080},
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)
```

### Issue: Empty Sections Returned

**Symptoms**: Scraper runs but returns no meaningful content

**Possible Causes**:
1. **Website blocks automated access**: Try accessing in incognito browser
2. **Content requires authentication**: Scraper can't handle login
3. **Heavy CAPTCHA protection**: Can't be bypassed
4. **Content in iframes**: Not currently extracted

**Solution**:
- Check if the website works in a regular browser
- Look for "403 Forbidden" or "429 Too Many Requests" errors
- Try a different test URL

## API Issues

### Issue: `/scrape` Returns 422 Error

**Symptoms**: "Unprocessable Entity" error

**Cause**: Invalid URL format

**Solution**:
```bash
# Correct format (include https://):
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Wrong format (missing protocol):
# {"url": "example.com"}  ❌
```

### Issue: CORS Errors in Frontend

**Symptoms**: Browser console shows CORS errors

**Solution**: Add CORS middleware to `main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Performance Issues

### Issue: Scraping is Very Slow

**Solutions**:
1. **Reduce timeout**:
```python
# In scraper.py
self.timeout = 15000  # Reduce from 30000
```

2. **Limit interactions**:
```python
# In scraper.py
self.max_scrolls = 2  # Reduce from 3
self.max_pages = 2    # Reduce from 3
```

3. **Disable JS for static sites**: The scraper should automatically use static scraping first

### Issue: High Memory Usage

**Cause**: Playwright browser instances not closing

**Solution**:
- Ensure browsers close in `finally` block (already implemented)
- Restart the server periodically for long-running instances

## Testing Issues

### Issue: Test Script Fails

**Symptoms**: `test_api.py` throws errors

**Solution**:
```bash
# Ensure server is running first
./run.sh

# In another terminal, run tests
python3 test_api.py
```

### Issue: Some Test URLs Don't Work

**Cause**: Website may be down, blocking automated access, or changed structure

**Solution**:
- Try alternative URLs from README.md
- Check if the website loads in a regular browser
- Look at the errors returned in the JSON response

## Development Issues

### Issue: Changes Not Reflected

**Solution**:
1. Stop the server (Ctrl+C)
2. Restart: `./run.sh`
3. For code changes, no need to reinstall dependencies

### Issue: Module Import Errors

**Symptoms**: "ModuleNotFoundError" when running

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## Debugging Tips

### Enable Verbose Logging

Add to `main.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### View Request/Response in Browser

Open browser DevTools (F12) → Network tab → Monitor API calls

### Check Playwright in Non-Headless Mode

In `scraper.py`:
```python
browser = await p.chromium.launch(headless=False)  # Change to False
```

This opens a visible browser window to see what's happening.

### Manual API Testing with curl

```bash
# Test health
curl http://localhost:8000/healthz

# Test scrape
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}' \
  | jq '.'  # Pretty print with jq
```

## Getting Help

If issues persist:

1. Check the `errors` array in API responses
2. Look for error messages in terminal output
3. Verify all dependencies installed correctly: `pip list`
4. Check Python version: `python3 --version` (should be 3.10+)
5. Review server logs for stack traces

## Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| "Address already in use" | Port 8000 busy | Kill process or use different port |
| "playwright._impl._errors.Error" | Browser not installed | Run `playwright install chromium` |
| "Connection refused" | Server not running | Start with `./run.sh` |
| "Timeout waiting for..." | Page too slow | Increase timeout or check internet |
| "422 Unprocessable Entity" | Invalid request format | Check URL format includes `https://` |

## Platform-Specific Notes

### macOS
- May need to install Xcode Command Line Tools: `xcode-select --install`
- Use `python3` explicitly (not `python`)

### Windows
- Use `venv\Scripts\activate` instead of `source venv/bin/activate`
- May need to enable script execution: `Set-ExecutionPolicy RemoteSigned`
- Consider using WSL2 for better compatibility

### Linux
- Install system dependencies for Playwright (see above)
- May need `sudo` for system package installation
- Ensure proper permissions on project directory