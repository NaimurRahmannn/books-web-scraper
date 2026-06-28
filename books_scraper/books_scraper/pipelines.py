import re

from itemadapter import ItemAdapter

import os
import sqlite3

class CleaningPipeline:
    """Trims whitespace, turns the price string into a float and the availability
    text into a plain boolean so the rest of the pipeline gets clean data.
    """

    PRICE_PATTERN = re.compile(r"[\d.]+")

    # spider=None: optional since Scrapy 2.14 (not a missing arg) - see README Design Decisions
    def process_item(self, item, spider=None):
        """Clean every field on the item and hand it back.

        ``spider`` is accepted for compatibility with every Scrapy version: it
        is required by Scrapy < 2.14 and optional (passing it is deprecated)
        from 2.14 onward, so a default of ``None`` works cleanly on both.
        """
        adapter = ItemAdapter(item)

        for field in ("title", "category"):
            value = adapter.get(field)
            if value:
                adapter[field] = self._normalize_text(value)

        adapter["price"] = self._parse_price(adapter.get("price"))
        adapter["availability"] = self._parse_availability(
            adapter.get("availability")
        )

        for field in ("product_url", "image_url"):
            value = adapter.get(field)
            if value:
                adapter[field] = value.strip()

        return item
    def _normalize_text(self, value):
        """Collapse runs of whitespace and trim the ends."""
        return " ".join(value.split())

    def _parse_price(self, value):
        """Drop the currency symbol and return the price as a float."""
        if value is None:
            return None
        match = self.PRICE_PATTERN.search(value)
        if not match:
            spider_msg = f"Could not parse price from: {value!r}"
            raise ValueError(spider_msg)
        return float(match.group())

    def _parse_availability(self, value):
        if not value:
            return False
        return "in stock" in value.lower()
    




class SQLitePipeline:

    def __init__(self, db_path):

        self.db_path = db_path
        self.connection = None
        self.cursor = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(db_path=crawler.settings.get("SQLITE_DB_PATH", "books.db"))

    # spider=None: optional since Scrapy 2.14 (not a missing arg) - see README Design Decisions
    def open_spider(self, spider=None):
        """Connect to the db (``spider`` kept for Scrapy version compatibility)."""
        directory = os.path.dirname(self.db_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                price REAL,
                availability INTEGER,
                product_url TEXT UNIQUE,
                image_url TEXT,
                category TEXT
            )
            """
        )
        self.cursor.execute("DELETE FROM books")
        self.connection.commit()
    # spider=None: optional since Scrapy 2.14 (not a missing arg) - see README Design Decisions
    def process_item(self, item, spider=None):
        """Insert the book, skipping it if we've already seen the URL."""
        adapter = ItemAdapter(item)
        self.cursor.execute(
            """
            INSERT OR IGNORE INTO books
                (title, price, availability, product_url, image_url, category)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                adapter.get("title"),
                adapter.get("price"),
                int(bool(adapter.get("availability"))),
                adapter.get("product_url"),
                adapter.get("image_url"),
                adapter.get("category"),
            ),
        )
        self.connection.commit()
        return item

    # spider=None: optional since Scrapy 2.14 (not a missing arg) - see README Design Decisions
    def close_spider(self, spider=None):
        """Close the db connection when the crawl is done."""
        if self.connection:
            self.connection.close()
    