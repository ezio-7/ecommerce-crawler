import scrapy

class ProductURL(scrapy.Item):
    url = scrapy.Field()
    domain = scrapy.Field()
    found_on = scrapy.Field()  # URL where this product link was found
    discovery_time = scrapy.Field()  # When the URL was discovered