from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Предоставляет методы для создания пользователей и суперпользователей."""

    def create_user(
        self,
        email,
        username,
        first_name,
        last_name,
        password
    ):
        """Создает и возвращает пользователя."""
        if not email:
            raise ValueError('Необходимо указать электронную почту')
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(
        self,
        email,
        username,
        first_name,
        last_name,
        password
    ):
        """Создает и возвращает суперпользователя."""
        user = self.create_user(
            email,
            username,
            first_name,
            last_name,
            password
        )
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user
