import requests
import logging
from datetime import datetime
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class MarketMonitor:

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        self.headers = {"User-Agent": "Mozilla/5.0"}

    def get_current_price(self) -> Optional[Dict]:
        try:
            url = f"{self.base_url}/{self.symbol}"
            params = {'interval': '1m', 'range': '1d'}
            response = requests.get(url,
                                    headers=self.headers,
                                    params=params,
                                    timeout=10)
            response.raise_for_status()
            data = response.json()
            return self._parse_price_data(data)
        except Exception as e:
            logger.error(f"Error fetching price for {self.symbol}: {str(e)}")
            return None

    def _parse_price_data(self, data):
        try:
            meta = data['chart']['result'][0]['meta']
            current = meta['regularMarketPrice']
            previous = meta['previousClose']
            change = current - previous
            change_percent = (change / previous) * 100

            return {
                'price': current,
                'previous_close': previous,
                'change': change,
                'change_percent': change_percent,
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error parsing data for {self.symbol}: {str(e)}")
            return None

    def get_top_movers(self) -> Dict:
        symbols = {
            "AAPL": "Apple",
            "TSLA": "Tesla",
            "NVDA": "NVIDIA",
            "AMZN": "Amazon",
            "GOOGL": "Google",
            "META": "Meta"
        }

        prices = {}
        for symbol in symbols:
            data = self._fetch_stock_data(symbol)
            if data:
                prices[symbol] = data

        if not prices:
            return {}

        top_gainer = max(prices.items(), key=lambda x: x[1]['change_percent'])
        top_loser = min(prices.items(), key=lambda x: x[1]['change_percent'])

        return {
            'top_gainer': {
                'symbol': top_gainer[0],
                'name': symbols[top_gainer[0]],
                'change_percent': top_gainer[1]['change_percent'],
                'price': top_gainer[1]['price']
            },
            'top_loser': {
                'symbol': top_loser[0],
                'name': symbols[top_loser[0]],
                'change_percent': top_loser[1]['change_percent'],
                'price': top_loser[1]['price']
            }
        }

    def _fetch_stock_data(self, symbol):
        try:
            url = f"{self.base_url}/{symbol}"
            params = {'interval': '1d', 'range': '2d'}
            response = requests.get(url,
                                    headers=self.headers,
                                    params=params,
                                    timeout=10)
            response.raise_for_status()
            data = response.json()

            result = data['chart']['result'][0]
            closes = result['indicators']['quote'][0].get('close', [])

            if len(closes) < 2 or closes[-1] is None or closes[-2] is None:
                raise ValueError("Close data unavailable.")

            current = closes[-1]
            previous = closes[-2]
            change_percent = ((current - previous) / previous) * 100

            return {'price': current, 'change_percent': change_percent}

        except Exception as e:
            logger.warning(f"Error fetching data for {symbol}: {str(e)}")
            return None
