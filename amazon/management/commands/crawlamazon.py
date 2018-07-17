# -*- coding: utf-8 -*-
import logging

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.forms.models import model_to_dict

from amazon.spiders import AmazonSpider
from amazon.models import Item


class Command(BaseCommand):
    help = 'Crawl Amazon'

    # def add_arguments(self, parser):
    #     parser.add_argument('category', type=str, nargs='?', default='adult-neutral')

    def handle(self, *args, **options):
        levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
        logging.basicConfig(
            level=levels[min(options['verbosity'], len(levels) - 1)],
        )
        logger = logging.getLogger('CrawlAmazon')
        # Fetch existing item URLs to ignore when
        # crawling
        crawled_urls = set(item.url for item in Item.objects.all())
        logger.info('Adding {} existing URLs to ignore list'.format(len(crawled_urls)))
        spider = AmazonSpider(ignore_urls=crawled_urls)
        for item_dict in spider.crawl():
            logger.info(item_dict)
            item = Item(**item_dict)
            try:
                item.save()
                logger.info('{}'.format(model_to_dict(item)))
            except IntegrityError as e:
                logger.info('Db write failed: {}'.format(e))
