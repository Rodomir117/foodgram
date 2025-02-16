from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator
from django.db import models

from foodgram_backend.constants import TEXT_LENGTH_MAX, TEXT_LENGTH_MEDIUM
from users.manager import UserManager


class User(AbstractUser):
    """Кастомный пользователь системы."""

    first_name = models.CharField(
        'Имя',
        max_length=TEXT_LENGTH_MEDIUM,
        validators=[
            RegexValidator(
                regex=r'^[А-Яа-яЁёA-Za-z]+$',
                message='Поле должно содержать только буквы',
                code='invalid_name',
            ),
        ],
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=TEXT_LENGTH_MEDIUM,
        validators=[
            RegexValidator(
                regex=r'^[А-Яа-яЁёA-Za-z]+$',
                message='Поле должно содержать только буквы',
                code='invalid_name',
            ),
        ],
    )
    username = models.CharField(
        'Никнейм',
        max_length=TEXT_LENGTH_MEDIUM,
        unique=True,
        error_messages={
            'unique': 'Никнейм занят.',
        },
        validators=[UnicodeUsernameValidator()]
    )
    email = models.EmailField(
        'Электронная почта',
        max_length=TEXT_LENGTH_MAX,
        unique=True
    )
    avatar = models.ImageField('Аватар', upload_to='users/')

    REQUIRED_FIELDS = ['first_name', 'last_name', 'username', 'password']
    USERNAME_FIELD = 'email'

    objects = UserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Подписка на автора."""

    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='subscribers',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='authors',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('subscriber',)
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'author'],
                name='unique_subscriber_author'
            ),
            models.CheckConstraint(
                name='check_subscriber_author',
                check=~models.Q(subscriber=models.F('author')),
            )
        ]

    def __str__(self):
        return f'{self.subscriber} подписан на {self.author}'
