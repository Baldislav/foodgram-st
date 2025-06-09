from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
    UserSerializer as DjoserUserSerializer,
)
from drf_extra_fields.fields import Base64ImageField
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated

from .constants import ERROR_MESSAGES, MAX_NAME_LENGTH, MIN_INGREDIENT_AMOUNT
from recipes.models import Ingredient, Recipe, IngredientInRecipe

UserModel = get_user_model()


class UserCreateSerializer(DjoserUserCreateSerializer):
    first_name = serializers.CharField(required=True, max_length=MAX_NAME_LENGTH)
    last_name = serializers.CharField(required=True, max_length=MAX_NAME_LENGTH)

    class Meta(DjoserUserCreateSerializer.Meta):
        model = UserModel
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
        )


class UserDetailSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = UserModel
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )
        read_only_fields = ("id", "is_subscribed", "avatar")

    def to_representation(self, user_instance):
        if not user_instance or getattr(user_instance, "is_anonymous", True):
            raise NotAuthenticated(
                "Authentication credentials were not provided."
            )
        return super().to_representation(user_instance)

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            return False

        return obj.following.filter(user=user).exists()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
        read_only_fields = ("id", "name", "measurement_unit")


class IngredientAmountSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    def validate_amount(self, value):
        if value < MIN_INGREDIENT_AMOUNT:
            raise serializers.ValidationError(
                f"Количество ингредиента должно быть не меньше {MIN_INGREDIENT_AMOUNT}."
            )
        return value


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = IngredientInRecipe
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def validate(self, data):
        required_fields = {"ingredients", "name", "text", "cooking_time", "image"}
        missing_fields = required_fields - set(self.initial_data.keys())
        if missing_fields:
            error_msg = ERROR_MESSAGES.get(
                "field_required_patch", ERROR_MESSAGES.get("field_required_post_put")
            )
            raise serializers.ValidationError(
                {field: [error_msg] for field in missing_fields}
            )
        image_value = self.initial_data.get("image", None)
        if image_value in ("", None):
            raise serializers.ValidationError({"image": [ERROR_MESSAGES["image_empty"]]})
        return data

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError("Пожалуйста, укажите ингредиенты.")

        ids = []
        for item in ingredients:
            if not isinstance(item, dict):
                raise serializers.ValidationError(
                    "Каждый ингредиент должен быть объектом с 'id' и 'amount'."
                )
            if "id" not in item or "amount" not in item:
                raise serializers.ValidationError("Каждый ингредиент должен содержать 'id' и 'amount'.")
            ids.append(item["id"])

        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Ингредиенты не должны повторяться.")

        return ingredients

    def _update_ingredients(self, recipe_instance, ingredients_list):
        IngredientInRecipe.objects.filter(recipe=recipe_instance).delete()
        objs_to_create = []
        for item in ingredients_list:
            try:
                ingredient = Ingredient.objects.get(id=item["id"])
            except Ingredient.DoesNotExist:
                raise serializers.ValidationError(f"Ингредиент с id={item['id']} не найден.")
            objs_to_create.append(
                IngredientInRecipe(
                    recipe=recipe_instance,
                    ingredient=ingredient,
                    amount=item["amount"]
                )
            )
        IngredientInRecipe.objects.bulk_create(objs_to_create)

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        self._update_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        instance = super().update(instance, validated_data)
        self._update_ingredients(instance, ingredients_data)
        return instance
    

class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserDetailSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(many=True, source="ingredient_amounts", read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = fields

    def get_is_favorited(self, recipe_obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or user.is_anonymous:
            return False
        return recipe_obj.favorited_by.filter(user=user).exists()

    def get_is_in_shopping_cart(self, recipe_obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or user.is_anonymous:
            return False
        return recipe_obj.in_shopping_carts_of.filter(user=user).exists()


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = ("id", "name", "image", "cooking_time")


class UserWithRecipesSerializer(UserDetailSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source="recipes.count", read_only=True)

    class Meta(UserDetailSerializer.Meta):
        fields = UserDetailSerializer.Meta.fields + ("recipes", "recipes_count")
        read_only_fields = UserDetailSerializer.Meta.read_only_fields + (
            "recipes",
            "recipes_count",
        )

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes_limit = None
        if request:
            try:
                recipes_limit = int(request.query_params.get("recipes_limit"))
            except (TypeError, ValueError):
                pass

        recipes_qs = obj.recipes.all()
        if recipes_limit is not None:
            recipes_qs = recipes_qs[:recipes_limit]
        return RecipeShortSerializer(recipes_qs, many=True, context=self.context).data


class AvatarUploadSerializer(serializers.Serializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        fields = ("avatar",)


class AvatarResponseSerializer(serializers.Serializer):
    avatar = serializers.URLField(read_only=True)

    class Meta:
        fields = ("avatar",)


class RecipeShortLinkSerializer(serializers.Serializer):
    short_link = serializers.URLField(read_only=True, source="get_short_link")

    class Meta:
        fields = ("short_link",)
