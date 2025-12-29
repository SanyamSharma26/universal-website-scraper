#!/usr/bin/env python3
"""
Test script for Universal Website Scraper API
Run this after starting the server with ./run.sh
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health_check() -> bool:
    """Test the /healthz endpoint"""
    print_section("Testing Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/healthz")
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200 and data.get("status") == "ok":
            print("✅ Health check passed!")
            return True
        else:
            print("❌ Health check failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_scrape(url: str, description: str) -> Dict[str, Any]:
    """Test the /scrape endpoint"""
    print_section(f"Testing Scrape: {description}")
    print(f"URL: {url}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/scrape",
            json={"url": url},
            timeout=60
        )
        
        data = response.json()
        result = data.get("result", {})
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Sections Found: {len(result.get('sections', []))}")
        print(f"Clicks Performed: {len(result.get('interactions', {}).get('clicks', []))}")
        print(f"Scrolls: {result.get('interactions', {}).get('scrolls', 0)}")
        print(f"Pages Visited: {len(result.get('interactions', {}).get('pages', []))}")
        print(f"Errors: {len(result.get('errors', []))}")
        
        # Show first section
        sections = result.get("sections", [])
        if sections:
            first_section = sections[0]
            print(f"\nFirst Section:")
            print(f"  Type: {first_section.get('type')}")
            print(f"  Label: {first_section.get('label')}")
            print(f"  Text Preview: {first_section.get('content', {}).get('text', '')[:100]}...")
            print(f"  Headings: {first_section.get('content', {}).get('headings', [])[:3]}")
        
        # Show errors if any
        errors = result.get("errors", [])
        if errors:
            print(f"\n⚠️  Errors encountered:")
            for error in errors:
                print(f"  - [{error.get('phase')}] {error.get('message')}")
        
        # Validation
        print(f"\n📊 Validation:")
        checks = {
            "URL matches": result.get("url") == url,
            "Has sections": len(sections) > 0,
            "Has metadata": bool(result.get("meta", {}).get("title")),
            "Sections have content": any(s.get("content", {}).get("text") for s in sections),
        }
        
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check}")
        
        all_passed = all(checks.values())
        if all_passed:
            print("\n✅ Scrape test passed!")
        else:
            print("\n⚠️  Scrape test completed with warnings")
            
        return result
        
    except requests.Timeout:
        print("❌ Request timed out")
        return {}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {}

def main():
    """Run all tests"""
    print("\n" + "🔍 Universal Website Scraper - API Tests".center(60))
    print("=" * 60)
    
    # Test health check
    if not test_health_check():
        print("\n❌ Server is not responding correctly!")
        sys.exit(1)
    
    # Test URLs
    test_cases = [
        {
            "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
            "description": "Wikipedia (Static HTML)"
        },
        {
            "url": "https://news.ycombinator.com/",
            "description": "Hacker News (Pagination)"
        },
        {
            "url": "https://vercel.com/",
            "description": "Vercel (JS-heavy)"
        }
    ]
    
    results = []
    for test_case in test_cases:
        result = test_scrape(test_case["url"], test_case["description"])
        results.append(result)
        
        # Add delay between tests
        import time
        time.sleep(2)
    
    # Summary
    print_section("Test Summary")
    successful = sum(1 for r in results if r.get("sections"))
    total = len(test_cases)
    print(f"Successful scrapes: {successful}/{total}")
    
    if successful == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - successful} test(s) had issues")

if __name__ == "__main__":
    main()