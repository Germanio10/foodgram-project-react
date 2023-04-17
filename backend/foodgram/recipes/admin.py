from django.contrib import admin
from .models import (Ingredient, Tag, Recipe, RecipeIngredient, Favorite,
                     ShoppingCart)

admin.site.register(Ingredient)
admin.site.register(Tag)
admin.site.register(Recipe)
admin.site.register(RecipeIngredient)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
