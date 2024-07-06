"""Views for the recipe API's"""

# from django.shortcuts import render
from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Recipe, Tag, Ingredient
from recipe import serializers


# Create your views here.
class RecipeViewSet(viewsets.ModelViewSet):
    """View for manage recipe API's"""

    # Viewset import multiple different endpoints
    # list endpoint, recipe by id endpoint and more
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve recipes for authenticated user."""

        # Adding filter to user by the user authenticated.
        # Since the authentication class is configures for all operations.
        # The user is passed by the authentication system for the request.
        return self.queryset.filter(user=self.request.user).order_by("-id")

    def get_serializer_class(self):
        """Return the serializer class by the type of request."""
        # Modify the serializer_class that is configured by default
        if self.action == "list":
            return serializers.RecipeSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe."""
        # Overwrite the behaviour when django saves a created object.
        serializer.save(user=self.request.user)


# Mixins must be defined before inoreder to use it
# So we can overwrite the behavior


class BaseRecipeAtrrViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Base viewset for generic recipe attributes."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve attribure for authenciated user"""
        return self.queryset.filter(user=self.request.user).order_by("-name")


class TagViewSet(BaseRecipeAtrrViewSet):
    """Manage Tags in the database."""

    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAtrrViewSet):
    """Manage Ingredients in the database."""

    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
