from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(FilterSet):
    """Фильтры для рецептов."""

    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def get_authenticated_user(self):
        """Возвращает аутентифицированного пользователя, если он есть."""
        return (
            self.request.user if self.request.user.is_authenticated else None
        )

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрует рецепты по наличию в избранном."""
        user = self.get_authenticated_user()
        if value and user:
            return queryset.filter(favorites__user_id=user.id)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрует рецепты по наличию в корзине покупок."""
        user = self.get_authenticated_user()
        if value and user:
            return queryset.filter(shopping_carts__user_id=user.id)
        return queryset

    def filter_tags(self, queryset, name, value):
        """Фильтрует рецепты по тегам."""
        tag_slugs = self.request.query_params.getlist('tags')
        if tag_slugs:
            return queryset.filter(tags__slug__in=tag_slugs).distinct()
        return queryset


class IngredientFilter(FilterSet):
    """Фильтры для ингредиентов."""

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']
