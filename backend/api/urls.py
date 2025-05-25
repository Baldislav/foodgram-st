from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientViewSet,
    RecipeViewSet,
    UserSubscriptionViewSet,
    AvatarUploadView,
)

app_name = "api_v1"

api_router = DefaultRouter()
api_router.register(r"ingredients", IngredientViewSet, basename="ingredient")
api_router.register(r"recipes", RecipeViewSet, basename="recipe")
api_router.register(r"users", UserSubscriptionViewSet, basename="user-subscription")

urlpatterns = [
    path("", include(api_router.urls)),
    path("users/me/avatar/", AvatarUploadView.as_view(), name="user_avatar"),
]
