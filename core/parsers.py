# -*- coding: utf-8 -*-
"""
Parser class module.
"""
import babel.numbers
import pycountry


class Parser():
    """
    Parsing utility class.
    """
    def __init__(self):
        self.currency_symbols = self.get_currency_symbols()

    def get_currency_symbols(self):
        """
        Return dictionary of pycountry currencies by symbol.
        """
        currencies = {}
        # Create constants...
        # Some countries use the same symbol
        constants = {
            '$': 'USD',
        }
        # Get list of currencies
        for currency in pycountry.currencies:
            # Get symbol
            symbol = babel.numbers.get_currency_symbol(currency.alpha_3)
            # Try constant first
            try:
                currencies[symbol] = constants[symbol]
            except KeyError:
                currencies[symbol] = currency.alpha_3

        return currencies

    def parse_prices(self, string):
        """
        Return list of parsed prices.
        """
        prices = []
        for chunk in string.split():
            try:
                currency = self.currency_symbols[chunk[0]]
                chunk = chunk[1:]
            except KeyError:
                currency = None

            try:
                price = babel.numbers.parse_decimal(chunk)
            except Exception as e:
                price = None

            if price:
                prices.append({'price': price, 'currency': currency})

        return prices
