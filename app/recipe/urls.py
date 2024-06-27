"""
URL mappings for the recipe app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from recipe import views

# User router to automatically create all different endpoint
# that are availlable for that view we are adding.
router = DefaultRouter()
# Create new endpoint /recipes, and assign all the different
# endpoints that are configured by the viewSet
# ModelViewSet - support all methods for manaing the model -
# Update, Create, Delete, Read
router.register("recipes", views.RecipeViewSet)
app_name = "recipe"
urlpatterns = [path("", include(router.urls))]
