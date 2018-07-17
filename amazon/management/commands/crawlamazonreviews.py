# -*- coding: utf-8 -*-
import logging

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.forms.models import model_to_dict

from amazon.spiders import AmazonReviewSpider
from amazon.models import Item, Review


class Command(BaseCommand):
    help = 'Crawl Amazon Reviews'

    # def add_arguments(self, parser):
    #     parser.add_argument('category', type=str, nargs='?', default='adult-neutral')

    def handle(self, *args, **options):
        levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
        logging.basicConfig(
            level=levels[min(options['verbosity'], len(levels) - 1)],
        )
        logger = logging.getLogger('crawlamazonreviews')
        # Fetch existing item URLs to ignore when
        # crawling
        items = Item.objects.all()
        logger.info('Adding {} item URLs to crawl list'.format(items.count()))
        crawled_urls = set(review.url for review in Review.objects.all())
        logger.info('Adding {} existing URLs to ignore list'.format(len(crawled_urls)))

        for item in items:
            spider = AmazonReviewSpider(start_url=item.url, ignore_urls=crawled_urls)
            for review_dict in spider.crawl():
                review = Review(item=item, **review_dict)
                try:
                    review.save()
                    logger.info('{}'.format(model_to_dict(review)))
                except IntegrityError as e:
                    logger.info('Db write failed: {}'.format(e))
