import random

import scrapy

from books_scraper.items import BookItem


class BooksSpider(scrapy.Spider):
    """Scrapes books.toscrape.com.
    """

    name = "books"
    allowed_domains = ["books.toscrape.com"]

    CATEGORIES_TO_SELECT = 5
    BOOKS_PER_CATEGORY = 5

    async def start(self):
        """start from homepage """
        base_url = self.settings.get("BOOKS_BASE_URL")
        yield scrapy.Request(url=base_url, callback=self.parse)

    def parse(self, response):
        """ pick 5 random categories and queue them up."""
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
                cb_kwargs={"category": category["name"], "book_urls": []},
            )

    def parse_category(self, response, category, book_urls):
        """Collect book links across all pages, then sample 5 to scrape.
        """
        for href in response.css("article.product_pod h3 a::attr(href)").getall():
            book_urls.append(response.urljoin(href))

        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield response.follow(
                next_page,
                callback=self.parse_category,
                cb_kwargs={"category": category, "book_urls": book_urls},
            )
            return

        self.logger.info(
            "Category '%s' has %d books total.", category, len(book_urls)
        )

        sample_size = min(self.BOOKS_PER_CATEGORY, len(book_urls))
        selected_books = random.sample(book_urls, sample_size)

        self.logger.info(
            "Selected %d books from '%s'.", len(selected_books), category
        )

        for url in selected_books:
            yield scrapy.Request(
                url=url,
                callback=self.parse_book,
                cb_kwargs={"category": category},
            )
            
    def parse_book(self, response, category):
        """Pull the fields we care about, a single book's detail page."""
        item = BookItem()
        item["title"] = response.css("div.product_main h1::text").get()
        item["price"] = response.css("p.price_color::text").get()
        item["availability"] = " ".join(
            response.css("p.availability::text").getall()
        ).strip()
        item["product_url"] = response.url
        item["image_url"] = response.urljoin(
            response.css("div.item.active img::attr(src)").get()
        )
        item["category"] = category
        yield item