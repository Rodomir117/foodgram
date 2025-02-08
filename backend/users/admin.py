from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import Subscription, User


@admin.register(User)
class UserAdmin(UserAdmin):
    """Административное представление пользователей."""

    list_display = (
        'id',
        'username',
        'first_name',
        'last_name',
        'email',
        'is_staff'
    )
    list_editable = ('is_staff',)
    search_fields = ('username', 'first_name', 'last_name', 'email')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Административное представление подписок пользователей."""

    list_display = ('subscriber', 'author')
    search_fields = ('subscriber', 'author')


admin.site.empty_value_display = '-пусто-'
