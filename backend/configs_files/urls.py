from django.contrib import admin
from django.urls import path, include

from api.views import recipe_short_redirect_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "s/<int:pk>/", recipe_short_redirect_view, name="recipe-short-redirect"
    ),
    path(
        "api/auth/", include("djoser.urls.authtoken")
    ),
    path(
        "api/", include("api.urls")
    ),
    path(
        "api/", include("djoser.urls")
    ),
]
