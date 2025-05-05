import os
import json
from datetime import datetime
from scrapy.exceptions import DropItem
from pathlib import Path

class DuplicatesPipeline:
    """Pipeline to remove duplicate product URLs."""
    
    def __init__(self):
        self.urls_seen = set()
    
    def process_item(self, item, spider):
        url = item['url']
        if url in self.urls_seen:
            raise DropItem(f"Duplicate item found: {url}")
        self.urls_seen.add(url)
        return item

class OutputPipeline:
    """Pipeline to save product URLs to a file per domain."""
    
    def __init__(self, output_dir):
        self.output_dir = output_dir or 'output'  # Default to 'output' if None
        self.items_per_domain = {}
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            output_dir=crawler.settings.get('OUTPUT_DIR', 'output')  # Default to 'output'
        )
    
    def open_spider(self, spider):
        # Create output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    def process_item(self, item, spider):
        domain = item['domain']
        if domain not in self.items_per_domain:
            self.items_per_domain[domain] = []
        
        self.items_per_domain[domain].append(dict(item))
        return item
    
    def close_spider(self, spider):
        # Save items for each domain to separate files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save individual domain files
        for domain, items in self.items_per_domain.items():
            filename = f"{domain.replace('.', '_')}_{timestamp}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w') as f:
                # Extract just the URLs for cleaner output
                urls = [item['url'] for item in items]
                json.dump(urls, f, indent=2)
        
        # Save combined results
        combined_file = os.path.join(self.output_dir, f"all_domains_{timestamp}.json")
        with open(combined_file, 'w') as f:
            result = {domain: [item['url'] for item in items] 
                      for domain, items in self.items_per_domain.items()}
            json.dump(result, f, indent=2)
            
        spider.logger.info(f"Found {sum(len(items) for items in self.items_per_domain.values())} product URLs across {len(self.items_per_domain)} domains")
        for domain, items in self.items_per_domain.items():
            spider.logger.info(f"  - {domain}: {len(items)} products")