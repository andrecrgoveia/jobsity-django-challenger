from decimal import Decimal
import requests
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase


class StockViewTests(APITestCase):
    def setUp(self):
        self.url = '/stock'  # URL direta sem usar `reverse`

    @patch('stocks.views.requests.get')
    def test_successful_response(self, mock_get):
        """
        Test that a successful response from the external API is handled correctly.
        """
        # Simulate a successful response from the external API
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = 'Symbol,Date,Time,Open,High,Low,Close,Volume,Name\nZIP.US,2024-08-06,18:38:57,7.97,7.97,7.57,7.63,126768,ZIPRECRUITER'
        response = self.client.get(self.url, {'q': 'ZIP.US'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            "name": "ZIPRECRUITER",
            "symbol": "ZIP.US",
            "open": Decimal('7.97'),
            "high": Decimal('7.97'),
            "low": Decimal('7.57'),
            "close": Decimal('7.63'),
        })

    @patch('stocks.views.requests.get')
    def test_invalid_response(self, mock_get):
        """
        Test that an invalid response from the external API results in a server error.
        """
        # Simulate an invalid response from the external API
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = 'Date,Open,High,Low,Close,Volume,Adj Close\n'
        
        response = self.client.get(self.url, {'q': 'AAPL.US'})
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, {"error": "Invalid response from stock API"})

    @patch('stocks.views.requests.get')
    def test_request_exception(self, mock_get):
        """
        Test that an exception during the external API request results in a server error.
        """
        # Simulate an exception during the external API request
        mock_get.side_effect = requests.RequestException("API request failed")
        
        response = self.client.get(self.url, {'q': 'AAPL.US'})
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, {"error": "API request failed"})

    def test_no_stock_code(self):
        """
        Test that a missing stock code results in a bad request error.
        """
        # Test for the absence of a stock code
        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "No stock code provided"})
