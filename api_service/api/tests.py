import requests
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from .models import UserRequestHistory
from .serializers import UserRequestHistorySerializer


class UserRequestHistoryModelTest(TestCase):
    """
    Test suite for the UserRequestHistory model.
    """

    def setUp(self):
        """
        Create a user and a UserRequestHistory instance for testing.
        """
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.history_entry = UserRequestHistory.objects.create(
            date=timezone.now(),
            name='Test Company',
            symbol='TST',
            open=Decimal('100.00'),
            high=Decimal('110.00'),
            low=Decimal('90.00'),
            close=Decimal('105.00'),
            user=self.user
        )

    def test_user_request_history_creation(self):
        """
        Test that a UserRequestHistory instance is created successfully.
        """
        self.assertEqual(self.history_entry.name, 'Test Company')
        self.assertEqual(self.history_entry.symbol, 'TST')
        self.assertEqual(self.history_entry.open, Decimal('100.00'))
        self.assertEqual(self.history_entry.high, Decimal('110.00'))
        self.assertEqual(self.history_entry.low, Decimal('90.00'))
        self.assertEqual(self.history_entry.close, Decimal('105.00'))
        self.assertEqual(self.history_entry.user, self.user)

    def test_user_request_history_str(self):
        """
        Test the string representation of the UserRequestHistory model.
        """
        expected_str = f"UserRequestHistory object ({self.history_entry.id})"
        self.assertEqual(str(self.history_entry), expected_str)

    def test_user_request_history_date(self):
        """
        Test the date field of the UserRequestHistory model.
        """
        self.assertTrue(self.history_entry.date <= timezone.now())

    def test_user_request_history_decimal_fields(self):
        """
        Test that decimal fields are correctly set and retrieved.
        """
        self.assertIsInstance(self.history_entry.open, Decimal)
        self.assertIsInstance(self.history_entry.high, Decimal)
        self.assertIsInstance(self.history_entry.low, Decimal)
        self.assertIsInstance(self.history_entry.close, Decimal)

    def test_user_request_history_user_relation(self):
        """
        Test the foreign key relationship with the user model.
        """
        self.assertEqual(self.history_entry.user.username, 'testuser')

    def tearDown(self):
        """
        Clean up any objects created during the tests.
        """
        self.history_entry.delete()
        self.user.delete()


