from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import Subscription, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Административное представление кастомных пользователей."""

    list_display = (
        'id',
        'username',
        'first_name',
        'last_name',
        'email',
        'get_subscribers',
        'get_recipes',
        'is_staff'
    )
    list_display_links = ('username',)
    list_filter = ('is_active', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    @admin.display(description='Сколько подписчиков')
    def get_subscribers(self, object):
        return object.authors.count()

    @admin.display(description='Сколько рецептов')
    def get_recipes(self, object):
        return object.recipes.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Административное представление подписок пользователей."""

    list_display = ('subscriber', 'author')
    search_fields = ('subscriber__username', 'author__username')

    def get_queryset(self, request):
        """Возвращает оптимизированный queryset для списка подписок."""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('subscriber', 'author')
        return queryset


admin.site.empty_value_display = '-пусто-'
