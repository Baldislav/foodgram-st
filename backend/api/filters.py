from django.contrib.auth import get_user_model
from django_filters.rest_framework import FilterSet, CharFilter, BooleanFilter

from recipes.models import Recipe, Ingredient

User = get_user_model()


class RecipeFilter(FilterSet):
    is_favorited = BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = BooleanFilter(method="filter_is_in_shopping_cart")

    class Meta:
        model = Recipe
        fields = ["author", "is_favorited", "is_in_shopping_cart"]

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated:
            return queryset.filter(favorited_by__user=user) if value else queryset.exclude(favorited_by__user=user)
        return queryset.none() if value else queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated:
            return queryset.filter(in_shopping_carts_of__user=user) if value else queryset.exclude(in_shopping_carts_of__user=user)
        return queryset.none() if value else queryset


class IngredientFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name",)
