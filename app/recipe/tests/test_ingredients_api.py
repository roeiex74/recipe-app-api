"""Tests for the ingredients API."""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Ingredient, Recipe
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

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test listing ingredients that are assigned to recipes."""
        ingredient1 = Ingredient.objects.create(user=self.user, name="ing1")
        ingredient2 = Ingredient.objects.create(user=self.user, name="ing2")
        recipe = Recipe.objects.create(
            user=self.user,
            title="recipe1",
            time_minutes=5,
            price=Decimal("5.50"),
        )
        recipe.ingredients.add(ingredient1, ingredient2)
        ingredient3 = Ingredient.objects.create(user=self.user, name="ing3")
        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        s1 = IngredientSerializer(ingredient1)
        s2 = IngredientSerializer(ingredient2)
        s3 = IngredientSerializer(ingredient3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filtered_ingredients_unique(self):
        """Test filtered ingredients returned list is unique."""
        ingredient1 = Ingredient.objects.create(user=self.user, name="ing1")
        Ingredient.objects.create(user=self.user, name="ing2")
        recipe1 = Recipe.objects.create(
            user=self.user,
            title="recipe1",
            time_minutes=5,
            price=Decimal("5.50"),
        )
        recipe1.ingredients.add(ingredient1)
        recipe2 = Recipe.objects.create(
            user=self.user,
            title="recipe2",
            time_minutes=10,
            price=Decimal("6.50"),
        )
        recipe2.ingredients.add(ingredient1)
        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})
        self.assertEqual(len(res.data), 1)
