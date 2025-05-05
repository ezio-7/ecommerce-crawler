import re
import tldextract
from urllib.parse import urlparse, urljoin

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
    
    Args:
        url: The URL to check
        patterns: Optional list of regex patterns to match against
        
    Returns:
        bool: True if the URL appears to be a product page
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
    # like utm_source, utm_medium, etc.
    cleaned = parsed._replace(
        query=re.sub(r'utm_[a-zA-Z]+=[^&]*&?', '', parsed.query)
    )
    return cleaned.geturl()