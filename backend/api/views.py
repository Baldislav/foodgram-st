from django.contrib.auth import get_user_model
from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.models import Follow
from .filters import IngredientFilter, RecipeFilter
from .pagination import FoodgramPageNumberPagination
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (
    AvatarResponseSerializer as SetAvatarResponseSerializer,
    AvatarUploadSerializer as SetAvatarSerializer,
    IngredientSerializer,
    RecipeDetailSerializer,
    RecipeShortSerializer,
    UserWithRecipesSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
)

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthorOrAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = RecipeFilter
    search_fields = ["name"]
    ordering_fields = ["pub_date", "name"]
    ordering = ["-pub_date"]

    queryset = Recipe.objects.select_related("author").prefetch_related(
        "ingredient_amounts__ingredient",
        "favorited_by",
        "in_shopping_carts_of",
        )

    def get_serializer_class(self):
        if self.action in ['favorite', 'shopping_cart']:
            return RecipeShortSerializer
        return RecipeDetailSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже в избранном."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = self.get_serializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            favorite_instance = Favorite.objects.filter(user=user, recipe=recipe)
            if not favorite_instance.exists():
                return Response(
                    {"errors": "Рецепта нет в избранном."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            favorite_instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = self.get_serializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            cart_item = ShoppingCart.objects.filter(user=user, recipe=recipe)
            if not cart_item.exists():
                return Response(
                    {"errors": "Рецепта нет в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])

    def download_shopping_cart(self, request):
        user = request.user

        totals = (
            IngredientInRecipe.objects.filter(recipe__in_shopping_carts_of__user=user)
            .values(name=F("ingredient__name"), unit=F("ingredient__measurement_unit"))
            .annotate(total=Sum("amount"))
            .order_by("name")
        )

        if not totals.exists():
            return Response(
                {"errors": "Ваш список покупок пуст, или в рецептах нет ингредиентов."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        recipe_info = (
            Recipe.objects.filter(in_shopping_carts_of__user=user)
            .values_list("name", "author__username")
            .order_by("name")
        )

        report_lines = [
            f"Список покупок Foodgram на {timezone.localdate():%d.%m.%Y}:",
            "\nПродукты:",
        ]
        for idx, row in enumerate(totals, 1):
            report_lines.append(f"{idx}. {row['name'].capitalize()} ({row['unit']}) — {row['total']}")

        report_lines.append("\nРецепты, для которых нужны эти продукты:")
        for idx, (title, author_username) in enumerate(recipe_info, 1):
            report_lines.append(f"{idx}. {title} — @{author_username}")

        report_text = "\n".join(report_lines)

        response = HttpResponse(report_text, content_type="text/plain; charset=utf-8")
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response


    @action(detail=True, methods=["get"], permission_classes=[AllowAny], url_path="get-link")
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_redirect_path = f"/s/{recipe.pk}/"

        absolute_short_link_url = request.build_absolute_uri(short_redirect_path)

        return Response({"short-link": absolute_short_link_url}, status=status.HTTP_200_OK)


class AvatarViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["put"])
    def avatar(self, request):
        user = request.user
        serializer = SetAvatarSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            if user.avatar:
                user.avatar.delete(save=False)
            user.avatar = serializer.validated_data['avatar']
            user.save()

            avatar_url = request.build_absolute_uri(user.avatar.url) if user.avatar else None
            response_serializer = SetAvatarResponseSerializer({"avatar": avatar_url})
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserSubscriptionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = FoodgramPageNumberPagination
    serializer_class = UserWithRecipesSerializer

    @action(detail=False, methods=["get"], url_path="subscriptions")
    def get_user_subscriptions(self, request):
        user = request.user

        authors_queryset = (
            User.objects.filter(follower__user=user)
            .prefetch_related("recipes")
            .order_by("username")
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(authors_queryset, request, view=self)

        serializer = self.serializer_class(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=["post", "delete"], url_path="subscribe")
    def manage_subscription(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        user = request.user

        if user == author:
            return Response(
                {"errors": "Нельзя подписаться на самого себя."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == "POST":
            follow, created = Follow.objects.get_or_create(user=user, author=author)
            if not created:
                return Response(
                    {"errors": "Вы уже подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = self.serializer_class(author, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            deleted_count, _ = Follow.objects.filter(user=user, author=author).delete()
            if not deleted_count:
                return Response(
                    {"errors": "Вы не были подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

