import scrapy


class BookItem(scrapy.Item):
    """The fields we scrape for each book"""

    title = scrapy.Field()
    price = scrapy.Field()         
    availability = scrapy.Field() 
    product_url = scrapy.Field()
    image_url = scrapy.Field()
    category = scrapy.Field()