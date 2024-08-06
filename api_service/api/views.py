# encoding: utf-8

import requests
from decimal import Decimal

from django.utils import timezone
from django.db.models import Count
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import UserRequestHistory
from api.serializers import UserRequestHistorySerializer


# class StockView(APIView):
#     """
#     Endpoint to allow users to query stock information.
#     Queries the stock service (stock_service) and returns the data to the API client.
#     """

#     permission_classes = [IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         stock_code = request.query_params.get('q')
#         if not stock_code:
#             return Response({"error": "No stock code provided"}, status=status.HTTP_400_BAD_REQUEST)

#         # Make request to the stock service
#         stock_service_url = f'http://0.0.0.0:8001/stock?q={stock_code}'

#         try:
#             stock_service_response = requests.get(stock_service_url)
#             stock_service_response.raise_for_status()

#             # Get data from the stock service response
#             stock_data = stock_service_response.json()

#             # Ensure all required fields are present
#             required_fields = ["name", "symbol", "open", "high", "low", "close"]
#             if not all(field in stock_data for field in required_fields):
#                 return Response({"error": "Incomplete data from stock service"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#             # Save the request history for the user
#             user_request = UserRequestHistory(
#                 date=timezone.now(),
#                 name=stock_data.get("name"),
#                 symbol=stock_data.get("symbol"),
#                 open=Decimal(stock_data.get("open")),
#                 high=Decimal(stock_data.get("high")),
#                 low=Decimal(stock_data.get("low")),
#                 close=Decimal(stock_data.get("close")),
#                 user=request.user
#             )
#             user_request.save()

#             return Response(stock_data)

#         except requests.RequestException as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from celery.result import AsyncResult
from api.models import UserRequestHistory
from api.serializers import UserRequestHistorySerializer
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from api_service.celery import app

class StockView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        stock_code = request.query_params.get('q')
        if not stock_code:
            return Response({"error": "No stock code provided"}, status=status.HTTP_400_BAD_REQUEST)

        task = app.send_task('stocks.tasks.fetch_stock_data', args=[stock_code])
        result = AsyncResult(task.id)

        # Wait for task to complete
        stock_data = result.get(timeout=10)

        if "error" in stock_data:
            return Response(stock_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        user_request = UserRequestHistory(
            date=timezone.now(),
            name=stock_data.get("name"),
            symbol=stock_data.get("symbol"),
            open=Decimal(stock_data.get("open")),
            high=Decimal(stock_data.get("high")),
            low=Decimal(stock_data.get("low")),
            close=Decimal(stock_data.get("close")),
            user=request.user
        )
        user_request.save()

        return Response(stock_data)


class HistoryView(generics.ListAPIView):
    """
    Returns queries made by the current user.
    """
    serializer_class = UserRequestHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserRequestHistory.objects.filter(user=self.request.user).order_by('-date')

class StatsView(APIView):
    """
    Allows superusers to view the most queried stocks.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Check if the user is a superuser
        if not request.user.is_superuser:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        # Get the top 5 most queried stocks
        top_stocks = (UserRequestHistory.objects.values('symbol')
                      .annotate(times_requested=Count('symbol'))
                      .order_by('-times_requested')[:5])

        # Format the response in the desired format
        formatted_response = [
            {"stock": stock['symbol'].lower(), "times_requested": stock['times_requested']}
            for stock in top_stocks
        ]

        return Response(formatted_response)
