from django.contrib import admin

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


class OptimizedQuerysetMixin:
    """Миксин для оптимизации запросов."""

    def get_queryset(self, request):
        """Возвращает оптимизированный queryset."""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related(
            'user', 'recipe__author'
        )
        return queryset


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
    search_fields = ('name',)
    list_filter = (
        'author__username',
        'tags'
    )
    inlines = (RecipeIngredientInline,)

    def get_queryset(self, request):
        """Возвращает оптимизированный queryset для списка рецептов."""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related(
            'author'
        ).prefetch_related('tags', 'recipe_ingredients__ingredient')
        return queryset


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Административное представление ингредиентов рецепта."""

    list_display = ('id', 'name', 'measurement_unit')
    list_display_links = ('name',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Административное представление тегов рецепта."""

    list_display = ('id', 'name', 'slug')
    list_display_links = ('name',)
    search_fields = ('name',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin, OptimizedQuerysetMixin):
    """Административное представление избранного."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin, OptimizedQuerysetMixin):
    """Административное представление  списка покупок."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


admin.site.empty_value_display = '-пусто-'
