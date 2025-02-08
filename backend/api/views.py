from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    SAFE_METHODS,
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.reverse import reverse

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeGetSerializer,
    RecipePostSerializer,
    ShoppingCartSerializer,
    SubscriptionGetSerializer,
    SubscriptionPostSerializer,
    TagSerializer,
    UserGetSerializer,
    UserPostSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription, User


class UserViewSet(DjoserViewSet):
    """Вьюсет для кастомного пользователя."""

    queryset = User.objects.all()
    serializer_class = UserPostSerializer
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if (
            self.action == 'list'
            or self.action == 'retrieve'
            or self.action == 'me'
        ):
            return UserGetSerializer
        return super().get_serializer_class()

    @action(
        ['GET'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me',
        url_name='me'
    )
    def me(self, request):
        """Получить информацию о текущем пользователе."""
        serializer = UserGetSerializer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['PUT'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
        url_name='avatar'
    )
    def avatar(self, request, *args, **kwargs):
        """Обновить аватар пользователя."""
        serializer = AvatarSerializer(instance=request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request, *args, **kwargs):
        """Удалить аватар пользователя."""
        user = self.request.user
        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='subscriptions',
        url_name='subscriptions',
    )
    def subscriptions(self, request):
        """Получить список подписок пользователя."""
        user = request.user
        subscriptions = Subscription.objects.filter(subscriber=user)
        authors = [subscription.author for subscription in subscriptions]
        pages = self.paginate_queryset(authors)
        serializer = SubscriptionGetSerializer(
            pages, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['POST', 'DELETE'],
        detail=True
    )
    def subscribe(self, request, id):
        """Подписаться или отписаться от автора."""
        user = request.user
        author = get_object_or_404(User, id=id)

        if user == author:
            return Response(
                {"errors": "Вы не можете подписаться на себя."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == "POST":
            subscription, created = Subscription.objects.get_or_create(
                subscriber=user, author=author
            )
            if not created:
                return Response(
                    {"errors": "Вы уже подписаны на этого автора."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = SubscriptionPostSerializer(
                subscription, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            try:
                subscription = Subscription.objects.get(
                    subscriber=user, author=author
                )
            except Subscription.DoesNotExist:
                return Response(
                    {"errors": "Вы не подписаны на этого автора."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с тегами."""

    pagination_class = None
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с ингредиентами."""

    pagination_class = None
    permission_classes = (AllowAny,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами."""

    permission_classes = (
        IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly
    )
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.request.method in SAFE_METHODS:
            return RecipeGetSerializer
        return RecipePostSerializer

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='favorite',
        url_name='favorite',
    )
    def favorite(self, request, pk):
        """Добавляет или удаляет рецепт из избранного пользователя."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if Favorite.objects.filter(recipe=recipe, user=user).exists():
                return Response(
                    {'detail': f'{recipe.name} уже в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            favorite_entry = Favorite.objects.create(recipe=recipe, user=user)
            serializer = FavoriteSerializer(
                favorite_entry, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            favorite_entry = Favorite.objects.filter(
                recipe=recipe, user=user
            )
            if favorite_entry.exists():
                favorite_entry.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'detail': f'{recipe.name} удален из избранного.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
        url_name='shopping_cart',
    )
    def shopping_cart(self, request, pk):
        """Добавляет или удаляет рецепт из списка покупок пользователя."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if ShoppingCart.objects.filter(recipe=recipe, user=user).exists():
                return Response(
                    {'detail': f' {recipe.name} уже добавлен.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ShoppingCart.objects.create(recipe=recipe, user=user)
            serializer = ShoppingCartSerializer(
                recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            cart_item = ShoppingCart.objects.filter(recipe__id=pk, user=user)
            if cart_item.exists():
                cart_item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'detail': f'{recipe.name} удален из списка покупок.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """Возвращает список покупок в виде текстового файла."""
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shopping_carts__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(sum=Sum('amount'))
        )
        shopping_list = '\n'.join(
            f'{ingredient["ingredient__name"]} - {ingredient["sum"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            for ingredient in ingredients
        )
        return HttpResponse(shopping_list, content_type='text/plain')

    @action(
        methods=['GET'],
        detail=True,
        permission_classes=[AllowAny],
        url_path='get-link',
        url_name='get-link'
    )
    def get_short_link(self, request, pk):
        """Возвращает короткую ссылку на рецепт."""
        recipe = get_object_or_404(Recipe, pk=pk)
        rev_link = reverse('short_url', args=[recipe.pk])
        return Response(
            {'short-link': request.build_absolute_uri(rev_link)},
            status=status.HTTP_200_OK
        )


def short_url(request, short_link):
    """Редирект с короткой ссылки."""

    link = request.build_absolute_uri()
    recipe = get_object_or_404(Recipe, short_link=link)
    return redirect(
        'api:recipe-detail',
        pk=recipe.id
    )
