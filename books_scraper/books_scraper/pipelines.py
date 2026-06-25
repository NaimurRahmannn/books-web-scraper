import re

from itemadapter import ItemAdapter


class CleaningPipeline:
    PRICE_PATTERN = re.compile(r"[\d.]+")

    def process_item(self, item):
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
        return " ".join(value.split())

    def _parse_price(self, value):
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