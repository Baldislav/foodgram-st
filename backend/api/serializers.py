from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
    UserSerializer as DjoserUserSerializer,
)

from drf_extra_fields.fields import Base64ImageField
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated

from recipes.models import Ingredient, Recipe, IngredientInRecipe
from users.models import Follow

UserModel = get_user_model()

class UserCreateSerializer(DjoserUserCreateSerializer):
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)

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
            raise NotAuthenticated("Authentication credentials were not provided.")
        return super().to_representation(user_instance)

    def get_is_subscribed(self, author_obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=author_obj).exists()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
        read_only_fields = ("id", "name", "measurement_unit")


class IngredientAmountSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=1,
        error_messages={"min_value": "Количество должно быть не меньше 1."},
    )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(source="ingredient.measurement_unit")

    class Meta:
        model = IngredientInRecipe
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeDetailSerializer(serializers.ModelSerializer):
    author = UserDetailSerializer(read_only=True)
    ingredients = IngredientAmountSerializer(many=True, write_only=True)
    detailed_ingredients = IngredientInRecipeSerializer(
        many=True, read_only=True, source="ingredient_amounts"
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "detailed_ingredients",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = ("id", "author", "is_favorited", "is_in_shopping_cart")

    def validate(self, data):
        data = super().validate(data)
        request = self.context["request"]
        request_method = request.method

        if request_method == "PATCH":
            required_fields = {"ingredients", "name", "text", "cooking_time"}
            missing_fields = required_fields - set(self.initial_data.keys())
            if missing_fields:
                raise serializers.ValidationError({
                    field: ["This field is required for update."] for field in missing_fields
                })

        else:
            # POST or PUT
            if "image" not in self.initial_data and not self.instance:
                raise serializers.ValidationError({"image": ["This field is required."]})
            if request_method == "PUT" and "image" not in self.initial_data:
                raise serializers.ValidationError({"image": ["This field is required for PUT."]})
            if "ingredients" not in self.initial_data:
                raise serializers.ValidationError({"ingredients": ["This field is required."]})

        # Проверка на пустое значение
        image_value = self.initial_data.get("image", None)
        if image_value in ("", None):
            raise serializers.ValidationError({"image": ["Image cannot be empty."]})

        return data


    def to_representation(self, recipe_instance):
        ret = super().to_representation(recipe_instance)
        ret["ingredients"] = IngredientInRecipeSerializer(
            recipe_instance.ingredient_amounts.all(), many=True, context=self.context
        ).data
        ret.pop("detailed_ingredients", None)
        return ret

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

    def _update_ingredients(self, recipe_instance, ingredients_list):
        IngredientInRecipe.objects.filter(recipe=recipe_instance).delete()
        objs_to_create = [
            IngredientInRecipe(
                recipe=recipe_instance,
                ingredient=ingredient_data["id"],
                amount=ingredient_data["amount"],
            )
            for ingredient_data in ingredients_list
        ]
        IngredientInRecipe.objects.bulk_create(objs_to_create)

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        self._update_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients", None)
        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get("cooking_time", instance.cooking_time)
        instance.image = validated_data.get("image", instance.image)
        instance.save()

        if ingredients_data is not None:
            self._update_ingredients(instance, ingredients_data)
        return instance

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError("Пожалуйста, укажите ингредиенты.")
        ingredient_ids = [item["id"].id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError("Ингредиенты не должны повторяться.")
        return ingredients


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = ("id", "name", "image", "cooking_time")


class UserWithRecipesSerializer(UserDetailSerializer):
    recipes = RecipeShortSerializer(many=True, read_only=True)
    recipes_count = serializers.IntegerField(source='recipes.count', read_only=True)

    class Meta(UserDetailSerializer.Meta):
        fields = UserDetailSerializer.Meta.fields + ("recipes", "recipes_count")
        read_only_fields = UserDetailSerializer.Meta.read_only_fields + ("recipes", "recipes_count")

    def to_representation(self, user_instance):
        data = super().to_representation(user_instance)
        recipes_limit_param = self.context.get("request").query_params.get("recipes_limit")
        if recipes_limit_param is not None:
            try:
                limit = int(recipes_limit_param)
                recipes_qs = user_instance.recipes.all()[:limit]
            except ValueError:
                recipes_qs = user_instance.recipes.all()
        else:
            recipes_qs = user_instance.recipes.all()
        data["recipes"] = RecipeShortSerializer(recipes_qs, many=True).data
        return data


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
