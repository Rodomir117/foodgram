from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from foodgram_backend.constants import (
    AMOUNT_INGREDIENTS_MAX,
    AMOUNT_INGREDIENTS_MIN,
    COOKING_TIME_MAX,
    COOKING_TIME_MIN,
    TEXT_LENGTH_MAX,
    TEXT_LENGTH_MEDIUM,
    TEXT_LENGTH_MIN,
)
from users.models import User


class Recipe(models.Model):
    """Рецепт."""

    author = models.ForeignKey(
        User, verbose_name='Автор публикации', on_delete=models.CASCADE
    )
    ingredient = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        'Tag',
        verbose_name='Тег'
    )
    image = models.ImageField('Изображение', upload_to='recipes/images/')
    name = models.CharField('Название', max_length=TEXT_LENGTH_MAX)
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления в минутах',
        validators=[
            MaxValueValidator(COOKING_TIME_MAX),
            MinValueValidator(COOKING_TIME_MIN)
        ],
    )
    created_at = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )
    short_link = models.CharField(
        'Короткая ссылка',
        max_length=TEXT_LENGTH_MIN,
        blank=True,
        unique=True,
        null=True
    )

    class Meta:
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.name}. Автор: {self.author}'


class Ingredient(models.Model):
    """Ингредиент."""

    name = models.CharField('Название', max_length=TEXT_LENGTH_MEDIUM)
    measurement_unit = models.CharField(
        'Единица измерения', max_length=TEXT_LENGTH_MIN
    )

    class Meta:
        default_related_name = 'ingredients'
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}.'


class RecipeIngredient(models.Model):
    """Промежуточная модель связи рецепта c ингредиентами."""

    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,

    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=(
            MinValueValidator(
                AMOUNT_INGREDIENTS_MIN,
                f'Минимальное количство {AMOUNT_INGREDIENTS_MIN}'
            ),
            MaxValueValidator(
                AMOUNT_INGREDIENTS_MAX,
                f'Максимальное количство {AMOUNT_INGREDIENTS_MAX}'
            ),
        )
    )

    class Meta:
        default_related_name = 'recipe_ingredients'
        verbose_name = 'Ингридиенты рецепта'
        verbose_name_plural = 'Ингридиенты рецепта'
        ordering = ('ingredient',)

    def __str__(self):
        return f'Ингридиент {self.ingredient} в количестве {self.amount}.'


class Tag(models.Model):
    """Теги рецептов."""

    name = models.CharField(
        'Название', max_length=TEXT_LENGTH_MIN, unique=True
    )
    slug = models.SlugField(
        'Слаг', max_length=TEXT_LENGTH_MIN, unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class BaseFavoriteShoppingCart(models.Model):
    """Базовая модель для Избранного и Списка покупок."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        ordering = ('user',)


class Favorite(BaseFavoriteShoppingCart):
    """Рецепты в списке избранного."""

    class Meta:
        default_related_name = 'favorites'
        verbose_name = 'Рецепт в избранном'
        verbose_name_plural = 'Рецепты в избранном'
        constraints = [
            models.UniqueConstraint(
                name='favorite_unique',
                fields=['user', 'recipe'],
            )
        ]

    def __str__(self):
        return f'Рецепт {self.recipe} в избранном у {self.user}'


class ShoppingCart(BaseFavoriteShoppingCart):
    """Список покупок для рецепта."""

    class Meta:
        default_related_name = 'shopping_carts'
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                name='shopping_unique',
                fields=['user', 'recipe'],
            )
        ]

    def __str__(self):
        return f'Список покупок{self.user} для рецепта {self.recipe}'
