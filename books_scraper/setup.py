# scrapyd-deploy

from setuptools import setup, find_packages

setup(
    name         = 'books_scraper',
    version      = '1.0',
    packages     = find_packages(),
    entry_points = {'scrapy': ['settings = books_scraper.settings']},
)
