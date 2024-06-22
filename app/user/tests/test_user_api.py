"""
Tests for the user API
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")


def create_user(**params):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)


class PublicUserAPITests(TestCase):
    """Test publilc feature of the user API. no auth needed."""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating user is successeful."""
        payload = {
            "email": "test@example.com",
            "password": "test123123",
            "name": "testUser Name",
        }
        res = self.client.post(CREATE_USER_URL, payload)

        # Check for create response code , and check if user actually created
        # and check for valid data by comparing the password.
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        # Asser password is not part of response data
        self.assertNotIn("password", res.data)

    def test_user_with_email_exists(self):
        """Test error returned if user with email exists."""
        payload = {
            "email": "test@example.com",
            "password": "test123123",
            "name": "testUser Name",
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test error is returned if passsword length under 5 characters."""
        payload = {
            "email": "test@example.com",
            "password": "1234",
            "name": "testUser Name",
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = (
            get_user_model().objects.filter(email=payload["email"]).exists()
        )
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generates a token for test user."""
        user_details = {
            "email": "test@example.com",
            "password": "good_password_1234",
            "name": "testUser Name",
        }
        create_user(**user_details)
        payload = {
            "email": user_details["email"],
            "password": user_details["password"],
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("token", res.data)

    def test_create_token_bad_credentials(self):
        """Test return error if credentials not valid."""
        user_details = {
            "email": "test@example.com",
            "password": "good_password",
            "name": "testUser Name",
        }
        create_user(**user_details)
        payload = {"email": user_details["email"], "password": "bad_password"}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test posting a blank password returns an error."""
        payload = {
            "email": "blank_test_user@example.com",
            "password": "",
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for users."""

        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserAPITests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self) -> None:
        # Set up a user, the client connection and force the authentication
        # so we wont do this for every single method
        self.user = create_user(
            email="test@example.com",
            name="User Name",
            password="good_password",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user."""
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data,
            {
                "email": self.user.email,
                "name": self.user.name,
            },
        )

    def test_post_me_not_allowed(self):
        """Test POST is not allowed for the ME endpoint."""
        res = self.client.post(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profiel(self):
        """Test updating the user profile for authenticated user."""
        payload = {"name": "New name", "password": "newpassword123"}
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()

        self.assertEqual(self.user.name, payload["name"])
        self.assertTrue(self.user.check_password(payload["password"]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
