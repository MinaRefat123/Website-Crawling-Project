import asyncio
import logging
import sqlite3
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser
import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import feedparser
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('crawled_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS crawl_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT,
        timestamp TEXT,
        titles TEXT,
        descriptions TEXT,
        links TEXT,
        can_crawl BOOLEAN,
        crawl_delay TEXT,
        sitemap_urls TEXT,
        is_js_heavy BOOLEAN,
        api_detected BOOLEAN,
        rss_feeds TEXT
    )''')
    conn.commit()
    conn.close()

async def analyze_robots_txt(base_url):
    """Analyze robots.txt for crawlability rules."""
    robots_url = urljoin(base_url, "/robots.txt")
    parser = RobotFileParser()
    parser.set_url(robots_url)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(robots_url, timeout=10) as response:
                if response.status == 200:
                    parser.parse((await response.text()).splitlines())
                    return {
                        "can_crawl": parser.can_fetch("*", base_url),
                        "crawl_delay": parser.crawl_delay("*") or "Not specified",
                        "sitemap_urls": parser.site_maps() or ["None found"],
                        "disallowed_paths": parser.disallow_all
                    }
    except Exception as e:
        logger.error(f"Failed to parse robots.txt: {e}")
        return {"error": f"Failed to parse robots.txt: {e}"}
    return {"error": "No robots.txt found"}

async def extract_content(url):
    """Extract meaningful content with retry and pagination."""
    async with aiohttp.ClientSession() as session:
        for attempt in range(3):
            try:
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status()
                    soup = BeautifulSoup(await response.text(), 'html.parser')
                    data = {
                        "titles": [tag.get_text().strip() for tag in soup.find_all(['h1', 'h2', 'h3'])][:10],
                        "descriptions": [meta.get("content", "") for meta in soup.find_all("meta", attrs={"name": "description"})],
                        "links": [urljoin(url, a.get("href")) for a in soup.find_all("a", href=True)][:50],
                        "next_page": None
                    }
                    next_page = soup.find("a", string="Next") or soup.find("a", attrs={"rel": "next"})
                    if next_page and next_page.get("href"):
                        data["next_page"] = urljoin(url, next_page.get("href"))
                    return data
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == 2:
                    return {"error": f"Extraction failed: {e}"}
                await asyncio.sleep(2 ** attempt)

async def check_js_and_api(url):
    """Check for JS-heavy content and APIs."""
    result = {"is_js_heavy": False, "api_detected": False, "rss_feeds": []}
    
    # Check JavaScript-heavy content
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(url, timeout=30000)
                content_with_js = await page.content()
                await browser.close()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10) as response:
                        content_without_js = await response.text()
                        result["is_js_heavy"] = len(content_with_js) > len(content_without_js) * 1.5
            except Exception as e:
                logger.error(f"JS check failed: {e}")
                result["is_js_heavy"] = False
    except Exception as e:
        logger.error(f"Playwright failed: {e}")
        result["is_js_heavy"] = False
    
    # Check RSS feeds
    rss_url = urljoin(url, "/rss")
    feed = feedparser.parse(rss_url)
    if feed.entries:
        result["rss_feeds"].append(rss_url)
    
    # Check API endpoints
    api_paths = ["/api", "/v1/api", "/json"]
    async with aiohttp.ClientSession() as session:
        for path in api_paths:
            try:
                async with session.get(urljoin(url, path), timeout=5) as response:
                    if response.status == 200 and "application/json" in response.headers.get("Content-Type", ""):
                        result["api_detected"] = True
                        break
            except:
                continue
    
    return result

def store_data(url, robots_data, content_data, js_api_data):
    """Store crawled data in SQLite database."""
    conn = sqlite3.connect('crawled_data.db')
    c = conn.cursor()
    c.execute('''INSERT INTO crawl_results (
        url, timestamp, titles, descriptions, links, can_crawl, crawl_delay, sitemap_urls,
        is_js_heavy, api_detected, rss_feeds
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
        url,
        datetime.now().isoformat(),
        str(content_data.get("titles", [])),
        str(content_data.get("descriptions", [])),
        str(content_data.get("links", [])),
        robots_data.get("can_crawl", False),
        robots_data.get("crawl_delay", "Unknown"),
        str(robots_data.get("sitemap_urls", [])),
        js_api_data.get("is_js_heavy", False),
        js_api_data.get("api_detected", False),
        str(js_api_data.get("rss_feeds", []))
    ))
    conn.commit()
    conn.close()

