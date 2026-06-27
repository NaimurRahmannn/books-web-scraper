import random

import scrapy

from books_scraper.items import BookItem


class BooksSpider(scrapy.Spider):
    """Scrapes books.toscrape.com.

    Discovers every category, keeps only the ones with enough books, then picks
    5 of those at random and scrapes 5 random books from each (so 25 in total).
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
        """Find every category, then go count how many books each one has."""
        category_links = response.css("div.side_categories ul li ul li a")

        categories = []
        for link in category_links:
            name = link.css("::text").get(default="").strip()
            url = response.urljoin(link.attrib["href"])
            categories.append({"name": name, "url": url})

        self.logger.info("Discovered %d categories.", len(categories))
        self._eligible = []
        self._pending = len(categories)

        for category in categories:
            yield scrapy.Request(
                url=category["url"],
                callback=self.count_category,
                cb_kwargs={"category": category},
            )

    def count_category(self, response, category):
        """Record a category's book count; once every count is in, pick 5."""
        count_text = response.css("form.form-horizontal strong::text").get()
        count = int(count_text) if count_text and count_text.isdigit() else 0

        if count >= self.BOOKS_PER_CATEGORY:
            self._eligible.append(category)

        self._pending -= 1
        if self._pending > 0:
            return

        # All counts are in now, so we know which categories are big enough.
        self.logger.info(
            "%d categories have at least %d books.",
            len(self._eligible),
            self.BOOKS_PER_CATEGORY,
        )

        if len(self._eligible) < self.CATEGORIES_TO_SELECT:
            self.logger.warning(
                "Only %d eligible categories; selecting all of them.",
                len(self._eligible),
            )
        sample_size = min(self.CATEGORIES_TO_SELECT, len(self._eligible))
        chosen = random.sample(self._eligible, sample_size)

        for category in chosen:
            self.logger.info(
                "Selected category: %s -> %s", category["name"], category["url"]
            )
            yield scrapy.Request(
                url=category["url"],
                callback=self.parse_category,
                cb_kwargs={"category": category["name"], "book_urls": []},
                dont_filter=True,  # already fetched this URL during counting
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
