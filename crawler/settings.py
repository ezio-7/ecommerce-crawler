BOT_NAME = 'ecommerce_crawler'

SPIDER_MODULES = ['crawler.spiders']
NEWSPIDER_MODULE = 'crawler.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 32
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# Configure a delay for requests for the same website
DOWNLOAD_DELAY = 0.5

# Disable cookies
COOKIES_ENABLED = False

# Set the user agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Enable and configure HTTP caching
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400
HTTPCACHE_DIR = 'httpcache'

# Configure item pipelines
ITEM_PIPELINES = {
    'crawler.pipelines.DuplicatesPipeline': 300,
    'crawler.pipelines.OutputPipeline': 500,
}

# Maximum crawl depth
MAX_DEPTH = 5

# Maximum number of products per domain (for testing or limits)
MAX_PRODUCTS_PER_DOMAIN = 1000  # Set to None for unlimited

# Output file settings
OUTPUT_DIR = 'output'