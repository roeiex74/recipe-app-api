"""Tests for the tag API."""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Tag, Recipe
from recipe.serializers import TagSerializer

TAGS_URL = reverse("recipe:tag-list")


def create_user(email="testUser@example.com", password="good_password123"):
    return get_user_model().objects.create_user(email, password)


def detailed_url(tag_id):
    """Create and return a tag detailed url."""
    return reverse("recipe:tag-detail", args=[tag_id])


class PublicTagsApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_auth_requried(self):
        """Test auth is required for retrieving tags."""
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test authenticated api requests."""

    def setUp(self) -> None:
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retreiving a list of tags."""
        Tag.objects.create(user=self.user, name="TestTag1")
        Tag.objects.create(user=self.user, name="TestTag2")
        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by("-name")
        # A list of object is expected - hence many=True
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test list of tags is limited to authenticated user."""
        user2 = create_user(email="anotherOne@example.com")
        Tag.objects.create(user=user2, name="Tag Name")
        Tag.objects.create(user=self.user, name="Tag Name")
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tags = Tag.objects.filter(user=self.user)
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_update_tag(self):
        """Test tag update."""
        tag = Tag.objects.create(user=self.user, name="testTag1")
        payload = {"name": "NewName"}
        res = self.client.patch(detailed_url(tag.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload["name"])

    def test_delete_tag(self):
        """Test deleting a tag."""
        tag = Tag.objects.create(user=self.user, name="testTag1")
        res = self.client.delete(detailed_url(tag.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_tags_assigned_to_recipes(self):
        """Test listing tags that are assigned to recipes."""
        tag1 = Tag.objects.create(user=self.user, name="tag1")
        tag2 = Tag.objects.create(user=self.user, name="tag2")
        recipe = Recipe.objects.create(
            user=self.user,
            title="recipe1",
            time_minutes=5,
            price=Decimal("5.50"),
        )
        recipe.tags.add(tag1, tag2)
        tag3 = Tag.objects.create(user=self.user, name="tag3")
        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        s3 = TagSerializer(tag3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filtered_tags_unique(self):
        """Test filtered tag returned list is unique."""
        tag1 = Tag.objects.create(user=self.user, name="tag1")
        Tag.objects.create(user=self.user, name="tag2")
        recipe1 = Recipe.objects.create(
            user=self.user,
            title="recipe1",
            time_minutes=5,
            price=Decimal("5.50"),
        )
        recipe1.tags.add(tag1)
        recipe2 = Recipe.objects.create(
            user=self.user,
            title="recipe2",
            time_minutes=10,
            price=Decimal("6.50"),
        )
        recipe2.tags.add(tag1)
        res = self.client.get(TAGS_URL, {"assigned_only": 1})
        self.assertEqual(len(res.data), 1)
