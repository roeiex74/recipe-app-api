"""Test for recipe API's."""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and return the recipe detail URL."""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a recipe."""
    defaults = {
        "title": "Default recipe",
        "time_minutes": 5,
        "price": Decimal("5.25"),
        "description": "Short default description for default recipe.",
        "link": "http://example.com/default_recipe.pdf",
    }
    defaults.update(params)
    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    """Create and return new user."""
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API request."""

    def setUp(self):
        # Set up test client for this class.
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for calling the API."""
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_user(
            email="test@example.com", password="good_password"
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        # Create two basic recipes.
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_create_list_limited_to_user(self):
        """Test list or recipes is limited to the authenticated user."""
        other_user = create_user(
            email="test_user2@example.com", password="password123123"
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail."""
        recipe = create_recipe(user=self.user)
        RECIPE_DETAIL_URL = detail_url(recipe_id=recipe.id)
        res = self.client.get(RECIPE_DETAIL_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe."""
        payload = {
            "title": "Test Recipe",
            "time_minutes": 30,
            "price": Decimal("5.99"),
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(pk=res.data["id"])
        for k, v in payload.items():
            # Compare the created recipe values, with the provided
            # Payload values.
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of recipe."""
        original_link = "https://example.com/recipe.pdf"
        recipe = create_recipe(
            user=self.user, title="Test Title", link=original_link
        )
        payload = {
            "title": "New Recipe title",
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test full recipe update."""
        original_link = "https://example.com/recipe.pdf"
        recipe = create_recipe(
            user=self.user,
            title="Test Title",
            link=original_link,
            description="Sample recipe description",
        )
        payload = {
            "title": "New Recipe title",
            "link": "https://newrecipe.com/recipe.pdf",
            "description": "New recipe description",
            "time_minutes": 15,
            "price": Decimal("5.55"),
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for attr, value in payload.items():
            self.assertEqual(getattr(recipe, attr), value)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the recipe user results in an error."""
        new_user = create_user(
            name="User Failure",
            email="FailedUser@example.com",
            password="IamHereToFail123123",
        )
        recipe = create_recipe(
            user=self.user,
            link="https://example.com/recipe.pdf",
            title="Sample Recipe",
            description="Sample recipe description",
        )
        payload = {"user": new_user.id}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleteing a recipe successful."""
        recipe = create_recipe(
            user=self.user,
            link="https://example.com/recipe.pdf",
            title="Sample Recipe",
            description="Sample recipe description",
        )
        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        """Test deleting another users recipe ends with an error."""
        recipe = create_recipe(
            user=self.user,
            link="https://example.com/recipe.pdf",
            title="Sample Recipe",
            description="Sample recipe description",
        )
        new_user = create_user(
            email="user_delete@example.com",
            password="IamHereToDeleteOtherUsersRecipe1234",
        )
        self.client.force_authenticate(new_user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
