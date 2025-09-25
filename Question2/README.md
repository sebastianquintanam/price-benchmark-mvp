## Price Benchmark MVP 🛒

A lightweight price comparison CLI that, given a Newegg itemNumber, fetches a product price from Newegg, Amazon, and a third site (eBay by default or Best Buy with a flag). Designed as a pragmatic MVP to demonstrate approach, trade-offs, and next-step priorities.

## Table of Contents

Overview

Features

Install

Usage

Examples

Architecture & Implementation

Limitations

Next Iteration Priorities

Troubleshooting

Sample Project Structure

Author

## Overview

Goal: Build an MVP that takes a Newegg itemNumber and returns price information from Newegg, Amazon, and one other retailer.
Business value: quick competitive pricing checks to support pricing decisions, promo validation, and market scanning.

## Features

- Multi-site lookup: Newegg (via item page), Amazon search, and eBay/BestBuy search.

- Robust fallback: if a site blocks or markup changes, the tool returns a clear status (e.g., blocked, no_results, no_price) instead of crashing.

- Configurable: override search text with --query, switch the third site with --bestbuy, choose pretty or JSON output.

- Simple CLI: fast to run, small dependency footprint.


## Install

## Tested with Python 3.10+.

# From the Question2 folder (recommended to use a venv)
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

## requirements.txt
requests==2.31.0
beautifulsoup4==4.12.2
lxml==4.9.3

## Usage

# Basic: try to read title from Newegg and compare
python price_benchmark_selenium.py N82E16820147795

# Recommended when Newegg blocks (pass a product title/query)
python price_benchmark_selenium.py N82E16820147795 --query "Samsung 970 EVO Plus SSD"

# Use Best Buy instead of eBay as the third site
python price_benchmark_selenium.py N82E16820147795 --query "Samsung 970 EVO Plus SSD" --bestbuy

# JSON output (for integration)
python price_benchmark_selenium.py N82E16820147795 --query "Samsung 970 EVO Plus SSD" --output json

## Common test items
N82E16820147795  Samsung 970 EVO Plus SSD
N82E16834360760  Lenovo IdeaPad (laptop)
N82E16824011439  ASUS Monitor


## JSON output (truncated):

{
  "input_data": {"newegg_item": "N82E16820147795", "search_query": "Samsung 970 EVO Plus SSD"},
  "results": [
    {"site": "newegg", "price": null, "status": "error"},
    {"site": "amazon", "price": "144.99", "status": "success"},
    {"site": "ebay", "price": null, "status": "no_results"}
  ],
  "summary": {"total_sites": 3, "successful_sites": 1, "lowest_price": 144.99}
}

## Architecture & Implementation

# High-level flow
1. Newegg: fetch the product page by itemNumber, try to extract title/price using meta tags and JSON-LD.
2. Query build: if Newegg is blocked or no title is found, you can supply --query (product title) manually.
3. Amazon + third site: search for the query and extract the first visible price. The third site is eBay by default or Best Buy with --bestbuy.
4. Aggregation: compute simple stats (lowest price, average), and print pretty or JSON output.

# Why this approach
- Minimal dependencies, quick iteration, and clear separation: one scraper per site + an orchestrator.
- Resilient: if one site blocks or changes DOM, the run continues and returns a diagnostic status.

# Key technical choices
- requests + BeautifulSoup with multiple CSS selectors and JSON-LD/meta fallbacks.
- Randomized User-Agents, timeouts, and defensive parsing to avoid crashes.
- CLI ergonomics: --query, --bestbuy, --output json.

## Limitations
- Anti-bot protections (403/429/503/CAPTCHA) on major retailers can block scraping; the tool reports blocked/error and continues.
- DOM fragility: small HTML changes can break selectors.
- Search ambiguity: when using text search, results can be variants/sponsored listings.
- Non-normalized prices: taxes, shipping, seller type, and condition are not standardized.

These constraints are expected for a first MVP without proxies or official APIs. The design focuses on clarity, resilience, and a concrete path forward.

## Next Iteration Priorities

# Official APIs
- Amazon PA-API or Keepa, eBay Browse API, Newegg partner endpoints.
- Match by UPC/EAN/GTIN instead of plain text.

# Headless browser fallback
- Playwright with smart waits and basic captcha handling for dynamic content.

# Normalization
- Currency, tax/shipping, condition, and seller to compute a comparable effective price.

# Caching & limits
- Redis + rate limiting; unit tests with HTML fixtures.

# Service wrapper
- Simple FastAPI endpoint + Docker for easy deployment.

## Troubleshooting
Symptom	                    Likely cause	              What to try
blocked / 403	        Anti-bot on retailer	Pass --query "Product Title"; try --bestbuy; wait or use VPN/IP rotation in future
no_results	            Query too long/ambiguous	    Shorten to 4–6 keywords; add model/size
no_price	            Result block present, no price	 Try different item or third site
Import errors	       Missing deps / wrong venv	   Install requirements.txt; select venv in VS Code


## Author

Sebastian Quintana Morales
Email: sebastian.quintana.m@gmail.com
GitHub: @sebastianquintanam
LinkedIn: https://www.linkedin.com/in/sebastianquintanam/