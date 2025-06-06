from django.shortcuts import get_object_or_404, redirect

from .models import Recipe

def recipe_short_redirect_view(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    return redirect(f"/recipes/{recipe.pk}/")
