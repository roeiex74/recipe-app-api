"""Test for recipe API's."""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe, Tag, Ingredient
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
        self.assertEqual(res.status_code, status.HTTP_200_OK)
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

    def test_create_recipe_with_tag(self):
        """Create a recipe with a new tag."""
        payload = {
            "title": "New Recipe title",
            "link": "https://newrecipe.com/recipe.pdf",
            "time_minutes": 15,
            "price": Decimal("5.55"),
            "tags": [{"name": "Tag1"}, {"name": "Tag2"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recepies = Recipe.objects.filter(user=self.user)
        self.assertEqual(len(recepies), 1)
        recipe = recepies[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload["tags"]:
            exists = Tag.objects.filter(
                name=tag["name"], user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tags."""
        tag = Tag.objects.create(name="FirstTag", user=self.user)
        payload = {
            "title": "SampleRecipe",
            "time_minutes": 10,
            "price": Decimal("9.91"),
            "tags": [{"name": "FirstTag"}, {"name": "NonExistingTag"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recepies = Recipe.objects.filter(user=self.user)
        self.assertEqual(len(recepies), 1)
        recipe = recepies[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag, recipe.tags.all())
        for tag_data in payload["tags"]:
            exists = Tag.objects.filter(
                name=tag_data["name"], user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating a tag when updating a recipe."""
        recipe = create_recipe(user=self.user)
        payload = {
            "tags": [{"name": "FirstTag"}, {"name": "NonExistingTag"}],
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # refresh from db is not needed in many-to-many relationships
        # recipe.refresh_from_db()
        for tag in payload["tags"]:
            new_tag = Tag.objects.get(user=self.user, name=tag["name"])
            self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe."""
        tag_created = Tag.objects.create(user=self.user, name="Tag1")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_created)
        another_tag = Tag.objects.create(user=self.user, name="Tag2")
        payload = {"tags": [{"name": another_tag.name}]}
        url = detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(another_tag, recipe.tags.all())
        self.assertNotIn(tag_created, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing a recipe tags."""
        tag = Tag.objects.create(user=self.user, name="Tag1")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)
        payload = {"tags": []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(tag, recipe.tags.all())
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_ingredients(self):
        """Test creating a recipe with Ingredient."""

        payload = {
            "title": "New Recipe title",
            "link": "https://newrecipe.com/recipe.pdf",
            "time_minutes": 15,
            "price": Decimal("5.55"),
            "ingredients": [{"name": "ing1"}, {"name": "ing2"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recepies = Recipe.objects.filter(user=self.user)

        self.assertEqual(len(recepies), 1)
        recipe = recepies[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload["ingredients"]:
            exists = Ingredient.objects.filter(
                name=ingredient["name"], user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        """Create a recipe with existing ingredients."""
        ingredient = Ingredient.objects.create(user=self.user, name="Ingr1")
        payload = {
            "title": "New Recipe title",
            "link": "https://newrecipe.com/recipe.pdf",
            "time_minutes": 15,
            "price": Decimal("5.55"),
            "ingredients": [
                {"name": ingredient.name},
                {"name": "NonExistingIng"},
            ],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Check that no new ingredient has been created.
        recipes = Recipe.objects.filter(user=self.user)
        # Check recipe has been created
        self.assertEqual(len(recipes), 1)
        # Check the ingredient is assigned to recipe
        self.assertIn(ingredient, recipes[0].ingredients.all())
        self.assertEqual(recipes[0].ingredients.count(), 2)

        for paylod_ingredient in payload["ingredients"]:
            exists = Ingredient.objects.filter(
                user=self.user, name=paylod_ingredient["name"]
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """Update an existing recipe with new ingredients."""
        payload = {
            "ingredients": [
                {"name": "Ing1"},
                {"name": "Ing2"},
            ],
        }
        recipe = create_recipe(user=self.user)
        res = self.client.patch(detail_url(recipe.id), payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.ingredients.count(), 2)
        for paylod_ingredient in payload["ingredients"]:
            new_ingredient = Ingredient.objects.get(
                user=self.user, name=paylod_ingredient["name"]
            )
            self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """Assing an existing tag to a recipe on update"""
        NotAssignedIngredient = Ingredient.objects.create(
            user=self.user, name="NotAssigned"
        )
        AssignedIngredient = Ingredient.objects.create(
            user=self.user, name="Assigned"
        )
        payload = {"ingredients": [{"name": AssignedIngredient.name}]}
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(NotAssignedIngredient)
        res = self.client.patch(detail_url(recipe.id), payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn(AssignedIngredient, recipe.ingredients.all())
        self.assertNotIn(NotAssignedIngredient, recipe.ingredients.all())

    def test_clear_ingredients(self):
        """Test clearing a single recipe ingredients."""
        ingredient = Ingredient.objects.create(user=self.user, name="Ing1")
        recipe = create_recipe(self.user)
        recipe.ingredients.add(ingredient)
        payload = {"ingredients": []}
        res = self.client.patch(detail_url(recipe.id), payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(ingredient, recipe.ingredients.all())
        self.assertEqual(recipe.ingredients.count(), 0)
