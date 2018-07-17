#!/usr/bin/env python
# -*- coding: utf-8 -*-
from babel import numbers
from yarl import URL
from parsel import Selector

from core.spiders import ListingSpider
from core.parsers import Parser


class SlickDealsSpider(ListingSpider):
    name = 'slickdeals'
    item_page_xpath = '//div[@id="detailsArea"]'
    listings_page_xpath = '//div[@class="resultsHeader"]'
    listings_xpath = '//div[@class="dealWrapper"]//a[@class="dealTitle"]/@href'

    def __init__(self, store='12029', rate_min=1,
                 hide_expired=True, price_min='500', price_max='0'):
        super().__init__()
        self.parser = Parser()
        self.store = store
        self.rate_min = rate_min
        self.price_min = price_min
        self.price_max = price_max
        self.hide_expired = hide_expired
        self.root_url = 'https://slickdeals.net/newsearch.php'
        self.url_args = [
            ('page', '1'),
            ('forum_id', 'Array'),
            ('pp', '100'),
            ('sort', 'highest_price'),
            ('filter[]', self.store),
            ('forum_id', 'Array'),
            ('pricemin', self.price_min),
            # ('price_range', 'Array'),
            ('previous_days', '-1'),
            ('thumbs', '1'),
            ('rating', '{}'.format(self.rate_min)),
            ('previousdays', '-1'),
            ('hideexpired', '{}'.format(int(self.hide_expired))),
            ('r', '1'),
        ]
        # Parsing start url will sort the args and minimise dupelicate
        # requests
        self.start_url = self.parse_url(
            URL(self.root_url).with_query(self.url_args))

    def get_final_url(self, url):
        """
        Return final destination URL.
        """
        response = self.fetch(url)
        return response.url

    def parse_item(self, html):
        """
        Parse SlickDeals deal item.
        """
        sel = Selector(html)
        # Parse deal item..
        xpath = '//div[@id="dealStats"]'

        try:
            details = sel.xpath(xpath)[0]
        except:
            self.logger.warning('Could not parse item')
            return  # Not an item page

        score_xpath = './/span[@role="thread.score"]/text()'
        score = details.xpath(score_xpath).extract_first()
        url_xpath = './/div[@data-action-type="see-deal"]//a/@href'
        url = details.xpath(url_xpath).extract_first()
        url = self.get_final_url(url)
        price_xpath = './/div[@id="dealPrice"]/text()'
        price = details.xpath(price_xpath).extract_first()
        views_xpath = './/div[@id="dealViews"]//span[2]/text()'

        try:
            views = numbers.parse_number(details.xpath(views_xpath).extract_first())
        except Exception as e:
            self.logger.warn('Could not parse views: {}'.format(e))

        category_xpath = '//span[@id="category"]//a[1]/text()'
        category = sel.xpath(category_xpath).extract_first()  # Use top level selector for this one

        try:
            price = self.parser.parse_prices(price)[0]
        except IndexError:
            self.logger.warning('Could not parse price: {}'.format(price))

        item = {
            'score': score,
            'url': url,
            'price': price['price'],
            'currency': price['currency'],
            'views': views,
            'category': category
        }
        self.logger.info('{}'.format(item))
