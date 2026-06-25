import random

import scrapy


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]

    CATEGORIES_TO_SELECT = 5
    BOOKS_PER_CATEGORY = 5

    async def start(self):
        base_url = self.settings.get("BOOKS_BASE_URL")
        yield scrapy.Request(url=base_url, callback=self.parse)
        
    def parse(self, response):
        category_links = response.css("div.side_categories ul li ul li a")

        categories = []
        for link in category_links:
            name = link.css("::text").get(default="").strip()
            url = response.urljoin(link.attrib["href"])
            categories.append({"name": name, "url": url})

        self.logger.info("Discovered %d categories.", len(categories))

        if len(categories) <= self.CATEGORIES_TO_SELECT:
            selected = categories
        else:
            selected = random.sample(categories, self.CATEGORIES_TO_SELECT)

        for category in selected:
            self.logger.info(
                "Selected category: %s -> %s", category["name"], category["url"]
            )
            yield scrapy.Request(
                url=category["url"],
                callback=self.parse_category,
                cb_kwargs={"category": category["name"]},
            )

    def parse_category(self, response, category):
        self.logger.info("Reached category page: %s", category)