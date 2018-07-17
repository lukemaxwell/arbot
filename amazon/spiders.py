#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dateparser

from parsel import Selector
from yarl import URL

from core.spiders import CrawlSpider, SplashListingSpider
from core.parsers import Parser


class AmazonSpider(SplashListingSpider):
    name = 'amazon'
    item_page_xpath = '//span[@id="productTitle"]'
    listings_page_xpath = '//li[@class="asin-container"]'
    listings_xpath = '//li[@class="asin-container"]//a/@href'

    def __init__(self, rate_min=1, category='adult-female',
                 price_min='', price_max='', is_prime='', **kwargs):
        super().__init__(**kwargs)
        self.parser = Parser()
        self.rate_min = rate_min
        self.price_min = price_min
        self.price_max = price_max
        self.is_prime = is_prime
        self.category = category
        self.url_args = [
            ('categoryId', category),
            ('isPrime', self.is_prime),
            ('priceFrom', self.price_min),
            ('priceTo', self.price_max),
        ]
        # Parsing start url will sort the args and minimise duplicate
        # requests
        self.start_url = self.parse_url(
            URL('https://www.amazon.co.uk/gcx/Gifts-for-Women/gfhz/').with_query(self.url_args))

        # self.start_url = self.parse_url(
        #     URL(self.root_url).with_query(self.url_args))

    def clean_listing_url(self, url):
        return URL(str(url).split('ref=')[0])

    def parse_item(self, html, url=None):
        """
        Parse Amazon product item.
        """
        sel = Selector(html)
        # Amazon adds guff to the URL paths, we only need /dp/ASIN/
        # A regex would be better
        if isinstance(url, URL):
            url = str(url)
        title_xpath = '//span[@id="productTitle"]/text()'
        title = sel.xpath(title_xpath).extract_first().strip()
        asin_xpath = '//div[@data-asin]/@data-asin'
        asin = sel.xpath(asin_xpath).extract_first().strip()
        rating = self.parse_rating(sel)
        review_count = self.parse_review_count(sel)
        price = self.parse_price(sel)
        description = self.parse_description(sel)

        item = {
            'title': title,
            'url': url,
            'price': price,
            'rating': rating,
            'review_count': review_count,
            'asin': asin,
            'category': self.category,
            'description': description,
            'currency': 'GBP',
        }
        return item

    def parse_price(self, sel):
        price_xpaths = [
            '//span[@id="priceblock_ourprice"]/text()',
            '//span[@id="priceblock_saleprice"]/text()',
            '//span[@id="priceblock_dealprice"]/text()',
            '//div[@data-asin-price]/@data-asin-price',
        ]
        price = None
        for xpath in price_xpaths:
            price = sel.xpath(xpath).extract_first()
            if price is not None:
                # Just take the lowest price it gives a range,
                # e.g. £25.00 - £100.00 would use £25.00
                price = price.split()[0]
                cleaned_price = ''
                for p in price.strip():
                    if p.isdigit() or p == '.':
                        cleaned_price += str(p)
                price = cleaned_price
                break
        return price

    def parse_description(self, sel):
        description_xpath = '//div[@id="productDescription"]//p/text()'
        description = sel.xpath(description_xpath).extract_first(default='')
        description = description.replace('"', '').replace('<br>', '').strip()
        return description

    def parse_rating(self, sel):
        rating_xpath = '//div[@id="averageCustomerReviews"]//span[@class="a-icon-alt"]/text()'
        rating = sel.xpath(rating_xpath).extract_first()
        if rating is not None:
            rating = rating.strip().split()[0]
        else:
            rating = 0
        return rating

    def parse_review_count(self, sel):
        review_count_xpath = '//span[@id="acrCustomerReviewText"]/text()'
        review_count = sel.xpath(review_count_xpath).extract_first()
        if review_count is not None:
            review_count = review_count.strip().split()[0].replace(',', '')
        else:
            review_count = 0
        return review_count


