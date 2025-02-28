import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers

from foodgram_backend.constants import IMAGE
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription, User


class Base64ImageField(serializers.ImageField):
    """Изображения в формате base64 сохраняет как файлы."""

    def __init__(self, *args, **kwargs):
        self.file_prefix = kwargs.pop('file_prefix', 'file')
        self.max_filename_length = kwargs.pop('max_filename_length', IMAGE)
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            filename = f'{self.file_prefix}_{uuid.uuid4()}.{ext}'
            data = ContentFile(base64.b64decode(imgstr), name=filename)
        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для модели пользователя с полем аватара."""

    avatar = Base64ImageField(allow_null=True, file_prefix='avatar')

    class Meta:
        model = User
        fields = ('avatar',)


class UserPostSerializer(serializers.ModelSerializer):
    """Сериализатор создания нового пользователя."""

    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )

    def create(self, validated_data):
        """Создает нового пользователя с валидированными данными."""
        return User.objects.create_user(**validated_data)


class UserGetSerializer(serializers.ModelSerializer):
    """Сериализатор информации о пользователе."""

    avatar = Base64ImageField(allow_null=True, required=False)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, author):
        """Проверка подписки пользователей."""
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and user.subscribers.filter(author=author).exists()
        )


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор инргедиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientPostSerializer(serializers.ModelSerializer):
    """Сериализатор создания связи рецепта c ингредиентами."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def validate_amount(self, value):
        if not value:
            serializers.ValidationError('Количество не может быть пустым.')
        return value


class RecipeIngredientGetSerializer(serializers.ModelSerializer):
    """Сериализатор получения связи рецепта c ингредиентами."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class RecipePostSerializer(serializers.ModelSerializer):
    """Сериализатор создания рецепта."""

    author = serializers.SlugRelatedField(
        slug_field='username', read_only=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = RecipeIngredientPostSerializer(
        many=True, source='recipe_ingredients'
    )
    image = Base64ImageField(required=True, file_prefix='recipe')

    class Meta:
        model = Recipe
        fields = (
            'author',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )
        read_only_fields = ('author',)

    def validate(self, value):
        """Валидация ингредиентов и тегов."""
        ingredients = value.get('recipe_ingredients')
        tags = value.get('tags')
        if not ingredients:
            raise serializers.ValidationError(
                'Отсутствует обязательное поле ингредиенты'
            )
        if not tags:
            raise serializers.ValidationError(
                'Отсутствует обязательное поле теги'
            )
        ingredients_id = [
            ingredient.get('ingredient').id for ingredient in ingredients
        ]
        if len(set(ingredients_id)) != len(ingredients):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальными.'
            )
        if len(set(tags)) != len(tags):
            raise serializers.ValidationError('Теги должны быть уникальными.')
        return value

    def add_ingredients(self, model, recipe, ingredients):
        """Добавляет ингредиенты к рецепту."""
        model.objects.bulk_create(
            (
                model(
                    recipe=recipe,
                    ingredient=ingredient['ingredient'],
                    amount=ingredient['amount']
                )
                for ingredient in ingredients
            )
        )

    def _update_tags_and_ingredients(self, recipe, tags, ingredients):
        """Обновляет теги и ингредиенты для рецепта."""
        recipe.tags.set(tags)
        recipe.recipe_ingredients.all().delete()
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(recipe=recipe, **ingredient)
                for ingredient in ingredients
            ]
        )

    def create(self, validated_data):
        """Создает новый рецепт с привязкой тегов и ингредиентов."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        validated_data.pop('author', None)
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        self._update_tags_and_ingredients(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновляет рецепт с возможностью изменить теги и ингредиенты."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        self._update_tags_and_ingredients(instance, tags, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Возвращает данные рецепта через RecipeGetSerializer."""
        return RecipeGetSerializer(
            instance, context={'request': self.context.get('request')}
        ).data


class RecipeGetSerializer(serializers.ModelSerializer):
    """Сериализатор получения информации рецепта."""

    author = UserGetSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientGetSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    image = Base64ImageField(required=True, allow_null=False)
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def check_user_status(self, obj, model_class):
        """Проверяет статус пользователя."""
        user = self.context.get('request')
        return (
            user and user.user.is_authenticated
            and model_class.objects.filter(recipe=obj, user=user.user).exists()
        )

    def get_is_favorited(self, obj):
        """Проверяет, в избранном ли рецепт."""
        return self.check_user_status(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, в корзине ли рецепт."""
        return self.check_user_status(obj, ShoppingCart)


class MiniRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор получения краткой информации рецепта."""

    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор добавления рецептов в избранное."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        """Проверяет, добавлен ли рецепт в избранное."""
        if Favorite.objects.filter(**data).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное.'
            )
        return data

    def to_representation(self, instance):
        """Возвращает данные рецепта в избранном через MiniRecipeSerializer."""
        return MiniRecipeSerializer(
            instance.recipe
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор добавления рецептов в список покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        """Проверяет, добавлен ли рецепт список покупок."""
        if ShoppingCart.objects.filter(**data).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в список покупок.'
            )
        return data

    def to_representation(self, instance):
        """Возвращает данные рецепта в через MiniRecipeSerializer."""
        return MiniRecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class SubscriptionPostSerializer(serializers.ModelSerializer):
    """Сериализатор создания подписки."""

    class Meta:
        fields = ('subscriber', 'author')
        model = Subscription

    def validate_author(self, value):
        """Проверка, что пользователь не подписывается на себя."""
        user = self.context['request'].user
        if user == value:
            raise serializers.ValidationError('Нельзя подписаться на себя')
        if Subscription.objects.filter(subscriber=user, author=value).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя'
            )
        return value

    def to_representation(self, instance):
        """Возвращает данные о подписке в формате SubscriptionGetSerializer."""
        request = self.context.get('request')
        return SubscriptionGetSerializer(
            instance.author, context={'request': request}
        ).data


class SubscriptionGetSerializer(serializers.ModelSerializer):
    """Сериализатор для получения подписок пользователей."""

    recipes = serializers.SerializerMethodField(method_name='get_recipes')
    recipes_count = serializers.IntegerField(default=0)
    is_subscribed = serializers.BooleanField(default=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_recipes(self, author):
        """Получает список рецептов пользователя."""
        recipes = author.recipes.all()
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]
        return MiniRecipeSerializer(
            recipes,
            many=True,
            context={'request': request}
        ).data
