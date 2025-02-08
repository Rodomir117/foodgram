from django.contrib import admin

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


class RecipeIngredientInline(admin.TabularInline):
    """Инлайн для ингредиентов рецепта."""

    model = RecipeIngredient
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Административное представление рецептов."""

    list_display = (
        'name',
        'author',
    )
    search_fields = (
        'author__username',
        'name',
        'created_at'
    )
    list_filter = ['tags']
    inlines = [RecipeIngredientInline]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Административное представление ингредиентов рецепта."""

    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Административное представление тегов рецепта."""
    list_display = ('id', 'name', 'slug')
    search_fields = ['name']
    list_filter = ['name']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Административное представление избранного."""
    list_display = ('user', 'recipe')
    search_fields = ['user']
    list_filter = ['user']


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Административное представление  списка покупок."""
    list_display = ('user', 'recipe')
    search_fields = ['user']
    list_filter = ['user']


admin.site.empty_value_display = '-пусто-'
