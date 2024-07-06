"""Tests for the ingredients API."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse("recipe:ingredient-list")


def create_user(email="test@example.com", password="good_password_123!"):
    return get_user_model().objects.create_user(email=email, password=password)


def detailed_url(ingredient_id):
    """Create and reutng an ingredient detailed url."""
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


class PublicIngredientsApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_requried(self):
        """Test auth is required for retrieving ingredients."""
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self) -> None:
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def retrieve_ingredient_list(self):
        """Test retreiving a list of recipes."""
        Ingredient.objects.create(user=self.user, name="Ing1")
        Ingredient.objects.create(user=self.user, name="Ing2")
        res = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_update_ingredient(self):
        ingredient = Ingredient.objects.create(user=self.user, name="OrigName")
        payload = {"name": "UpdatedName"}
        res = self.client.patch(detailed_url(ingredient.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload["name"])

    def test_ingredients_limited_to_user(self):
        other_user = create_user(email="other_user@example.com")
        ingredient = Ingredient.objects.create(
            user=self.user, name="CorrectIngredient"
        )
        Ingredient.objects.create(user=other_user, name="Other Ingredient")

        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], ingredient.name)
        self.assertEqual(res.data[0]["id"], ingredient.id)

    def test_delete_ingredient(self):
        ingredient = Ingredient.objects.create(user=self.user, name="OrigName")
        res = self.client.delete(detailed_url(ingredient.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())
