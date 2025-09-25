#!/usr/bin/env python3
"""
Price Benchmark MVP
Author: Sebastian Quintana
Description: Fetches and compares prices from Newegg, Amazon, and eBay/Best Buy
            for consumer electronics price benchmarking.
"""

import re, sys, time, json, random, argparse
from decimal import Decimal
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Tuple, List
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# -------------------- Configuration --------------------
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0'
]

# -------------------- Data Models --------------------
@dataclass
class PriceResult:
    site: str
    price: Optional[Decimal]
    currency: str = "USD"
    url: Optional[str] = None
    title: Optional[str] = None
    status: str = "pending"
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

@dataclass
class BenchmarkResult:
    input_data: Dict[str, Any]
    results: List[Dict[str, Any]]
    summary: Dict[str, Any]
    metadata: Dict[str, Any]

# -------------------- Utilities --------------------
def parse_price(text: str) -> Optional[Decimal]:
    """Extract price from text string"""
    if not text:
        return None
    
    # Remove currency symbols and extra whitespace
    cleaned = re.sub(r'[$€£¥₹,]', '', text).strip()
    
    # Find first number pattern
    match = re.search(r'\d+\.?\d*', cleaned)
    if match:
        try:
            return Decimal(match.group())
        except:
            pass
    return None

