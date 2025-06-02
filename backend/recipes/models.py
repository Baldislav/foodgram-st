from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

from .constants import (
    INGREDIENT_VERBOSE_NAME,
    INGREDIENT_VERBOSE_NAME_PLURAL,
    INGREDIENT_NAME_FIELD,
    INGREDIENT_MEASUREMENT_UNIT_FIELD,
    INGREDIENT_UNIQUE_CONSTRAINT_NAME,
    RECIPE_VERBOSE_NAME,
    RECIPE_VERBOSE_NAME_PLURAL,
    RECIPE_AUTHOR_FIELD,
    RECIPE_NAME_FIELD,
    RECIPE_IMAGE_FIELD,
    RECIPE_TEXT_FIELD,
    RECIPE_INGREDIENTS_FIELD,
    RECIPE_COOKING_TIME_FIELD,
    RECIPE_PUB_DATE_FIELD,
    INGREDIENT_IN_RECIPE_VERBOSE_NAME,
    INGREDIENT_IN_RECIPE_VERBOSE_NAME_PLURAL,
    INGREDIENT_IN_RECIPE_RECIPE_FIELD,
    INGREDIENT_IN_RECIPE_INGREDIENT_FIELD,
    INGREDIENT_IN_RECIPE_AMOUNT_FIELD,
    INGREDIENT_IN_RECIPE_UNIQUE_CONSTRAINT_NAME,
    FAVORITE_VERBOSE_NAME,
    FAVORITE_VERBOSE_NAME_PLURAL,
    FAVORITE_USER_FIELD,
    FAVORITE_RECIPE_FIELD,
    FAVORITE_UNIQUE_CONSTRAINT_NAME,
    FAVORITE_STR_FORMAT,
    SHOPPING_CART_VERBOSE_NAME,
    SHOPPING_CART_VERBOSE_NAME_PLURAL,
    SHOPPING_CART_USER_FIELD,
    SHOPPING_CART_RECIPE_FIELD,
    SHOPPING_CART_UNIQUE_CONSTRAINT_NAME,
    SHOPPING_CART_STR_FORMAT,
)

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(INGREDIENT_NAME_FIELD, max_length=200)
    measurement_unit = models.CharField(INGREDIENT_MEASUREMENT_UNIT_FIELD, max_length=200)

    class Meta:
        verbose_name = INGREDIENT_VERBOSE_NAME
        verbose_name_plural = INGREDIENT_VERBOSE_NAME_PLURAL
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name=INGREDIENT_UNIQUE_CONSTRAINT_NAME,
            )
        ]

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name=RECIPE_AUTHOR_FIELD,
    )
    name = models.CharField(RECIPE_NAME_FIELD, max_length=200)
    image = models.ImageField(RECIPE_IMAGE_FIELD, upload_to="recipes/images/")
    text = models.TextField(RECIPE_TEXT_FIELD)
    ingredients = models.ManyToManyField(
        Ingredient,
        through="IngredientInRecipe",
        related_name="recipes",
        verbose_name=RECIPE_INGREDIENTS_FIELD,
    )
    cooking_time = models.PositiveSmallIntegerField(
        RECIPE_COOKING_TIME_FIELD, validators=[MinValueValidator(1)]
    )
    pub_date = models.DateTimeField(RECIPE_PUB_DATE_FIELD, auto_now_add=True)

    class Meta:
        verbose_name = RECIPE_VERBOSE_NAME
        verbose_name_plural = RECIPE_VERBOSE_NAME_PLURAL
        ordering = ["-pub_date"]

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredient_amounts",
        verbose_name=INGREDIENT_IN_RECIPE_RECIPE_FIELD,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_amounts",
        verbose_name=INGREDIENT_IN_RECIPE_INGREDIENT_FIELD,
    )
    amount = models.PositiveSmallIntegerField(
        INGREDIENT_IN_RECIPE_AMOUNT_FIELD, validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = INGREDIENT_IN_RECIPE_VERBOSE_NAME
        verbose_name_plural = INGREDIENT_IN_RECIPE_VERBOSE_NAME_PLURAL
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name=INGREDIENT_IN_RECIPE_UNIQUE_CONSTRAINT_NAME,
            )
        ]

    def __str__(self):
        return (
            f"{self.ingredient.name} ({self.amount} {self.ingredient.measurement_unit}) "
            f"в {self.recipe.name}"
        )


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorite_recipes",
        verbose_name=FAVORITE_USER_FIELD,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorited_by",
        verbose_name=FAVORITE_RECIPE_FIELD,
    )

    class Meta:
        verbose_name = FAVORITE_VERBOSE_NAME
        verbose_name_plural = FAVORITE_VERBOSE_NAME_PLURAL
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name=FAVORITE_UNIQUE_CONSTRAINT_NAME
            )
        ]

    def __str__(self):
        return FAVORITE_STR_FORMAT.format(self.user.username, self.recipe.name)


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_cart_recipes",
        verbose_name=SHOPPING_CART_USER_FIELD,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="in_shopping_carts_of",
        verbose_name=SHOPPING_CART_RECIPE_FIELD,
    )

    class Meta:
        verbose_name = SHOPPING_CART_VERBOSE_NAME
        verbose_name_plural = SHOPPING_CART_VERBOSE_NAME_PLURAL
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name=SHOPPING_CART_UNIQUE_CONSTRAINT_NAME
            )
        ]

    def __str__(self):
        return SHOPPING_CART_STR_FORMAT.format(self.user.username, self.recipe.name)
