# -*- coding: utf-8 -*-
import logging

from django.core.management.base import BaseCommand
from deals.spiders import SlickDealsSpider


class Command(BaseCommand):
    help = 'Crawl SlickDeals'

    def handle(self, *args, **options):
        levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
        logging.basicConfig(
            level=levels[min(options['verbosity'], len(levels) - 1)],
        )
        spider = SlickDealsSpider()
        spider.crawl()
