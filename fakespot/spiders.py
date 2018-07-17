#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Modules
import string
import yarl
# Submodules
from parsel import Selector
# App
from core.spiders import SplashBaseSpider


class FakespotSpiderError(Exception):
    pass


class FakespotSpider(SplashBaseSpider):
    name = 'fakespot'

    def __init__(self, urls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Parsing start url will sort the args and minimise duplicate
        # requests
        self.base_url = yarl.URL('https://www.fakespot.com/analyze')
        self.amazon_urls = urls

    def crawl(self):
        for amazon_url in self.amazon_urls:
            self.logger.info('Submitting {} for fakespot analysis'.format(amazon_url))
            url = self.base_url.with_query({'url': amazon_url})
            response = self.fetch(str(url), wait=10)
            yield self.parse_result(response.text, amazon_url, url)

    def parse_result(self, html, amazon_url, url=None):
        """
        Parse Fakespot product analysis.
        """
        sel = Selector(html)
        self.logger.info('Parsing rating')
        score_xpath = '//div[contains(@class, "comp-grade")]//p/text()'
        score = None

        try:
            score = sel.xpath(score_xpath).extract_first()[0]
        except TypeError:
            pass  # we can come back and get them later

        if score:
            score = score.strip()
            if score == '?':
                score = None
            else:
                score = string.ascii_uppercase.index(score)

        self.logger.info(amazon_url)
        result = {
            'score': score
        }

        return result
