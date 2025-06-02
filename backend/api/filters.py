import django_filters
from django.contrib.auth import get_user_model
from django_filters.rest_framework import FilterSet, CharFilter

from recipes.models import Recipe, Ingredient


User = get_user_model()


class RecipeFilter(django_filters.FilterSet):
    class Meta:
        model = Recipe
        fields = ["author"]


class IngredientFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name",)