def create_session() -> requests.Session:
    """Create HTTP session with browser-like headers"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    return session

def safe_request(url: str, params: Optional[Dict] = None, 
                session: Optional[requests.Session] = None,
                timeout: int = 10) -> Optional[requests.Response]:
    """Make HTTP request with error handling"""
    if not session:
        session = create_session()
    
    try:
        response = session.get(url, params=params, timeout=timeout)
        if response.status_code == 200:
            return response
        print(f"    Status code {response.status_code} for {url}")
    except requests.RequestException as e:
        print(f"    Request failed: {str(e)[:50]}")
    return None

# -------------------- Site Scrapers --------------------
class NeweggScraper:
    """Scraper for Newegg.com"""
    
    @staticmethod
    def fetch(item_number: str) -> Tuple[PriceResult, Optional[str]]:
        """Fetch product data from Newegg"""
        print(f"  → Fetching from Newegg...")
        url = f"https://www.newegg.com/p/{item_number}"
        
        session = create_session()
        session.headers['Referer'] = 'https://www.newegg.com/'
        
        response = safe_request(url, session=session)
        if not response:
            return PriceResult("newegg", None, status="error"), None
        
        if response.status_code == 403:
            return PriceResult("newegg", None, url=url, status="blocked"), None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = None
        title_meta = soup.find('meta', {'property': 'og:title'})
        if title_meta and title_meta.get('content'):
            title = re.sub(r'\s*-\s*Newegg\.com.*$', '', title_meta['content'])
        
        # Extract price from meta or JSON-LD
        price = None
        price_meta = soup.find('meta', {'itemprop': 'price'})
        if price_meta and price_meta.get('content'):
            price = parse_price(price_meta['content'])
        
        if not price:
            # Try JSON-LD
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        offers = data.get('offers', {})
                        if isinstance(offers, dict) and 'price' in offers:
                            price = parse_price(str(offers['price']))
                            break
                except:
                    continue
        
        status = "success" if price else "no_price"
        return PriceResult("newegg", price, url=url, title=title, status=status), title

class AmazonScraper:
    """Scraper for Amazon.com"""
    
    @staticmethod
    def search(query: str) -> PriceResult:
        """Search and get first result from Amazon"""
        print(f"  → Searching Amazon...")
        
        session = create_session()
        session.headers['Referer'] = 'https://www.amazon.com/'
        
        # Simplify query for better results
        simple_query = ' '.join(query.split()[:5])
        url = "https://www.amazon.com/s"
        params = {"k": simple_query}
        
        response = safe_request(url, params=params, session=session)
        if not response:
            return PriceResult("amazon", None, status="error")
        
        if "Enter the characters" in response.text:
            return PriceResult("amazon", None, url=url, status="captcha")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find first product
        product = soup.select_one('[data-component-type="s-search-result"]')
        if not product:
            return PriceResult("amazon", None, url=url, status="no_results")
        
        # Extract title
        title_elem = product.select_one('h2 span')
        title = title_elem.get_text(strip=True) if title_elem else None
        
        # Extract price with multiple selectors
        price = None
        price_selectors = [
            '.a-price .a-offscreen',
            '.a-price-whole',
            '.a-price span',
            '[class*="price"]'
        ]
        
        for selector in price_selectors:
            elem = product.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                price = parse_price(text)
                if price:
                    break
        
        # Extract URL
        link = product.select_one('h2 a')
        product_url = f"https://www.amazon.com{link['href']}" if link else url
        
        status = "success" if price else "no_price"
        return PriceResult("amazon", price, url=product_url, title=title, status=status)

class EbayScraper:
    """Scraper for eBay.com"""
    
    @staticmethod
    def search(query: str) -> PriceResult:
        """Search and get first Buy It Now result from eBay"""
        print(f"  → Searching eBay...")
        
        session = create_session()
        session.headers['Referer'] = 'https://www.ebay.com/'
        
        # Use simplified query
        simple_query = ' '.join(query.split()[:4])
        url = "https://www.ebay.com/sch/i.html"
        params = {
            "_nkw": simple_query,
            "LH_BIN": "1",  # Buy It Now only
            "_sop": "15"    # Sort by price
        }
        
        response = safe_request(url, params=params, session=session)
        if not response:
            return PriceResult("ebay", None, status="error")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find items (skip first as it's often ad)
        items = soup.select('.s-item')
        if len(items) < 2:
            return PriceResult("ebay", None, url=url, status="no_results")
        
        # Use second item
        product = items[1]
        
        # Extract title
        title_elem = product.select_one('.s-item__title')
        title = title_elem.get_text(strip=True) if title_elem else None
        
        # Extract price (skip ranges)
        price = None
        price_elem = product.select_one('.s-item__price')
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            if ' to ' not in price_text and ' - ' not in price_text:
                price = parse_price(price_text)
        
        # Extract URL
        link = product.select_one('.s-item__link')
        product_url = link['href'] if link else url
        
        status = "success" if price else "no_price"
        return PriceResult("ebay", price, url=product_url, title=title, status=status)

class BestBuyScraper:
    """Scraper for BestBuy.com (alternative)"""
    
    @staticmethod
    def search(query: str) -> PriceResult:
        """Search and get first result from Best Buy"""
        print(f"  → Searching Best Buy...")
        
        session = create_session()
        session.headers['Referer'] = 'https://www.bestbuy.com/'
        
        simple_query = ' '.join(query.split()[:4])
        url = "https://www.bestbuy.com/site/searchpage.jsp"
        params = {"st": simple_query}
        
        response = safe_request(url, params=params, session=session)
        if not response:
            return PriceResult("bestbuy", None, status="error")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find first product
        product = soup.select_one('.sku-item')
        if not product:
            return PriceResult("bestbuy", None, url=url, status="no_results")
        
        # Extract title
        title_elem = product.select_one('.sku-title a')
        title = title_elem.get_text(strip=True) if title_elem else None
        
        # Extract price
        price = None
        price_elem = product.select_one('.priceView-customer-price span')
        if price_elem:
            price = parse_price(price_elem.get_text(strip=True))
        
        # Extract URL
        link = product.select_one('.sku-title a')
        if link and link.get('href'):
            href = link['href']
            product_url = f"https://www.bestbuy.com{href}" if href.startswith('/') else href
        else:
            product_url = url
        
        status = "success" if price else "no_price"
        return PriceResult("bestbuy", price, url=product_url, title=title, status=status)

# -------------------- Main Benchmark Function --------------------
def run_benchmark(item_number: str, 
                manual_query: Optional[str] = None,
                use_bestbuy: bool = False) -> BenchmarkResult:
    """
    Run price comparison benchmark across multiple sites
    
    Args:
        item_number: Newegg item number
        manual_query: Optional manual search query
        use_bestbuy: Use Best Buy instead of eBay
    
    Returns:
        BenchmarkResult with prices from all sites
    """
    print("\n" + "="*60)
    print(" PRICE BENCHMARK MVP - Starting Analysis")
    print("="*60)
    
    start_time = time.time()
    results = []
    
    # 1. Fetch from Newegg
    print(f"\n📦 Newegg Item: {item_number}")
    newegg_result, product_title = NeweggScraper.fetch(item_number)
    results.append(asdict(newegg_result))
    
    if newegg_result.price:
        print(f"    ✓ Price: ${newegg_result.price}")
    else:
        print(f"    ✗ Status: {newegg_result.status}")
    
    # 2. Build search query
    search_query = manual_query or product_title or f"product {item_number}"
    search_query = re.sub(r'\s+', ' ', search_query).strip()
    print(f"\n🔍 Search Query: {search_query}")
    
    # Add delay to avoid rate limiting
    time.sleep(random.uniform(1, 2))
    
    # 3. Search Amazon
    amazon_result = AmazonScraper.search(search_query)
    results.append(asdict(amazon_result))
    
    if amazon_result.price:
        print(f"    ✓ Amazon: ${amazon_result.price}")
    else:
        print(f"    ✗ Amazon: {amazon_result.status}")
    
    time.sleep(random.uniform(1, 2))
    
    # 4. Search third site
    if use_bestbuy:
        third_result = BestBuyScraper.search(search_query)
    else:
        third_result = EbayScraper.search(search_query)
    
    results.append(asdict(third_result))
    
    if third_result.price:
        print(f"    ✓ {third_result.site.title()}: ${third_result.price}")
    else:
        print(f"    ✗ {third_result.site.title()}: {third_result.status}")
    
    # 5. Calculate summary statistics
    valid_prices = [r.price for r in [newegg_result, amazon_result, third_result] 
                if r.price is not None]
    
    summary = {
        "total_sites": 3,
        "successful_sites": len(valid_prices),
        "sites_with_prices": [r.site for r in [newegg_result, amazon_result, third_result] 
                            if r.price],
        "lowest_price": float(min(valid_prices)) if valid_prices else None,
        "highest_price": float(max(valid_prices)) if valid_prices else None,
        "average_price": float(sum(valid_prices) / len(valid_prices)) if valid_prices else None,
        "price_variance": float(max(valid_prices) - min(valid_prices)) if len(valid_prices) >= 2 else None,
        "savings_potential": float(max(valid_prices) - min(valid_prices)) if len(valid_prices) >= 2 else 0
    }
    
    metadata = {
        "execution_time": f"{time.time() - start_time:.2f} seconds",
        "timestamp": datetime.now().isoformat(),
        "query_used": search_query,
        "third_site": third_result.site
    }
    
    # Print summary
    print("\n" + "="*60)
    if valid_prices:
        print(f"✅ SUCCESS: Found {len(valid_prices)} price(s)")
        print(f"  • Lowest: ${min(valid_prices)}")
        print(f"  • Highest: ${max(valid_prices)}")
        if len(valid_prices) >= 2:
            print(f"  • Potential Savings: ${max(valid_prices) - min(valid_prices)}")
    else:
        print("⚠️  WARNING: No prices found")
        print("  Suggestions:")
        print("  • Try with --query parameter")
        print("  • Use --bestbuy flag for alternative site")
        print("  • Check if product is still available")
    print("="*60)
    
    return BenchmarkResult(
        input_data={"newegg_item": item_number, "search_query": search_query},
        results=results,
        summary=summary,
        metadata=metadata
    )

# -------------------- CLI Interface --------------------
def main():
    parser = argparse.ArgumentParser(
        description="Consumer Electronics Price Benchmark MVP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
%(prog)s N82E16820147795
%(prog)s N82E16820147795 --query "Samsung SSD 970 EVO"
%(prog)s N82E16834360760 --bestbuy

COMMON TEST ITEMS:
N82E16820147795 - Samsung SSD
N82E16834360760 - Lenovo Laptop
N82E16824011439 - ASUS Monitor

IMPLEMENTATION NOTES:
This MVP demonstrates price comparison across major e-commerce sites.
Production version would use official APIs and proxy rotation.
        """
    )
    
    parser.add_argument('item_number',
                    help='Newegg item number (e.g., N82E16820147795)')
    parser.add_argument('--query',
                    help='Manual search query for other sites')
    parser.add_argument('--bestbuy',
                    action='store_true',
                    help='Use Best Buy instead of eBay')
    parser.add_argument('--output',
                    choices=['json', 'pretty'],
                    default='pretty',
                    help='Output format (default: pretty)')
    
    args = parser.parse_args()
    
    # Run benchmark
    result = run_benchmark(
        item_number=args.item_number,
        manual_query=args.query,
        use_bestbuy=args.bestbuy
    )
    
    # Output results
    print("\n" + "="*60)
    print(" OUTPUT")
    print("="*60)
    
    if args.output == 'json':
        print(json.dumps(asdict(result), indent=2, default=str))
    else:
        # Pretty print for demonstration
        print(f"\n📊 PRICE COMPARISON RESULTS")
        print(f"   Item: {args.item_number}")
        print(f"   Query: {result.metadata['query_used']}")
        print(f"\n💰 PRICES FOUND:")
        for r in result.results:
            if r['price']:
                print(f"   • {r['site'].upper()}: ${r['price']}")
            else:
                print(f"   • {r['site'].upper()}: {r['status']}")
        
        if result.summary['lowest_price']:
            print(f"\n💡 INSIGHTS:")
            print(f"   Best Price: ${result.summary['lowest_price']}")
            print(f"   Average: ${result.summary['average_price']:.2f}")
            if result.summary['savings_potential'] > 0:
                print(f"   Max Savings: ${result.summary['savings_potential']:.2f}")
    
    print("\n✨ Execution completed in", result.metadata['execution_time'])
    print("="*60 + "\n")

if __name__ == "__main__":
    main()