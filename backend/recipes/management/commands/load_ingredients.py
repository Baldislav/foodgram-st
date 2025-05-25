import json
import os
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.conf import settings
from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Загружает ингредиенты из JSON файла в базу данных"

    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR, "data", "ingredients.json")
        self.stdout.write(self.style.SUCCESS(f"Ищем файл по пути: {file_path}"))

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"Файл {file_path} не найден."))
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                ingredients_data = json.load(f)
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f"Ошибка декодирования JSON в файле {file_path}."))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Произошла ошибка при чтении файла: {e}"))
            return

        count_added = 0
        count_skipped = 0

        for item in ingredients_data:
            try:
                name = item["name"].strip().lower()
                measurement_unit = item["measurement_unit"].strip().lower()

                ingredient, created = Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit,
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f"Добавлен ингредиент: {ingredient.name}"))
                    count_added += 1
                else:
                    self.stdout.write(self.style.WARNING(f"Ингредиент уже существует (пропущен): {ingredient.name}"))
                    count_skipped += 1

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f'Ошибка целостности для {item.get("name", "(нет имени")}: {e}'))
                count_skipped += 1
            except KeyError:
                self.stdout.write(self.style.ERROR(f'Отсутствует "name" или "measurement_unit" в записи: {item}'))
                count_skipped += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Не удалось добавить ингредиент {item.get("name", "(нет имени)")} : {e}'))
                count_skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Загрузка ингредиентов завершена. Добавлено: {count_added}, "
                f"Пропущено (уже существовали или ошибка): {count_skipped}"
            )
        )
