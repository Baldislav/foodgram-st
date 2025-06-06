# Ingredient
INGREDIENT_VERBOSE_NAME = "Ингредиент"
INGREDIENT_VERBOSE_NAME_PLURAL = "Ингредиенты"
INGREDIENT_NAME_FIELD = "Название ингредиента"
INGREDIENT_MEASUREMENT_UNIT_FIELD = "Единица измерения"
INGREDIENT_UNIQUE_CONSTRAINT_NAME = "unique_ingredient_measurement_unit"

# Recipe
RECIPE_VERBOSE_NAME = "Рецепт"
RECIPE_VERBOSE_NAME_PLURAL = "Рецепты"
RECIPE_AUTHOR_FIELD = "Автор рецепта"
RECIPE_NAME_FIELD = "Название рецепта"
RECIPE_IMAGE_FIELD = "Картинка рецепта"
RECIPE_TEXT_FIELD = "Описание рецепта"
RECIPE_INGREDIENTS_FIELD = "Ингредиенты"
RECIPE_COOKING_TIME_FIELD = "Время приготовления (в минутах)"
RECIPE_PUB_DATE_FIELD = "Дата публикации"

# IngredientInRecipe
INGREDIENT_IN_RECIPE_VERBOSE_NAME = "Ингредиент в рецепте"
INGREDIENT_IN_RECIPE_VERBOSE_NAME_PLURAL = "Ингредиенты в рецептах"
INGREDIENT_IN_RECIPE_RECIPE_FIELD = "Рецепт"
INGREDIENT_IN_RECIPE_INGREDIENT_FIELD = "Ингредиент"
INGREDIENT_IN_RECIPE_AMOUNT_FIELD = "Количество"
INGREDIENT_IN_RECIPE_UNIQUE_CONSTRAINT_NAME = "unique_recipe_ingredient"

# Favorite
FAVORITE_VERBOSE_NAME = "Избранный рецепт"
FAVORITE_VERBOSE_NAME_PLURAL = "Избранные рецепты"
FAVORITE_USER_FIELD = "Пользователь"
FAVORITE_RECIPE_FIELD = "Рецепт"
FAVORITE_UNIQUE_CONSTRAINT_NAME = "unique_user_favorite_recipe"
FAVORITE_STR_FORMAT = "добавил в избранное"

# ShoppingCart
SHOPPING_CART_VERBOSE_NAME = "Рецепт в списке покупок"
SHOPPING_CART_VERBOSE_NAME_PLURAL = "Рецепты в списках покупок"
SHOPPING_CART_USER_FIELD = "Пользователь"
SHOPPING_CART_RECIPE_FIELD = "Рецепт"
SHOPPING_CART_UNIQUE_CONSTRAINT_NAME = "unique_user_shopping_cart_recipe"
SHOPPING_CART_STR_FORMAT = "добавил в список покупок"

# Максимальная длина полей
INGREDIENT_NAME_MAX_LENGTH = 128
INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH = 64
RECIPE_NAME_MAX_LENGTH = 256

# Минимальные значения
RECIPE_COOKING_TIME_MIN_VALUE = 1
INGREDIENT_AMOUNT_MIN_VALUE = 1