class StockViewTest(APITestCase):
    """
    Test suite for the StockView.
    """

    def setUp(self):
        """
        Create a user for testing.
        """
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)

    @patch('requests.get')
    def test_stock_view_success(self, mock_get):
        """
        Test successful retrieval of stock data and saving to UserRequestHistory.
        """
        mock_response = {
            "name": "Test Company",
            "symbol": "TST",
            "open": "100.00",
            "high": "110.00",
            "low": "90.00",
            "close": "105.00"
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        response = self.client.get('/stock', {'q': 'TST'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, mock_response)

        # Check if the data was saved in UserRequestHistory
        user_request_history = UserRequestHistory.objects.first()
        self.assertIsNotNone(user_request_history)
        self.assertEqual(user_request_history.name, "Test Company")
        self.assertEqual(user_request_history.symbol, "TST")
        self.assertEqual(user_request_history.open, Decimal('100.00'))
        self.assertEqual(user_request_history.high, Decimal('110.00'))
        self.assertEqual(user_request_history.low, Decimal('90.00'))
        self.assertEqual(user_request_history.close, Decimal('105.00'))
        self.assertEqual(user_request_history.user, self.user)

    @patch('requests.get')
    def test_stock_view_failure(self, mock_get):
        """
        Test failure to retrieve stock data from the stock service.
        """
        mock_get.side_effect = requests.RequestException("Service unavailable")

        response = self.client.get('/stock', {'q': 'TST'})
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, {"error": "Service unavailable"})


class HistoryViewTest(APITestCase):
    """
    Test suite for the HistoryView.
    """

    def setUp(self):
        """
        Create a user and some UserRequestHistory instances for testing.
        """
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create history entries for the user
        self.history_entry1 = UserRequestHistory.objects.create(
            date=timezone.now(),
            name='Company A',
            symbol='CMPA',
            open=Decimal('100.00'),
            high=Decimal('110.00'),
            low=Decimal('90.00'),
            close=Decimal('105.00'),
            user=self.user
        )
        self.history_entry2 = UserRequestHistory.objects.create(
            date=timezone.now(),
            name='Company B',
            symbol='CMPB',
            open=Decimal('200.00'),
            high=Decimal('210.00'),
            low=Decimal('190.00'),
            close=Decimal('205.00'),
            user=self.user
        )
        # Create a history entry for another user
        self.other_user = get_user_model().objects.create_user(
            username='otheruser',
            password='otherpassword'
        )
        self.history_entry_other_user = UserRequestHistory.objects.create(
            date=timezone.now(),
            name='Company C',
            symbol='CMPC',
            open=Decimal('300.00'),
            high=Decimal('310.00'),
            low=Decimal('290.00'),
            close=Decimal('305.00'),
            user=self.other_user
        )

    def test_history_view_success(self):
        """
        Test that the HistoryView returns the correct history entries for the current user.
        """
        response = self.client.get('/history')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Create a sorted list of expected data
        expected_data = UserRequestHistorySerializer([self.history_entry1, self.history_entry2], many=True).data
        # Sort by 'symbol' or another relevant field if necessary
        response_data = sorted(response.data, key=lambda x: x['symbol'])
        expected_data_sorted = sorted(expected_data, key=lambda x: x['symbol'])
        
        self.assertEqual(response_data, expected_data_sorted)


    def test_history_view_no_entries(self):
        """
        Test that the HistoryView returns an empty list when the user has no history entries.
        """
        # Create a new user with no history entries
        new_user = get_user_model().objects.create_user(
            username='newuser',
            password='newpassword'
        )
        self.client.force_authenticate(user=new_user)
        response = self.client.get('/history')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_history_view_other_user_entries(self):
        """
        Test that the HistoryView does not return history entries of other users.
        """
        response = self.client.get('/history')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ensure that the history entry of the other user is not included
        excluded_data = UserRequestHistorySerializer([self.history_entry_other_user], many=True).data
        self.assertNotIn(excluded_data[0], response.data)

    def tearDown(self):
        """
        Clean up any objects created during the tests.
        """
        UserRequestHistory.objects.all().delete()
        get_user_model().objects.all().delete()


class StatsViewTest(APITestCase):
    """
    Test suite for the StatsView.
    """

    def setUp(self):
        """
        Create a superuser and some UserRequestHistory instances for testing.
        """
        self.superuser = get_user_model().objects.create_superuser(
            username='superuser',
            password='superpassword'
        )
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.client.force_authenticate(user=self.superuser)

        # Create history entries for the user
        self.history_entry1 = UserRequestHistory.objects.create(
            date=timezone.now(),
            name='Company A',
            symbol='CMPA',
            open=Decimal('100.00'),
            high=Decimal('110.00'),
            low=Decimal('90.00'),
            close=Decimal('105.00'),
            user=self.user
        )
        self.history_entry2 = UserRequestHistory.objects.create(
            date=timezone.now(),
            name='Company A',
            symbol='CMPA',
            open=Decimal('200.00'),
            high=Decimal('210.00'),
            low=Decimal('190.00'),
            close=Decimal('205.00'),
            user=self.user
        )
        self.history_entry3 = UserRequestHistory.objects.create(
            date=timezone.now(),
            name='Company B',
            symbol='CMPB',
            open=Decimal('300.00'),
            high=Decimal('310.00'),
            low=Decimal('290.00'),
            close=Decimal('305.00'),
            user=self.user
        )

    def test_stats_view_success(self):
        """
        Test that the StatsView returns the most queried stocks for superusers.
        """
        response = self.client.get('/stats')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Expected data should match the format returned by the view
        expected_data = [
            {"stock": "cmpa", "times_requested": 2},
            {"stock": "cmpb", "times_requested": 1}
        ]

        # Format the response data similarly to the expected data
        formatted_response_data = [
            {"stock": stock['stock'].lower(), "times_requested": stock['times_requested']}
            for stock in response.data
        ]

        # Assert that the formatted response matches the expected data
        self.assertCountEqual(formatted_response_data, expected_data)

    def test_stats_view_permission_denied(self):
        """
        Test that a non-superuser receives a permission denied response.
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/stats')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"error": "Permission denied"})

    def test_stats_view_no_data(self):
        """
        Test the StatsView response when there are no data entries.
        """
        # Clear existing data
        UserRequestHistory.objects.all().delete()

        response = self.client.get('/stats')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def tearDown(self):
        """
        Clean up any objects created during the tests.
        """
        UserRequestHistory.objects.all().delete()
        get_user_model().objects.all().delete()
