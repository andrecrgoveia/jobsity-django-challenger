# encoding: utf-8

import requests
from decimal import Decimal

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class StockView(APIView):
    """
    Receives stock requests from the API service.
    """

    def get(self, request, *args, **kwargs):
        stock_code = request.query_params.get('q')
        if not stock_code:
            return Response({"error": "No stock code provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Make the request to stooq.com API
        url = f'https://stooq.com/q/l/?s={stock_code}&f=sd2t2ohlcvn&h&e=csv'

        try:
            response = requests.get(url)
            response.raise_for_status()
            
            # Parse the CSV response
            lines = response.text.splitlines()
            if len(lines) < 2:
                return Response({"error": "Invalid response from stock API"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Extract stock data
            data = lines[1].split(',')
            if len(data) < 9:
                return Response({"error": "Unexpected CSV format"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            stock_data = {
                "name": data[8],
                "symbol": data[0],
                "open": Decimal(data[3]),
                "high": Decimal(data[4]),
                "low": Decimal(data[5]),
                "close": Decimal(data[6]),
            }

            return Response(stock_data)

        except requests.RequestException as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
