import re
import json
import logging
from urllib.parse import urlparse, urljoin
from datetime import datetime

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule, CrawlSpider

from crawler.items import ProductURL
from crawler.utils.url_helpers import (
    is_valid_url, normalize_url, get_domain, 
    is_product_url, is_same_domain, clean_url
)

class EcommerceSpider(CrawlSpider):
    """Generic spider for e-commerce websites."""
    
    name = 'ecommerce'
    
    # Common product URL patterns for all e-commerce sites
    common_product_patterns = [
        r'/product[s]?/',
        r'/p/',
        r'/item[s]?/',
        r'/pd/',
        r'/shop/product[s]?',
        r'/good[s]?/'
    ]
    
    # URLs to exclude (common non-product pages)
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
    
    def __init__(self, domain=None, config_file=None, *args, **kwargs):
        self.domain = domain
        self.config_file = config_file or 'domains.json'
        
        # Load domain configs
        self.domain_configs = self._load_configs()
        
        # Configure the spider based on the domain
        if domain and domain in self.domain_configs:
            self._configure_for_domain(domain)
        else:
            # If no specific domain, use default configuration
            self.start_urls = ['https://www.example.com']
            self.allowed_domains = ['example.com']
            self.site_specific_patterns = []
        
        self.products_found = 0
        self.site_specific_patterns = getattr(self, 'site_specific_patterns', [])
        self.all_patterns = self.common_product_patterns + self.site_specific_patterns
        
        # Call the parent constructor after setting up our attributes
        super(EcommerceSpider, self).__init__(*args, **kwargs)
        
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(EcommerceSpider, cls).from_crawler(crawler, *args, **kwargs)
        # Get settings from crawler
        spider.max_products = crawler.settings.getint('MAX_PRODUCTS_PER_DOMAIN')
        spider.max_depth = crawler.settings.getint('MAX_DEPTH', 5)
        # Set up rules after we have all configuration
        spider._set_rules()
        return spider
    
    def _load_configs(self):
        """Load domain-specific configurations from a JSON file."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logging.error(f"Failed to load domain configs: {e}")
            return {}
    
    def _configure_for_domain(self, domain):
        """Configure the spider for a specific domain."""
        config = self.domain_configs[domain]
        
        self.allowed_domains = [domain]
        self.start_urls = config.get('start_urls', [f"https://www.{domain}/"])
        self.site_specific_patterns = config.get('product_patterns', [])
    
    def _set_rules(self):
        """Set up the crawling rules."""
        self.rules = (
            # Rule to follow category links
            Rule(
                LinkExtractor(
                    deny=self.exclude_patterns,
                    deny_domains=['facebook.com', 'twitter.com', 'instagram.com', 'youtube.com']
                ), 
                callback='parse_links', 
                follow=True
            ),
        )
        # Needed because we're setting rules after initialization
        self._compile_rules()
        
    def parse_start_url(self, response):
        """Process the start URL."""
        return self.parse_links(response)
        
    def parse_links(self, response):
        """
        Parse links from response and yield product URLs.
        Also follow other links for further crawling.
        """
        domain = get_domain(response.url)
        
        # Check if we've reached the product limit
        if self.max_products and self.products_found >= self.max_products:
            self.logger.info(f"Reached maximum number of products ({self.max_products}) for {domain}")
            return
            
        # Extract all links from the page
        links = response.css('a::attr(href)').getall()
        
        # Process each link
        for link in links:
            # Build absolute URL
            url = urljoin(response.url, link)
            
            # Skip invalid URLs
            if not is_valid_url(url):
                continue
                
            # Skip URLs from different domains
            if not is_same_domain(url, response.url):
                continue
                
            # Clean and normalize the URL
            url = clean_url(normalize_url(url))
            
            # Check if this is a product URL
            if self.is_product_url(url):
                # Skip if we've reached the product limit
                if self.max_products and self.products_found >= self.max_products:
                    return
                    
                self.products_found += 1
                
                yield ProductURL(
                    url=url,
                    domain=domain,
                    found_on=response.url,
                    discovery_time=datetime.now().isoformat()
                )
    
    def is_product_url(self, url):
        """Check if URL is likely a product page."""
        # Use both common patterns and site-specific patterns
        for pattern in self.all_patterns:
            if re.search(pattern, url):
                return True
                
        return False