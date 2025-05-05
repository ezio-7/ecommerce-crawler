#!/usr/bin/env python3

import os
import sys
import json
import time
import argparse
import logging
import requests
from urllib.parse import urljoin, urlparse
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from collections import deque, defaultdict
import re
import tldextract

# Configure logging
def setup_logger():
    """Set up logging."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'crawl_{timestamp}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()

# URL Helper Functions
def is_valid_url(url):
    """Check if URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def normalize_url(url):
    """Normalize URL by removing fragments, some query parameters, etc."""
    parsed = urlparse(url)
    # Remove fragments
    normalized = parsed._replace(fragment='')
    # Convert to string
    return normalized.geturl()

def get_domain(url):
    """Extract domain from URL."""
    ext = tldextract.extract(url)
    return f"{ext.domain}.{ext.suffix}"

def is_product_url(url, patterns=None):
    """
    Determine if a URL is likely a product page based on common patterns.
    """
    # Default patterns for product URLs
    default_patterns = [
        r'/product[s]?/',
        r'/p/',
        r'/item[s]?/',
        r'/pd/',
        r'/shop/product[s]?',
        r'/good[s]?/'
    ]
    
    patterns = patterns or default_patterns
    
    # Check if URL matches any pattern
    for pattern in patterns:
        if re.search(pattern, url):
            return True
            
    return False

def is_same_domain(url1, url2):
    """Check if two URLs belong to the same domain."""
    domain1 = tldextract.extract(url1)
    domain2 = tldextract.extract(url2)
    
    return domain1.domain == domain2.domain and domain1.suffix == domain2.suffix

def clean_url(url):
    """Clean the URL by removing unnecessary parameters."""
    parsed = urlparse(url)
    # Remove parameters that cause duplicates in e-commerce sites
    cleaned = parsed._replace(
        query=re.sub(r'utm_[a-zA-Z]+=[^&]*&?', '', parsed.query)
    )
    return cleaned.geturl()

# Exclude patterns for URLs that are definitely not product pages
exclude_patterns = [
    r'/login',
    r'/register',
    r'/cart',
    r'/checkout',
    r'/wishlist',
    r'/account',
    r'/blog',
    r'/article',
    r'/search',
    r'/contact',
    r'/about',
    r'/faq',
    r'/help',
    r'/support',
    r'/privacy',
    r'/terms',
    r'/policy',
    r'/sitemap',
    r'\.xml$',
    r'\.pdf$',
    r'\.jpg$',
    r'\.png$',
    r'\.gif$',
]

