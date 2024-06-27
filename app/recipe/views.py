"""Views for the recipe API's"""

from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Recipe
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
        else:
            return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe."""
        # Overwrite the behaviour when django saves a created object.
        serializer.save(user=self.request.user)
        return super().perform_create(serializer)