async def analyze_website(url):
    """Main function to analyze website concurrently."""
    init_db()
    tasks = [
        analyze_robots_txt(url),
        extract_content(url),
        check_js_and_api(url)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle exceptions and ensure dictionary return
    robots_data = results[0] if isinstance(results[0], dict) else {"error": str(results[0])}
    content_data = results[1] if isinstance(results[1], dict) else {"error": str(results[1])}
    js_api_data = results[2] if isinstance(results[2], dict) else {"is_js_heavy": False, "api_detected": False, "rss_feeds": []}
    
    store_data(url, robots_data, content_data, js_api_data)
    return robots_data, content_data, js_api_data

def main():
    """Streamlit dashboard with modern GUI."""
    st.set_page_config(page_title="Web Crawler & Analyzer", layout="wide", page_icon="🌐")
    st.markdown("""
        <style>
        .main { background-color: #f5f5f5; }
        .stButton>button { background-color: #4CAF50; color: white; }
        .stTextInput>div>input { border-radius: 5px; }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("Intelligent Web Crawler & Analyzer")
    st.markdown("Analyze a website's crawlability, extract metadata, and get data access recommendations.")
    
    # Input and Analysis
    with st.form(key="url_form"):
        url = st.text_input("Enter Website URL", value="https://example.com", help="E.g., https://example.com")
        submit = st.form_submit_button("Analyze Website")
    
    if submit:
        with st.spinner("Crawling and analyzing..."):
            try:
                robots_data, content_data, js_api_data = asyncio.run(analyze_website(url))
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                logger.error(f"Analysis error: {e}")
                return
        
        # Crawlability Analysis
        st.subheader("Crawlability Analysis", anchor="crawlability")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Can Crawl", "Yes" if robots_data.get("can_crawl", False) else "No")
        with col2:
            st.metric("Crawl Delay", robots_data.get("crawl_delay", "Unknown"))
        with col3:
            st.write("**Sitemap URLs**")
            st.write(", ".join(robots_data.get("sitemap_urls", ["None"])))
        
        # Content Extraction
        st.subheader("Extracted Content", anchor="content")
        if "error" not in content_data:
            tabs = st.tabs(["Titles", "Descriptions", "Links"])
            with tabs[0]:
                for title in content_data.get("titles", []):
                    st.write(f"- {title}")
            with tabs[1]:
                for desc in content_data.get("descriptions", []):
                    st.write(f"- {desc}")
            with tabs[2]:
                links = content_data.get("links", [])
                if links:
                    df = pd.DataFrame({"Links": links})
                    fig = px.histogram(df, x="Links", title="Link Distribution", nbins=20,
                                     color_discrete_sequence=["#4CAF50"])
                    fig.update_layout(xaxis_title="Links", yaxis_title="Count", showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write("No links found.")
        
        # JS and API Analysis
        st.subheader("JS & API Analysis", anchor="js-api")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("JavaScript Heavy", "Yes" if js_api_data.get("is_js_heavy", False) else "No")
        with col2:
            st.metric("API Detected", "Yes" if js_api_data.get("api_detected", False) else "No")
        with col3:
            st.write("**RSS Feeds**")
            st.write(", ".join(js_api_data.get("rss_feeds", ["None"])))
        
        # Recommendations
        st.subheader("Recommendations", anchor="recommendations")
        recommendations = []
        if robots_data.get("can_crawl", False):
            recommendations.append("Use aiohttp with BeautifulSoup for efficient static content extraction.")
        if js_api_data.get("is_js_heavy", False):
            recommendations.append("Employ Playwright for rendering JavaScript-heavy content.")
        if js_api_data.get("api_detected", False):
            recommendations.append("Investigate API endpoints for structured data access.")
        if js_api_data.get("rss_feeds", []):
            recommendations.append("Leverage RSS feeds for real-time content updates.")
        if not recommendations:
            recommendations.append("No specific recommendations; check website for additional access methods.")
        for rec in recommendations:
            st.write(f"- {rec}")
        
        # Data Download
        st.subheader("Download Data", anchor="download")
        conn = sqlite3.connect('crawled_data.db')
        df = pd.read_sql_query("SELECT * FROM crawl_results WHERE url = ?", conn, params=(url,))
        conn.close()
        st.download_button(
            label="Download Crawled Data (CSV)",
            data=df.to_csv(index=False),
            file_name=f"crawled_data_{url.replace('https://', '').replace('/', '_')}.csv",
            mime="text/csv",
            help="Download the analysis results as a CSV file."
        )

if __name__ == "__main__":
    main()