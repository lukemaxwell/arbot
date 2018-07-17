# -*- coding: utf-8 -*-
"""
Base spider module.
"""
import autopager
import datetime
import glob
import logging
import maybedont
import os
import parsel
import queue
import requests
import sys
import time
import yarl

from django.conf import settings

# Disable insecure request warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class BaseSpider():
    name = 'base'

    def __init__(self, start_url='', ignore_urls=set()):
        # self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.dir_path = os.path.dirname(sys.modules[self.__module__].__file__)
        self.samples_path = os.path.join(self.dir_path, 'samples/{}'.format(self.name))
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info('Samples path: {}'.format(self.samples_path))
        self.user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0'
        self.start_url = yarl.URL(start_url)
        self.headers = {
            'USER-AGENT': self.user_agent
        }
        self.seen_urls = ignore_urls
        self.delay = 1  # seconds
        self.last_request_ts = None
        self.dedupe = True
        self.logger.info('Dedupe enabled: {}'.format(self.dedupe))
        self.dp = self._load_dupe_predictor()

    def _load_samples(self, path):
        """
        Return list of html pages from path.
        """
        samples = list()
        paths = glob.glob('{}/*.html'.format(self.samples_path))
        self.logger.info('Dedupe samples: {}'.format(','.join(paths)))
        for path in paths:
            with open(path) as f:
                samples.append(f.read())
        return samples

    def _load_dupe_predictor(self):
        """
        Return maybedont dupefilter.
        """
        samples = self._load_samples(self.samples_path)
        dp = maybedont.DupePredictor(
            texts_sample=samples,
            jaccard_threshold=0.9)  # default value

        return dp

    def apply_delay(self):
        """
        Implement delay_time.
        """
        if self.last_request_ts is None:
            return

        current_ts = datetime.datetime.now()
        time_ok = self.last_request_ts + datetime.timedelta(seconds=self.delay)
        self.logger.info(time_ok)

        while current_ts < time_ok:
            current_ts = datetime.datetime.now()
            time.sleep(1)

    def clean_args(self, url):
        """
        Return yarl URL with cleaned query args.
        """
        query_str = ''
        # Sort and dedupe
        keys = sorted(list(set(url.query.keys())))
        if keys:
            for key in keys:
                query_str += '&{}={}'.format(key, url.query[key])

        return url.with_query(query_str[1:])  # trim first ampersand

    def parse_url(self, url):
        """
        Return valid yarl URL.

        Use start_url to populate missing scheme and host.
        """
        # Convert to yarl URL
        if not isinstance(url, yarl.URL):
            url = yarl.URL(url)
        # Add missing host
        if not url.host:
            url = self.start_url.origin().join(url)
        # Add missing scheme
        if not url.scheme:
            url = url.with_scheme(self.start_url.scheme)

        url = self.clean_args(url)

        return url

    def get_pagination_urls(self, html):
        """
        Return set of urls extracted from pagination links.

        Uses AutoPager:
        https://github.com/TeamHG-Memex/autopager
        """
        urls = set()

        for url in autopager.urls(html):
            urls.add(self.parse_url(url))

        return urls

    def fetch(self, url):
        """
        Return requests.Response for url.

        ToDo - args such as timeout.
        """
        response = requests.get(
            str(url), headers=self.headers, verify=False)
        self.last_request_ts = datetime.datetime.now()

        return response


