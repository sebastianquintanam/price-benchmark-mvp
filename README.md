# Price Benchmark MVP

CLI tool that, given a Newegg item number, fetches the product's price from
Newegg, Amazon, and a third retailer (eBay by default, Best Buy with a flag),
and outputs a structured JSON comparison.

**Stack:** Python · requests · BeautifulSoup

## How it works

The script fetches the product page on Newegg, extracts the product name and
price, then searches the other retailers for the same product, normalizes the
results, and prints a side-by-side price comparison in JSON.

## Run it

​```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python benchmark.py N82E16820147795
​```

Options:

​```
item_number          Newegg item number (e.g., N82E16820147795)
--query QUERY        Manual search query for the other sites
--bestbuy            Use Best Buy instead of eBay
--output {json,pretty}   Output format (default: pretty)
​```

## Example output

## Example output

```json
{
  "input_data": {
    "newegg_item": "N82E16820147795",
    "search_query": "Samsung 970 EVO Plus SSD"
  },
  "results": [
    { "site": "newegg", "price": null, "status": "blocked" },
    { "site": "amazon", "price": "144.99", "currency": "USD",
      "status": "success", "title": "Samsung 970 EVO Plus SSD 1TB" },
    { "site": "ebay", "price": null, "status": "no_results" }
  ],
  "summary": {
    "total_sites": 3,
    "successful_sites": 1,
    "lowest_price": 144.99
  }
}
```

## Limitations

Scrapers depend on each retailer's HTML structure. As of 2026 the original
selectors no longer match (Newegg changed its markup, eBay returns 403 for
non-browser requests), so live runs return no prices — see
`sample_output.json` for the output format from when the scrapers worked.
The script handles these failures gracefully instead of crashing.

There's no caching, proxying, or rate limiting. A production version would
use official retailer APIs and proxy rotation — this is an MVP built to
demonstrate the approach and trade-offs.