class AmazonReviewSpider(CrawlSpider):
    name = 'amazonreview'
    base_url = URL('https://www.amazon.co.uk')
    item_page_xpath = '//span[@id="productTitle"]'
    reviews_listing_url_xpath = '//a[@id="dp-summary-see-all-reviews"]/@href'
    reviews_listing_page_xpath = '//div[contains(@class, "reviews-content")]'
    review_url_xpath = '//a[@data-hook="review-title"]/@href'
    review_page_xpath = '//h1[text()="Customer Review"]'

    def parse(self, html, url=None):
        """
        Extract reviews page URLs to crawl and reviews to parse.
        """
        sel = Selector(html)
        self.logger.info('Parsing page')
        page_type = None
        # Parse item page
        try:
            sel.xpath(self.item_page_xpath).extract()[0]
            page_type = 'item'
            reviews_url = self.parse_reviews_url(html)
            self.logger.info('Reviews url: {}'.format(reviews_url))
            self.add_url(reviews_url)
        except IndexError:
            pass

        # Parse review listings page
        if not page_type:
            try:
                sel.xpath(self.reviews_listing_page_xpath).extract()[0]
                page_type = 'review listings'
                self.parse_review_listings(sel)
            except IndexError:
                pass

        # Parse review page
        if not page_type:
            try:
                sel.xpath(self.review_page_xpath).extract()[0]
                page_type = 'review'
                yield self.parse_review(sel, url=url)
            except IndexError:
                pass

        self.logger.info('Page type: {}'.format(page_type))

    def parse_reviews_url(self, html):
        """
        Parse reviews link from item page.
        """
        sel = Selector(html)
        url = sel.xpath(self.reviews_listing_url_xpath).extract()[0]
        return url

    def clean_review_url(self, url):
        """
        Returned cleaned URL for review page.

        returns: yarl.URL
        """
        url = URL(url)
        if not url.host:
            url = self.base_url.join(url)
        return url

    def parse_review_listings(self, sel):
        """
        Parse review URLs from review listings page.
        """
        # Add item URLs to crawl queue.
        count = 0
        for url in sel.xpath(self.review_url_xpath).extract():
            self.add_url(self.clean_review_url(url))
            count += 1
        self.logger.info('Parsed {} review listings'.format(count))

    def parse_review(self, sel, url=None):
        """
        Parse item.

        Subclass spiders should override this method.
        """
        title_xpath = '//a[@data-hook="review-title"]/text()'
        body_xpath = '//span[@data-hook="review-body"]/text()'
        review = {
            'url': str(url),
            'rating': self.parse_rating(sel),
            'title': sel.xpath(title_xpath).extract_first().strip(),
            'body': sel.xpath(body_xpath).extract_first(),
            'date': self.parse_date(sel),
            'author_username': self.parse_author_username(sel),
            'author_url': str(self.parse_author_url(sel)),
            'verified_purchase': self.parse_verified_purchase(sel)
        }
        self.logger.info('Review: {}'.format(review))
        return review

    def parse_author_username(self, sel):
        """
        Parse review author username.
        """
        username_xpath = '//a[@data-hook="review-author"]/text()'
        username = sel.xpath(username_xpath).extract_first().strip()
        return username

    def parse_author_url(self, sel):
        """
        Parse review author url.
        """
        url_xpath = '//a[@data-hook="review-author"]/@href'
        url = sel.xpath(url_xpath).extract_first().strip()
        return self.parse_url(url)

    def parse_verified_purchase(self, sel):
        """
        Parse review verified purchase status.
        """
        vf_xpath = '//span[text()="Verified Purchase"]'

        try:
            sel.xpath(vf_xpath).extract()[0]
            return True
        except IndexError:
            return False

    def parse_date(self, sel):
        """
        Parse review date.
        """
        date_xpath = '//span[@data-hook="review-date"]/text()'
        date = sel.xpath(date_xpath).extract_first().replace('on', '').strip()
        date = dateparser.parse(date)
        return date

    def parse_rating(self, sel):
        rating_xpath = '//i[@data-hook="review-star-rating"]//span/text()'
        rating = sel.xpath(rating_xpath).extract_first()
        if rating is not None:
            rating = rating.strip().split()[0]
        else:
            rating = 0
        return rating
