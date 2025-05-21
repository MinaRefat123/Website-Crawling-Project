# Intelligent Web Crawler & Analyzer

## Overview
This project is a Python-based web crawler that analyzes website crawlability, extracts metadata (titles, descriptions, links), detects JavaScript-heavy content and APIs/RSS feeds, and visualizes results via a Streamlit dashboard. It stores data in SQLite, supports CSV export, and uses Gulp for automation.

## Features
- **Crawlability Analysis**: Parses `robots.txt` for allowed paths, crawl delay, and sitemap URLs.
- **Content Extraction**: Extracts titles, descriptions, and links with retry logic and pagination support.
- **JS/API Detection**: Identifies JS-heavy content (via Playwright) and checks for APIs and RSS feeds.
- **Visualization**: Streamlit dashboard with metrics, tabs, Plotly charts, and recommendations.
- **Storage**: SQLite database with CSV export.
- **Automation**: Gulp tasks for linting, testing, and deployment preparation.

## Directory Structure
```
web-crawler/
├── crawler.py
├── gulpfile.js
├── package.json
├── requirements.txt
├── README.md
├── tests/
│   └── test_crawler.py
└── dist/
```

## Setup Instructions
### Prerequisites
- Python 3.11 (recommended; avoid 3.13 due to Playwright compatibility issues)
- Node.js 16+ and npm
- Git (optional)

### Steps
1. **Clone or Set Up the Project**:
   ```bash
   mkdir web-crawler
   cd web-crawler
   ```
   - Copy the provided files (`crawler.py`, `gulpfile.js`, `package.json`, `requirements.txt`, `tests/test_crawler.py`) into the directory.

2. **Install Python Dependencies**:
   - Create a virtual environment (optional but recommended):
     ```bash
     python -m venv venv
     venv\Scripts\activate  # Windows
     ```
   - Install packages:
     ```bash
     pip install -r requirements.txt
     playwright install
     ```

3. **Install Node.js Dependencies**:
   - Install Gulp and dependencies:
     ```bash
     npm install
     ```
   - Fix vulnerabilities if prompted:
     ```bash
     npm audit fix
     ```

4. **Run Gulp Tasks** (optional):
   - Lint, test, and build:
     ```bash
     npx gulp
     ```

## Usage
1. **Run the Application**:
   - Start Streamlit:
     ```bash
     streamlit run crawler.py
     ```
   - Access at `http://localhost:8501`.

2. **Analyze a Website**:
   - Enter a URL (e.g., `https://example.com` or your assigned website).
   - Click "Analyze Website".
   - View results:
     - **Crawlability**: Can crawl, crawl delay, sitemap URLs.
     - **Content**: Titles, descriptions, links (with Plotly histogram).
     - **JS/API**: JS-heavy status, API detection, RSS feeds.
     - **Recommendations**: Suggested crawling methods.
     - **Download**: Export results as CSV.

## Deployment on Streamlit Cloud
1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/your-repo/web-crawler.git
   git push -u origin main
   ```

2. **Deploy**:
   - Go to [share.streamlit.io](https://share.streamlit.io).
   - Connect your GitHub repository.
   - Set `crawler.py` as the entry point.
   - Deploy and access the app URL.

## Findings
### Development Findings
- **Crawlability**: Successfully parsed `robots.txt` for sites like `https://example.com`, showing allowed paths and sitemap URLs.
- **Content Extraction**: Extracted up to 10 titles, descriptions, and 50 links per page, with pagination support (e.g., detected "Next" links).
- **Visualization**: Plotly histogram effectively visualized link distribution.
- **Storage**: SQLite database (`crawled_data.db`) stored results, enabling CSV export.

### Execution Findings on Your Device
- **Setup**: Dependencies installed successfully after initial issues (`pytest` and `streamlit` not recognized resolved via `pip install -r requirements.txt`).
- **Playwright Issue**: Persistent `NotImplementedError` due to Python 3.13 incompatibility blocked JS analysis. Recommended downgrading to Python 3.11.
- **Workaround**: Enhanced exception handling in `crawler.py` allowed static content analysis to proceed, returning default values for JS/API data.
- **Results**:
  - Crawlability and content extraction worked for `https://example.com`.
  - JS/API detection failed (returned `False`/`None`) due to Playwright issues.
  - Recommendations adjusted to focus on static content extraction (`aiohttp` and `BeautifulSoup`).

## Challenges
- **Python 3.13 Incompatibility**: Playwright failed with `NotImplementedError` due to Python 3.13's asyncio subprocess changes. Mitigated by recommending Python 3.11 and adding fallback logic.
- **Error Handling**: Initial `'NotImplementedError' object has no attribute 'get'` error resolved by ensuring `asyncio.gather` results are dictionaries.
- **Duplicate Code**: Removed duplicate `check_js_and_api` function to prevent overwriting.
- **Website Access**: Some sites (e.g., `https://www.cnet.com`) may block crawling; `https://example.com` worked reliably.

## Reflections
- **Efficiency**: Using `asyncio` for concurrent tasks improved performance.
- **Robustness**: Exception handling was critical for handling Playwright failures.
- **Future Improvements**: Use a Playwright-compatible Python version or alternative JS rendering libraries (e.g., `selenium`) if issues persist.