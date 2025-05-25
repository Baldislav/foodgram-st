# Foodgram platform 

**Foodgram** — это веб-платформа, где пользователи могут делиться собственными рецептами, сохранять понравившиеся рецепты других участников в избранное и подписываться на обновления любимых авторов. После регистрации открывается доступ к удобной функции «Список покупок» — она помогает формировать перечень ингредиентов, необходимых для приготовления выбранных блюд.

## Технологический стэк

- Python 3.10,
- Django,
- DRF (Django Rest Framework),
- PostgreSQL
- Docker,
- Docker Compose,
- Nginx,
- Djoser,

## Установка компонентов и их запуск

### 1. Клонирование репозитория

Клонируйте данный репозиторий.

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта со следующими данными:

```env
DJANGO_DEBUG=False
POSTGRES_DB=foodgram_db
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD='pass'
DATABASE_URL=postgresql://foodgram_user:pass@db:5432/foodgram_db
DB_HOST=db
DB_PORT=5432
```

### 3. Сборка и запуск Docker-образов

```sh
docker-compose down && docker-compose up --build
```

### 4. Выполните миграции, 
```sh
docker-compose exec backend python manage.py migrate
```
### 5. Загрузите ингредиенты, 
```sh
docker-compose exec backend python manage.py load_ingredients
```
### 6.соберите статику и создайте суперпользователя
```sh
docker-compose exec backend python manage.py collectstatic --noinput
docker-compose exec backend python manage.py createsuperuser
```

### 7. Основные ресурсы приложения

* **Главная страница приложения:** [http://localhost/](http://localhost/)
* **API-документация к проекту:** [http://localhost/api/docs/](http://localhost/api/docs/)
* **Админ-панель Django:** [http://localhost/admin/](http://localhost/admin/)

### 8. Тестирование API

- Примеры запросов и тесты доступны и производятся в коллекции Postman:
  `postman_collection/foodgram.postman_collection.json`

## Контакты

Автор: Сысоев Кирилл Вячеславович

---
