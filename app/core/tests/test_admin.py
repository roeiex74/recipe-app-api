"""Test for Django admin modification."""

from django.urls import reverse
from django.test import TestCase
from django.test import Client
from django.contrib.auth import get_user_model


class AdminSiteTests(TestCase):
    """Test for Django admin."""

    def setUp(self):
        """Create user and client"""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin_user@example.com", password="test123123"
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email="simple_user@example.com",
            password="testpass123",
            name="Test User",
        )

    def test_user_list(self):
        """Test users are listed on page."""
        url = reverse("admin:core_user_changelist")
        res = self.client.get(url)
        self.assertContains(res, self.user)
        self.assertContains(res, self.user.email)

    def test_user_change(self):
        """Test users are listed on page."""
        url = reverse("admin:core_user_change", args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_create_user_page(self):
        """Test create user page availlability."""
        url = reverse("admin:core_user_add")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
