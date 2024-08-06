# encoding: utf-8

from django.contrib import admin
from django.urls import path

from api import views as api_views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('stock', api_views.StockView.as_view()),
    path('history', api_views.HistoryView.as_view()),
    path('stats', api_views.StatsView.as_view()),
    path('admin', admin.site.urls),
    # Simple JWT urls
    path('token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
]
