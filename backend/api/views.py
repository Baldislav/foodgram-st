from rest_framework import viewsets, filters, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404, redirect
from recipes.models import Recipe
from django.http import FileResponse, Http404
from django.db.models import F, Sum
from django.utils import timezone
from django.http import HttpResponse
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import (
    Ingredient,
    Recipe,
    IngredientInRecipe,
    Favorite,
    ShoppingCart,
)

from django.contrib.auth import get_user_model
from users.models import Follow

from .serializers import (
    IngredientSerializer,
    RecipeDetailSerializer,
    RecipeShortSerializer,
    UserWithRecipesSerializer,
    AvatarUploadSerializer as SetAvatarSerializer,
    AvatarResponseSerializer as SetAvatarResponseSerializer,
)

from .permissions import IsAuthorOrAdminOrReadOnly
from .filters import IngredientFilter
from .pagination import FoodgramPageNumberPagination

User = get_user_model()


@api_view(["GET"])
def recipe_short_redirect_view(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    return redirect(f"/recipes/{recipe.pk}/")


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthorOrAdminOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["author"]
    search_fields = ["name"]
    ordering_fields = ["pub_date", "name"]
    ordering = ["-pub_date"]

    def get_queryset(self):
        queryset = Recipe.objects.select_related("author").prefetch_related(
            "ingredient_amounts__ingredient",
            "favorited_by",
            "in_shopping_carts_of",
        )

        user = self.request.user
        query_params = self.request.query_params
        is_favorited_param = query_params.get("is_favorited")
        if is_favorited_param in ["true", "1"] and user.is_authenticated:
            queryset = queryset.filter(favorited_by__user=user)
        elif is_favorited_param in ["false", "0"] and user.is_authenticated:
            queryset = queryset.exclude(favorited_by__user=user)

        is_in_shopping_cart_param = query_params.get("is_in_shopping_cart")
        if is_in_shopping_cart_param in ["true", "1"] and user.is_authenticated:
            queryset = queryset.filter(in_shopping_carts_of__user=user)
        elif is_in_shopping_cart_param in ["false", "0"] and user.is_authenticated:
            queryset = queryset.exclude(in_shopping_carts_of__user=user)
        return queryset

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


class AvatarUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = SetAvatarSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Удаляем старый аватар, если есть
            if user.avatar:
                user.avatar.delete(save=False)

            # Сохраняем новый аватар
            user.avatar = serializer.validated_data['avatar']
            user.save()

            avatar_url = request.build_absolute_uri(user.avatar.url) if user.avatar else None

            response_serializer = SetAvatarResponseSerializer({"avatar": avatar_url})
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        if user.avatar:
            user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserSubscriptionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = FoodgramPageNumberPagination

    def get_serializer_class(self):
        return UserWithRecipesSerializer

    @action(detail=False, methods=["get"], url_path="subscriptions")
    def get_user_subscriptions(self, request):
        user = request.user
        subscribed_author_ids = Follow.objects.filter(user=user).values_list("author_id", flat=True)

        authors_queryset = (
            User.objects.filter(pk__in=subscribed_author_ids)
            .prefetch_related("recipes")
            .order_by("username")
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(authors_queryset, request, view=self)

        serializer_context = {"request": request}
        serializer = self.get_serializer_class()(page, many=True, context=serializer_context)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=["post", "delete"], url_path="subscribe")
    def manage_subscription(self, request, pk=None):
        author_to_subscribe = get_object_or_404(User, pk=pk)
        current_user = request.user

        if current_user == author_to_subscribe:
            return Response(
                {"errors": "Нельзя подписаться на самого себя."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == "POST":
            follow_instance, created = Follow.objects.get_or_create(user=current_user, author=author_to_subscribe)
            if not created:
                return Response(
                    {"errors": "Вы уже подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer_context = {"request": request}
            author_instance = User.objects.prefetch_related("recipes").get(pk=author_to_subscribe.pk)
            serializer = self.get_serializer_class()(author_instance, context=serializer_context)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            deleted_count, _ = Follow.objects.filter(user=current_user, author=author_to_subscribe).delete()
            if deleted_count == 0:
                return Response(
                    {"errors": "Вы не были подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405)
