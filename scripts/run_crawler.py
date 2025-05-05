#!/usr/bin/env python3

import os
import sys
import json
import argparse
import logging
import subprocess
from datetime import datetime
from pathlib import Path

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

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run e-commerce product URL crawler.')
    
    parser.add_argument('--domains', nargs='+', help='List of domains to crawl')
    parser.add_argument('--domains-file', default='domains.json', help='Path to domains configuration file')
    parser.add_argument('--max-products', type=int, help='Maximum number of products per domain')
    parser.add_argument('--max-depth', type=int, help='Maximum crawl depth')
    parser.add_argument('--output-dir', default='output', help='Directory for output files')
    
    return parser.parse_args()

def load_domains(domains_file):
    """Load domains from configuration file."""
    try:
        with open(domains_file, 'r') as f:
            return json.load(f).keys()
    except (IOError, json.JSONDecodeError) as e:
        logging.error(f"Failed to load domains from {domains_file}: {e}")
        return []

def main():
    """Main function to run the crawler."""
    logger = setup_logger()
    args = parse_arguments()
    
    # Ensure output directory exists
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Determine which domains to crawl
    if args.domains:
        domains_to_crawl = args.domains
    else:
        domains_to_crawl = load_domains(args.domains_file)
    
    if not domains_to_crawl:
        logger.error("No domains specified for crawling. Exiting.")
        return
    
    logger.info(f"Starting crawl process for {len(domains_to_crawl)} domains...")
    
    # Set up command-line arguments
    settings_args = []
    if args.max_products:
        settings_args.extend(['-s', f'MAX_PRODUCTS_PER_DOMAIN={args.max_products}'])
    if args.max_depth:
        settings_args.extend(['-s', f'MAX_DEPTH={args.max_depth}'])
    settings_args.extend(['-s', f'OUTPUT_DIR={args.output_dir}'])
    
    # Run Scrapy crawl for each domain
    for domain in domains_to_crawl:
        logger.info(f"Starting crawler for domain: {domain}")
        try:
            cmd = ['scrapy', 'crawl', 'ecommerce', 
                   '-a', f'domain={domain}',
                   '-a', f'config_file={args.domains_file}']
            cmd.extend(settings_args)
            
            logger.info(f"Running command: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error crawling {domain}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error crawling {domain}: {e}")
    
    logger.info("Crawl process complete!")

if __name__ == "__main__":
    main()