# Technical Assessment 📝

![Python](https://img.shields.io/badge/python-3.9%2B-blue)

This repository contains my solutions for a technical assessment.  
It includes two independent problems, each organized in its own folder.

## 📂 Repository Structure

- **[Question1](Question1/)** – Subset Sum Solver
  - Python implementation to solve the subset sum problem.
  - Includes a `sample.csv` input and a simple solver script.

- **[Question2](Question2/)** – Price Benchmark MVP
  - A lightweight CLI that benchmarks prices from Newegg, Amazon, and BestBuy/eBay.
  - Uses `requests` and `BeautifulSoup` for scraping.
  - Includes `requirements.txt` and a sample output in JSON.

## 🚀 How to Run

Each folder contains its own instructions in a `README.md` file.  
To set up the environment and dependencies:

```bash
# Create and activate venv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies for Question 2
pip install -r Question2/requirements.txt
```

