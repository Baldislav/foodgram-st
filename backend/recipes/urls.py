from django.urls import path

from .views import recipe_short_redirect_view

urlpatterns = [
    path('s/<int:pk>/', recipe_short_redirect_view, name='recipe-short-redirect'),
]