class CrawlSpider(BaseSpider):
    """
    Base crawl spider class implementing crawl queue.

    Subclass the spider and override the parse method.
    """
    name = 'crawl'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.q = queue.Queue()
        self.follow_pagination = True

    def add_pagination_urls_to_queue(self, html):
        """
        Extract pagination urls from html and add to crawl queue.
        """
        for url in self.get_pagination_urls(html):
            self.add_url(url)

    def add_url(self, url):
        """
        Add url (yarl.URL or string) to queue
        """
        if isinstance(url, str):
            url = self.parse_url(url)
        elif isinstance(url, yarl.URL):
            # We still parse the yarl URL in order
            # to sort and dedupe the args.
            url = self.parse_url(str(url))
        else:
            raise ValueError('`url` must be str or yarl.URL')

        if str(url) not in self.seen_urls:
            self.q.put(url)
            self.seen_urls.add(str(url))

    def parse(self, html, url=None):
        """
        Add urls to queue and yield parsed items.

        This is the default method to be overridden by
        spiders that subclass the CrawlSpider.
        """
        # Extract urls..
        # Add urls to crawl queue
        # Parse items..
        # Yield items
        pass

    def crawl(self):
        """
        Crawl pages.

        ToDo: handle errors
        """
        # Add start url to the queue
        self.q.put(self.start_url)
        # Crawl...
        while not self.q.empty():
            url = self.q.get()

            if self.dedupe:
                self.logger.info(
                    'Dupe prob: {}'.format(self.dp.get_dupe_prob(str(url))))

            self.apply_delay()  # apply wait time between requests
            response = self.fetch(str(url))
            self.logger.info('{} {}'.format(response.status_code, url))
            self.seen_urls.add(str(url))

            # Update dupepredictor
            if self.dedupe and response.status_code == 200:
                self.dp.update_model(str(url), response.text)

            # Process paginated urls
            if self.follow_pagination:
                self.add_pagination_urls_to_queue(response.text)

            # Parse
            for item in self.parse(response.text, url=url):
                yield item


class ListingSpider(CrawlSpider):
    name = 'listing'
    # Define page element identifiers
    item_page_xpath = ''
    listings_page_xpath = ''
    # Define URLs to crawl from listings pages
    listings_xpath = ''
    page_type = None

    def parse(self, html, url=None):
        """
        Extract listing page URLs to crawl and items to parse.
        """
        sel = parsel.Selector(html)
        self.logger.info('Parsing page')
        page_type = None
        # Parse listings page
        try:
            sel.xpath(self.listings_page_xpath)[0]
            page_type = 'listing'
            self.parse_listings(html)
        except IndexError:
            pass

        # Parse item page
        if not page_type:
            try:
                sel.xpath(self.item_page_xpath)[0]
                page_type = 'item'
                self.logger.info(url)
                yield self.parse_item(html, url=url)
            except IndexError:
                pass

        self.logger.info('Page type: {}'.format(page_type))

    def clean_listing_url(self, url):
        """
        Override for custom spider.
        """
        return url

    def parse_listings(self, html):
        """
        Parse item URLs from listings page.
        """
        # Add item URLs to crawl queue.
        sel = parsel.Selector(html)
        count = 0
        for url in sel.xpath(self.listings_xpath).extract():
            self.add_url(self.clean_listing_url(url))
            count += 1
        self.logger.info('Parsed {} listings'.format(count))

    def parse_item(self, html, url=None):
        """
        Parse item.

        Subclass spiders should override this method.
        """
        raise NotImplemented('The base parse_item method should not be used directly, '
                             'override it subclassed spider.')


class SplashMixin():
    """
    Splash request mixin.

    Sends requests via splash to obtain rendered pages from
    Javascript-enabled sites.
    """
    splash_url = yarl.URL(settings.SPLASH_URL).with_path('render.json')

    def fetch(self, url, timeout=30, wait=0, png=0):
        """
        Return requests.Response for url.

        Use splash as proxy to return data and
        updates response.content fields with splash response
        data.

        Full splash json data is available via
        response.json()
        """
        args = {
            'url': url,
            'headers': self.headers,
            'html': 1,
            'png': png,
            'timeout': timeout,
            'wait': wait
        }
        response = requests.post(url=str(self.splash_url), json=args)
        # Update response content fields with Splash response html
        try:
            response._content = response.json()['html'].encode('utf8')
        except KeyError:
            pass
        return response


class SplashBaseSpider(SplashMixin, BaseSpider):
    """
    Base spider using splash.
    """
    pass


class SplashCrawlSpider(SplashMixin, CrawlSpider):
    """
    Crawl spider using splash.
    """
    pass


class SplashListingSpider(SplashMixin, ListingSpider):
    """
    Listing spider using splash.
    """
    pass
