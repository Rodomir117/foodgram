from io import BytesIO

from django.db.models import Count, Exists, OuterRef, Sum
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
from foodgram_backend.constants import ZERO
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

    queryset = User.objects.annotate(recipes_count=Count('recipes'))
    serializer_class = UserPostSerializer
    pagination_class = CustomPagination

    def get_serializer_class(self):
        """Возвращаеткласс сериализатора в зависимости от действия."""
        if self.action in ['list', 'retrieve', 'me']:
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
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['POST', 'DELETE'],
        detail=True
    )
    def subscribe(self, request, id):
        """Подписаться или отписаться от автора."""
        user = request.user
        if request.method == 'POST':
            author = get_object_or_404(User, id=id)
            serializer = SubscriptionPostSerializer(
                data={'subscriber': user.id, 'author': author.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            subscription = serializer.save()
            return Response(
                SubscriptionPostSerializer(
                    subscription,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            deleted_count, _ = Subscription.objects.filter(
                subscriber=user, author_id=id
            ).delete()
            if deleted_count == ZERO:
                return Response(
                    {'errors': 'Вы не подписаны на этого автора.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
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

    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    queryset = (
        Recipe.objects
        .select_related('author')
        .prefetch_related('tags', 'recipe_ingredients__ingredient')
    )
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        """Сохраняет рецепт с указанием автора."""
        serializer.save(author=self.request.user)

    def handle_favorite_or_cart(
        self,
        request,
        pk,
        model,
        serializer_class,
        already_exists_message,
    ):
        """Добавляет/удаляет рецепты в избранное или корзину пользователя."""
        user = request.user
        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, id=pk)
            if model.objects.filter(recipe=recipe, user=user).exists():
                return Response(
                    {'detail': already_exists_message.format(recipe.name)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = serializer_class(
                data={'recipe': recipe.id, 'user': user.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            deleted_count, _ = model.objects.filter(
                recipe__id=pk, user=user
            ).delete()
            if deleted_count:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'detail': 'Рецепт не существует'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='favorite',
        url_name='favorite',
    )
    def favorite(self, request, pk):
        """Добавляет или удаляет рецепт из избранного пользователя."""
        return self.handle_favorite_or_cart(
            request=request,
            pk=pk,
            model=Favorite,
            serializer_class=FavoriteSerializer,
            already_exists_message='{} уже в избранном.'
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
        return self.handle_favorite_or_cart(
            request=request,
            pk=pk,
            model=ShoppingCart,
            serializer_class=ShoppingCartSerializer,
            already_exists_message='{} уже добавлен.'
        )

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.request.method in SAFE_METHODS:
            return RecipeGetSerializer
        return RecipePostSerializer

    def get_queryset(self):
        """Возвращает набор запросов рецептов с аннотациями."""
        user = self.request.user
        queryset = (
            Recipe.objects
            .select_related('author')
            .prefetch_related('tags', 'recipe_ingredients')
        )
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(recipe=OuterRef('pk'), user=user)
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        recipe=OuterRef('pk'), user=user
                    )
                ),
            )
        return queryset

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
                recipe__shopping_carts__user=request.user
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(sum=Sum('amount'))
        )
        buffer = self.generate_shopping_list(ingredients)
        return HttpResponse(buffer, content_type='text/plain')

    def generate_shopping_list(self, ingredients):
        """Создает список покупок в виде буфера BytesIO."""
        shopping_list = '\n'.join(
            f'{ingredient["ingredient__name"]} - {ingredient["sum"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            for ingredient in ingredients
        )
        buffer = BytesIO()
        buffer.write(shopping_list.encode('utf-8'))
        buffer.seek(0)
        return buffer

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
