# -*- coding: utf-8 -*-
import logging

from django.core.management.base import BaseCommand
from amazon.models import Item
from fakespot.spiders import FakespotSpider


class Command(BaseCommand):
    help = 'Crawl Fakespot'

    def handle(self, *args, **options):
        levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
        logging.basicConfig(
            level=levels[min(options['verbosity'], len(levels) - 1)],
        )
        logger = logging.getLogger('CrawlFakespot')
        # Fetch existing item URLs to ignore when
        # crawling
        items = Item.objects.filter(spam_rating=None)
        logger.info('Adding {} URLs to crawl list'.format(items.count()))
        for item in items:
            spider = FakespotSpider(urls=[item.url])
            for result_dict in spider.crawl():
                item.spam_rating = result_dict['score']
                item.save()
                logger.info(
                    'Updated item {} with spam_score: {}'
                    .format(item.id, result_dict['score']))
