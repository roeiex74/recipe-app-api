""" 
Serializers for recipes API.
"""

from rest_framework import serializers
from core.models import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for Recipes Model."""

    class Meta:
        model = Recipe
        fields = ["id", "title", "time_minutes", "price", "link"]
        read_only_fields = ["id"]


# Extension of the recipe serializer, with added fields.
class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for the recipe detail view."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ["description"]
