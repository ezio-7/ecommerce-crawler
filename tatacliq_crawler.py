# tatacliq_crawler.py

import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Create output directory
output_dir = 'output'
Path(output_dir).mkdir(parents=True, exist_ok=True)

def setup_driver():
    """Set up and return a Selenium WebDriver."""
    options = Options()
    # Uncomment next line if you want to run in headless mode (no browser window)
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')  # Try to avoid detection
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Set window size
    driver.set_window_size(1920, 1080)
    
    return driver

def extract_product_urls(driver, current_url):
    """Extract product URLs from the current page."""
    product_urls = []
    
    # Wait for the page to load
    time.sleep(3)
    
    # Get page source
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all links
    for a_tag in soup.find_all('a', href=True):
        href = a_tag.get('href', '')
        if '/p-' in href:
            # Convert to absolute URL if needed
            absolute_url = urljoin(current_url, href)
            product_urls.append(absolute_url)
            logger.info(f"Found product URL: {absolute_url}")
    
    return product_urls

def crawl_category_pages(driver, start_url, max_products=10):
    """Crawl category pages to find product URLs."""
    product_urls = []
    
    # Start with the home page
    logger.info(f"Navigating to home page: {start_url}")
    driver.get(start_url)
    time.sleep(5)  # Let the home page load fully
    
    # Find category links to navigate to
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for navigation links or category links
    category_links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag.get('href', '')
        # Skip irrelevant links
        if not href or href.startswith('#') or href.startswith('javascript:'):
            continue
        
        # Identify potential category links - adjust these patterns based on TataCliq's structure
        if '/c-' in href or 'category' in href or 'department' in href:
            absolute_url = urljoin(start_url, href)
            category_links.append(absolute_url)
    
    # Keep a limited number of category links
    category_links = category_links[:5]  # Start with just a few categories
    
    # Navigate to each category page
    for category_url in category_links:
        logger.info(f"Navigating to category: {category_url}")
        try:
            driver.get(category_url)
            time.sleep(5)  # Let the category page load
            
            # Extract product URLs
            new_product_urls = extract_product_urls(driver, category_url)
            logger.info(f"Found {len(new_product_urls)} products on category page: {category_url}")
            
            # Add to our collection
            product_urls.extend(new_product_urls)
            
            # Check if we've reached our limit
            if len(product_urls) >= max_products:
                logger.info(f"Reached maximum number of products: {max_products}")
                break
        
        except Exception as e:
            logger.error(f"Error navigating to {category_url}: {e}")
    
    # Ensure we have unique URLs only
    product_urls = list(set(product_urls))
    
    # Limit to max_products
    return product_urls[:max_products]

def main():
    """Main function to crawl TataCliq."""
    try:
        driver = setup_driver()
        
        # Crawl TataCliq
        logger.info("Starting TataCliq crawler...")
        product_urls = crawl_category_pages(driver, "https://www.tatacliq.com/", max_products=10)
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"tatacliq_com_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(product_urls, f, indent=2)
        
        logger.info(f"Found {len(product_urls)} product URLs")
        logger.info(f"Results saved to {filepath}")
        
        # Create or update the combined results file
        try:
            combined_file = os.path.join(output_dir, "all_domains_latest.json")
            combined_data = {}
            
            # Read existing data if the file exists
            if os.path.exists(combined_file):
                with open(combined_file, 'r') as f:
                    combined_data = json.load(f)
            
            # Update with new data
            combined_data['tatacliq'] = product_urls
            
            # Write back the updated data
            with open(combined_file, 'w') as f:
                json.dump(combined_data, f, indent=2)
                
            logger.info(f"Updated combined results in {combined_file}")
        except Exception as e:
            logger.error(f"Error updating combined results: {e}")
    
    except Exception as e:
        logger.error(f"Error in TataCliq crawler: {e}")
    
    finally:
        # Clean up
        try:
            driver.quit()
        except:
            pass
        
        logger.info("TataCliq crawler complete!")

if __name__ == "__main__":
    main()