# Main Crawler Class
class SimpleEcommerceCrawler:
    """A simple crawler for e-commerce websites that doesn't rely on Scrapy's reactor."""
    
    def __init__(self, domain, config_file='domains.json', output_dir='output', max_products=1000, max_depth=5):
        self.domain = domain
        self.config_file = config_file
        self.output_dir = output_dir
        self.max_products = max_products
        self.max_depth = max_depth
        
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Load domain configs
        self.domain_configs = self._load_configs()
        
        # Configure crawler for this domain
        self._configure_for_domain()
        
        # Initialize crawler state
        self.visited_urls = set()
        self.product_urls = set()
        self.queue = deque()
        
        # Common headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def _load_configs(self):
        """Load domain-specific configurations from a JSON file."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load domain configs: {e}")
            return {}
    
    def _configure_for_domain(self):
        """Configure the crawler for a specific domain."""
        if self.domain not in self.domain_configs:
            logger.error(f"No configuration found for domain: {self.domain}")
            self.start_urls = [f"https://www.{self.domain}/"]
            self.product_patterns = []
        else:
            config = self.domain_configs[self.domain]
            self.start_urls = config.get('start_urls', [f"https://www.{self.domain}/"])
            self.product_patterns = config.get('product_patterns', [])
    
    def is_excluded(self, url):
        """Check if URL matches any exclude pattern."""
        for pattern in exclude_patterns:
            if re.search(pattern, url):
                return True
        return False
    
    def is_product(self, url):
        """Check if URL is likely a product page."""
        # Check domain-specific patterns first
        for pattern in self.product_patterns:
            if re.search(pattern, url):
                return True
        
        # Then check common patterns
        return is_product_url(url)
    
    def fetch_page(self, url):
        """Fetch a page and return its content."""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Failed to fetch {url}: HTTP {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_links(self, html, base_url):
        """Extract links from HTML content."""
        links = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            for a_tag in soup.find_all('a', href=True):
                href = a_tag.get('href', '').strip()
                if href and not href.startswith('javascript:') and not href.startswith('#'):
                    # Convert to absolute URL
                    absolute_url = urljoin(base_url, href)
                    # Clean and normalize URL
                    absolute_url = clean_url(normalize_url(absolute_url))
                    # Check if URL is valid and same domain
                    if is_valid_url(absolute_url) and is_same_domain(absolute_url, base_url):
                        links.append(absolute_url)
        except Exception as e:
            logger.error(f"Error extracting links from {base_url}: {e}")
        
        return links
    
    def crawl(self):
        """Start the crawling process."""
        # Initialize queue with start URLs
        for url in self.start_urls:
            self.queue.append((url, 0))  # (url, depth)
        
        logger.info(f"Starting crawl for domain: {self.domain}")
        logger.info(f"Start URLs: {self.start_urls}")
        
        # Main crawling loop
        while self.queue and len(self.product_urls) < self.max_products:
            # Get next URL from queue
            url, depth = self.queue.popleft()
            
            # Skip if already visited
            if url in self.visited_urls:
                continue
            
            # Mark as visited
            self.visited_urls.add(url)
            
            # Check if this is a product URL
            if self.is_product(url):
                logger.info(f"Found product URL: {url}")
                self.product_urls.add(url)
                
                # Check if we've reached the product limit
                if len(self.product_urls) >= self.max_products:
                    logger.info(f"Reached maximum number of products ({self.max_products})")
                    break
            
            # Stop if we've reached max depth
            if depth >= self.max_depth:
                continue
            
            # Fetch the page
            html = self.fetch_page(url)
            if not html:
                continue
            
            # Extract links from the page
            links = self.extract_links(html, url)
            
            # Add new links to the queue
            for link in links:
                # Skip excluded URLs
                if self.is_excluded(link):
                    continue
                
                # Skip already visited URLs
                if link in self.visited_urls:
                    continue
                
                # Add to queue with incremented depth
                self.queue.append((link, depth + 1))
            
            # Short pause to be nice to the server
            time.sleep(0.5)
        
        logger.info(f"Crawling complete for {self.domain}")
        logger.info(f"Found {len(self.product_urls)} product URLs")
        
        # Save results
        self._save_results()
    
    def _save_results(self):
        """Save the results to files."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save domain-specific file
        filename = f"{self.domain.replace('.', '_')}_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(list(self.product_urls), f, indent=2)
        
        logger.info(f"Results saved to {filepath}")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run e-commerce product URL crawler.')
    
    parser.add_argument('--domains', nargs='+', help='List of domains to crawl')
    parser.add_argument('--domains-file', default='domains.json', help='Path to domains configuration file')
    parser.add_argument('--max-products', type=int, default=10, help='Maximum number of products per domain')
    parser.add_argument('--max-depth', type=int, default=5, help='Maximum crawl depth')
    parser.add_argument('--output-dir', default='output', help='Directory for output files')
    
    return parser.parse_args()

def load_domains(domains_file):
    """Load domains from configuration file."""
    try:
        with open(domains_file, 'r') as f:
            return json.load(f).keys()
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load domains from {domains_file}: {e}")
        return []

def main():
    """Main function to run the crawler."""
    args = parse_arguments()
    
    # Determine which domains to crawl
    if args.domains:
        domains_to_crawl = args.domains
    else:
        domains_to_crawl = load_domains(args.domains_file)
    
    if not domains_to_crawl:
        logger.error("No domains specified for crawling. Exiting.")
        return
    
    logger.info(f"Starting crawl process for {len(domains_to_crawl)} domains...")
    
    # Crawl each domain
    for domain in domains_to_crawl:
        try:
            crawler = SimpleEcommerceCrawler(
                domain=domain,
                config_file=args.domains_file,
                output_dir=args.output_dir,
                max_products=args.max_products,
                max_depth=args.max_depth
            )
            crawler.crawl()
        except Exception as e:
            logger.error(f"Error crawling {domain}: {e}")
    
    # Create a combined results file
    combine_results(args.output_dir)
    
    logger.info("Crawl process complete!")

def combine_results(output_dir):
    """Combine all individual result files into a single file."""
    results = defaultdict(list)
    
    # Get all JSON files in the output directory
    json_files = list(Path(output_dir).glob('*.json'))
    
    if not json_files:
        logger.warning(f"No JSON files found in {output_dir}")
        return
    
    for file_path in json_files:
        # Skip if this is already a combined results file
        if file_path.name.startswith('all_domains_'):
            continue
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                # Extract domain from filename
                filename = file_path.stem
                parts = filename.split('_')
                if len(parts) >= 2:
                    domain = parts[0].replace('_', '.')
                    results[domain].extend(data)
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    # Save combined results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    combined_file = os.path.join(output_dir, f"all_domains_{timestamp}.json")
    
    with open(combined_file, 'w') as f:
        json.dump(dict(results), f, indent=2)
    
    logger.info(f"Combined results saved to {combined_file}")

if __name__ == "__main__":
    main()