from celery import shared_task
import requests
from decimal import Decimal

@shared_task
def fetch_stock_data(stock_code):
    url = f'https://stooq.com/q/l/?s={stock_code}&f=sd2t2ohlcvn&h&e=csv'

    try:
        response = requests.get(url)
        response.raise_for_status()
        
        lines = response.text.splitlines()
        if len(lines) < 2:
            return {'error': 'Invalid response from stock API'}

        data = lines[1].split(',')
        if len(data) < 9:
            return {'error': 'Unexpected CSV format'}

        stock_data = {
            'name': data[8],
            'symbol': data[0],
            'open': Decimal(data[3]),
            'high': Decimal(data[4]),
            'low': Decimal(data[5]),
            'close': Decimal(data[6]),
        }

        return stock_data

    except requests.RequestException as e:
        return {'error': str(e)}
