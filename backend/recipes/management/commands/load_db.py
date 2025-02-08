import os
from csv import reader

from django.core.management.base import BaseCommand

from foodgram_backend import settings
from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    """Загружает списки ингредиентов и тегов из CSV файлов в базу данных."""
    help = 'Загрузка данных из CSV-файлов в базу данных'

    def handle(self, *args, **options):
        """Чтение ingredients.csv и tags.csv и их загрузка в базу данных."""
        ingredients_file_path = os.path.join(
            settings.BASE_DIR, 'data', 'ingredients.csv'
        )
        with open(ingredients_file_path, encoding='utf-8') as csv_file:
            csv_reader = reader(csv_file)
            for row in csv_reader:
                Ingredient.objects.update_or_create(
                    name=row[0].strip(),
                    measurement_unit=row[1].strip()
                )
        self.stdout.write(self.style.SUCCESS('Список ингредиентов загружен!'))

        tags_file_path = os.path.join(
            settings.BASE_DIR, 'data', 'tags.csv'
        )
        with open(tags_file_path, encoding='utf-8') as csv_file:
            csv_reader = reader(csv_file)
            for row in csv_reader:
                Tag.objects.update_or_create(
                    name=row[0].strip(),
                    slug=row[1].strip()
                )
        self.stdout.write(self.style.SUCCESS('Список тегов загружен!'))
