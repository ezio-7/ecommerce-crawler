#!/usr/bin/env python3

import os
import json
import argparse
import csv
from collections import defaultdict
from pathlib import Path

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Process and analyze crawler results.')
    
    parser.add_argument('--input-dir', default='output', help='Directory with crawler output files')
    parser.add_argument('--output-file', default='product_urls.json', help='Output JSON file')
    parser.add_argument('--format', choices=['json', 'csv', 'txt'], default='json', help='Output format')
    
    return parser.parse_args()

def merge_results(input_dir):
    """Merge all individual result files."""
    all_results = defaultdict(list)
    
    # Get all JSON files in the input directory
    json_files = list(Path(input_dir).glob('*.json'))
    
    if not json_files:
        print(f"No JSON files found in {input_dir}")
        return all_results
        
    for file_path in json_files:
        # Skip the combined results file
        if file_path.name.startswith('all_domains_'):
            continue
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                # If this is a domain-specific file (list of URLs)
                if isinstance(data, list):
                    # Extract domain from filename
                    filename = file_path.stem
                    # Format is usually domain_timestamp
                    domain = filename.split('_')[0].replace('_', '.')
                    
                    # Add unique URLs
                    for url in data:
                        if url not in all_results[domain]:
                            all_results[domain].append(url)
                
        except json.JSONDecodeError:
            print(f"Error parsing JSON from {file_path}")
            
    return all_results

def export_results(results, output_file, format_type):
    """Export results in the specified format."""
    if format_type == 'json':
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
            
    elif format_type == 'csv':
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Domain', 'URL'])
            
            for domain, urls in results.items():
                for url in urls:
                    writer.writerow([domain, url])
                    
    elif format_type == 'txt':
        with open(output_file, 'w') as f:
            for domain, urls in results.items():
                f.write(f"Domain: {domain}\n")
                f.write("="*50 + "\n")
                for url in urls:
                    f.write(f"{url}\n")
                f.write("\n\n")
                
    print(f"Results exported to {output_file} in {format_type} format")
    
def print_statistics(results):
    """Print statistics about the results."""
    total_domains = len(results)
    total_urls = sum(len(urls) for urls in results.values())
    
    print("\n" + "="*50)
    print(f"Total domains: {total_domains}")
    print(f"Total product URLs: {total_urls}")
    print("="*50)
    
    for domain, urls in results.items():
        print(f"{domain}: {len(urls)} product URLs")
        
    print("="*50)

def main():
    """Main function to process results."""
    args = parse_arguments()
    
    # Merge results from all files
    results = merge_results(args.input_dir)
    
    if not results:
        print("No results found to process.")
        return
        
    # Print statistics
    print_statistics(results)
    
    # Export results in the specified format
    export_results(results, args.output_file, args.format)

if __name__ == "__main__":
    main()