# 📬 Сервис рассылок

Веб-приложение на Django для управления **email-рассылками** клиентам. Позволяет создавать клиентов, шаблоны писем и рассылки, отслеживать статистику отправок, разграничивать права доступа между пользователями и менеджерами.

Курсовая работа по курсу «Разработка веб-приложений на Django».

## 🎯 Возможности

### Управление данными
- **Клиенты** — добавление, редактирование, удаление получателей
- **Сообщения** — шаблоны писем (тема + тело)
- **Рассылки** — расписание + привязка сообщения и получателей
- **Логи попыток** — история успешных и неуспешных отправок

### Отправка рассылок
- **Вручную** — кнопка на странице рассылки
- **Через CLI** — management-команда `send_mailing`
- **По расписанию** — автоматически через `django-apscheduler`

### Пользователи и роли
- **Регистрация** с подтверждением email
- **Вход/выход** по email и паролю
- **Восстановление пароля** по email
- **Роли:**
  - **Пользователь** — управляет только своими клиентами и рассылками
  - **Менеджер** — видит всё, блокирует пользователей, отключает рассылки

### Статистика
- **Главная** — общее количество рассылок / активные / уникальные получатели
- **Страница статистики** — успешные и неуспешные попытки по каждой рассылке

### Производительность
- **Серверное кеширование** — Redis (счётчики главной, агрегаты статистики)
- **Клиентское кеширование** — HTTP-заголовки `Cache-Control`

### Наблюдаемость
- **Логирование** — события и ошибки в `logs/app.log` и `logs/errors.log`
- **Middleware** — отлов необработанных исключений (5xx)

## 🛠 Стек технологий

- **Python** 3.14
- **Django** 6.1
- **SQLite** — БД (по умолчанию, для разработки)
- **Redis** — кеш-бэкенд
- **django-apscheduler** — фоновые задачи
- **itsdangerous** — токены подтверждения email
- **Pillow** — обработка изображений
- **Poetry** — управление зависимостями
- **Black, isort, flake8** — линтеры и форматирование

## 🚀 Установка и запуск

### 1. Клонирование

```bash
git clone git@github.com:alexcherch/Coursework_3.git
cd Coursework_3
```

### 2. Установка зависимостей

```bash
poetry install --no-root --with lint
```

> `--no-root` — проект является Django-приложением, а не библиотекой.
> `--with lint` — дополнительно установить линтеры (black, isort, flake8).

### 3. Настройка переменных окружения

Скопируй пример и заполни своими значениями:

```bash
cp .env.sample .env
```

Открой `.env` и укажи:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True

# Redis (для серверного кеша)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Email
# По умолчанию письма выводятся в терминал (console backend).
# Для реальной отправки через Yandex SMTP — укажи SMTP-настройки:
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.yandex.ru
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=your@yandex.ru
EMAIL_HOST_PASSWORD=app_password
DEFAULT_FROM_EMAIL=your@yandex.ru
```

> Для **простого локального запуска** достаточно указать только `SECRET_KEY`, `DEBUG` и `REDIS_*`. Остальные настройки имеют разумные дефолты (email уйдёт в консоль).

### 4. Redis

**macOS (Homebrew):**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
```

Проверка:
```bash
redis-cli ping   # должно быть PONG
```

### 5. Миграции

```bash
poetry run python manage.py migrate
```

### 6. Создание групп пользователей

```bash
poetry run python manage.py create_groups
```

Создаёт группу **«Менеджер»**.

### 7. Суперпользователь

```bash
poetry run python manage.py createsuperuser
```

### 8. Запуск сервера

```bash
poetry run python manage.py runserver
```

Открой http://127.0.0.1:8000/

## ⏰ Планировщик задач (APScheduler)

Для **автоматической отправки** рассылок по расписанию запусти **отдельным процессом**:

```bash
poetry run python manage.py runapscheduler
```

Задача `send_scheduled_mailings` **каждые 30 секунд**:
- Ищет рассылки, попадающие в окно `[start_time, end_time]`
- Пропускает **уже отправленные** (у которых есть успешные попытки)
- Отправляет письма + создаёт `MailingAttempt` (batch через `bulk_create`)

> Остановка — **Ctrl+C**.

## 🖥 Отправка рассылок вручную

### Через UI

На странице рассылки — кнопка **«🚀 Запустить рассылку сейчас»**.

### Через CLI

```bash
# Конкретная рассылка по id
poetry run python manage.py send_mailing --id 5

# Все активные рассылки (попадающие в окно)
poetry run python manage.py send_mailing --all
```

## 🎨 Качество кода

```bash
poetry run black .      # форматирование
poetry run isort .      # сортировка импортов
poetry run flake8 .     # проверка стиля
```

**Длина строки** — 119 символов.
**isort** использует `profile = "black"` для согласованности.

## 📁 Структура проекта

```
Coursework_3/
├── config/                  # Настройки Django
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── mailing/                 # Основное приложение
│   ├── models.py           # Client, Message, Mailing, MailingAttempt
│   ├── views.py            # CBV + index + statistics
│   ├── services.py         # send_mailing (бизнес-логика отправки)
│   ├── forms.py
│   ├── admin.py
│   ├── middleware.py       # Cache-Control + логирование ошибок
│   ├── management/commands/
│   │   ├── send_mailing.py       # CLI отправка
│   │   └── runapscheduler.py     # Планировщик
│   └── templates/mailing/
│       ├── base.html
│       ├── index.html
│       ├── statistics.html
│       ├── client_*.html / message_*.html / mailing_*.html
│       └── user_list.html
├── users/                   # Кастомный пользователь
│   ├── models.py           # User(AbstractUser) с email-логином
│   ├── views.py            # Регистрация, вход, выход, подтверждение email
│   ├── forms.py
│   ├── mixins.py           # OwnerOnlyMixin, ManagerRequiredMixin, ...
│   ├── utils.py            # Токены через itsdangerous
│   ├── templatetags/role_tags.py
│   ├── management/commands/create_groups.py
│   └── templates/users/
│       ├── register.html / login.html
│       ├── email_sent.html / email_confirm_invalid.html
│       └── password_reset*.html
├── logs/                    # Логи (в .gitignore)
├── media/                   # Медиа (в .gitignore)
├── .env.sample
├── .flake8
├── .gitignore
├── manage.py
├── poetry.lock
├── pyproject.toml
└── README.md
```

## 🧪 Сценарии тестирования

### Обычный пользователь
1. Регистрация → подтверждение email
2. Вход
3. Создание клиентов и рассылок → видит **только свои**
4. Отправка своей рассылки → попытки в логах
5. Статистика → **своя**
6. Попытка открыть чужое → **403** / редирект

### Менеджер
1. Назначить группу **«Менеджер»** через админку
2. Видит **все** рассылки, клиентов, сообщения
3. Может **блокировать** пользователей и **отключать** рассылки
4. Статистика → **по всем**

### Суперпользователь
- Видит всё, может всё

## 📄 Лицензия

Учебный проект.

---

**Автор:** alexcherch (alexcherch0@gmail.com)
