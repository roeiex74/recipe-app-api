"""
Tests for models.
"""

from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from core import models


def create_user(email="testUser@example.com", password="goodpass123!"):
    return get_user_model().objects.create_user(email=email, password=password)


class ModelTest(TestCase):
    """Test models."""

    def test_creat_user_with_email_successful(self):
        """Test creating a user with email is successful."""
        email = "test@example.com"
        password = "test123123"
        user = get_user_model().objects.create_user(
            email=email, password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_noramlized(self):
        """Test email is normalized for new users."""
        sample_emails = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            [
                "Test2@EXAMPLE.com",
                "Test2@example.com",
            ],
            ["TEST3@EXAmple.com", "TEST3@example.com"],
        ]
        for cur_email, norm_email in sample_emails:
            user = get_user_model().objects.create_user(email=cur_email)
            self.assertEqual(user.email, norm_email)

    def test_new_user_without_user_raises_error(self):
        """Test that creating a user without an emails raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "pass123")

    def test_create_superuser(self):
        """Test creating super user"""
        user = get_user_model().objects.create_superuser(
            "test_super@example.com", "test123"
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test creating recipe is successful."""
        user = create_user()
        recipe = models.Recipe.objects.create(
            user=user,
            title="Sample Recipe",
            time_minutes=5,
            price=Decimal("5.50"),
            description="Sample recipe short description",
        )
        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """Test create tag is successeful."""
        user = create_user()
        tag = models.Tag.objects.create(
            user=user,
            name="Tag Name",
        )
        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        """Test create ingredient is successeful."""
        user = create_user()
        ingredient = models.Ingredient.objects.create(
            name="TestIngredient", user=user
        )
        self.assertEqual(str(ingredient), ingredient.name)

    @patch("core.models.uuid.uuid4")
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test generating image path."""
        uuid = "test-uuid"
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, "example.jpg")
        self.assertEqual(file_path, f"uploads/recipe/{uuid}.jpg")
