#!/usr/bin/env python

from crawler.spiders.ecommerce_spider import EcommerceSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import sys

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python run.py <domain>")
        sys.exit(1)
        
    domain = sys.argv[1]
    
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(EcommerceSpider, domain=domain, config_file='domains.json')
    process.start()