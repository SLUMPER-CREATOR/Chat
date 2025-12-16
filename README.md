# 💬 Django Real-Time Chat Application

Современное веб-приложение для общения в реальном времени, построенное на Django и WebSocket технологиях.

![Python](https://img.shields.io/badge/Python-3.13-blue)
![Django](https://img.shields.io/badge/Django-6.0-green)
![WebSocket](https://img.shields.io/badge/WebSocket-Channels-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🚀 Возможности

### 💬 **Чаты**
- **Общий чат** - Публичное общение всех пользователей
- **Личные сообщения** - Приватные беседы один на один
- **Групповые чаты** - Создание и управление группами

### 👤 **Пользователи**
- **Регистрация и аутентификация** - Безопасная система входа
- **Профили пользователей** - Аватарки, биография, статистика
- **Система лайков** - Возможность лайкать других пользователей

### ⚡ **Реальное время**
- **WebSocket соединения** - Мгновенная доставка сообщений
- **Онлайн статус** - Отображение активных пользователей
- **Уведомления** - Звуковые и визуальные уведомления

### 🎨 **Интерфейс**
- **Адаптивный дизайн** - Работает на всех устройствах
- **Современный UI** - TailwindCSS для красивого интерфейса
- **Темная/светлая тема** - Удобство использования

## 📸 Скриншоты

### Общий чат
![Общий чат](docs/screenshots/main-chat.png)

### Личные сообщения
![Личные сообщения](docs/screenshots/private-chat.png)

### Групповые чаты
![Групповые чаты](docs/screenshots/group-chat.png)

### Профиль пользователя
![Профиль](docs/screenshots/profile.png)

## 🛠️ Технологический стек

- **Backend:** Django 6.0, Django Channels 4.3.2
- **WebSocket:** Daphne, Autobahn, Twisted
- **Database:** SQLite (легко заменить на PostgreSQL/MySQL)
- **Frontend:** HTML5, TailwindCSS, Vanilla JavaScript
- **Images:** Pillow для обработки аватарок
- **Real-time:** WebSocket для мгновенных сообщений

## 📦 Установка и запуск

### Требования
- Python 3.8+
- pip
- Git

### 1. Клонирование репозитория
```bash
git clone https://github.com/yourusername/django-chat.git
cd django-chat
```

### 2. Создание виртуального окружения
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка базы данных
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Создание суперпользователя
```bash
python manage.py createsuperuser
```

### 6. Запуск сервера
```bash
python manage.py runserver
```

Откройте браузер и перейдите по адресу: `http://127.0.0.1:8000/`

## 🔧 Конфигурация

### Настройки Django
Основные настройки находятся в `chat_site/settings.py`:

```python
# Для продакшена измените:
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']

# Настройте базу данных:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### WebSocket настройки
Channel layers настроены для разработки. Для продакшена рекомендуется Redis:

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
```

## 📁 Структура проекта

```
django-chat/
├── chat/                   # Основное приложение
│   ├── models.py          # Модели данных
│   ├── views.py           # Представления
│   ├── consumers.py       # WebSocket consumers
│   ├── routing.py         # WebSocket маршруты
│   └── urls.py            # URL маршруты
├── chat_site/             # Настройки проекта
│   ├── settings.py        # Конфигурация Django
│   ├── asgi.py           # ASGI конфигурация
│   └── urls.py           # Главные URL
├── templates/             # HTML шаблоны
│   ├── chat/             # Шаблоны чата
│   └── registration/     # Шаблоны аутентификации
├── static/               # Статические файлы
├── media/                # Загруженные файлы
├── requirements.txt      # Python зависимости
└── manage.py            # Django управление
```

## 🎯 Основные модели

### User Profile
```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    bio = models.TextField(max_length=500, blank=True)
```

### Messages
```python
class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
```

### Groups
```python
class Group(models.Model):
    name = models.CharField(max_length=100)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    members = models.ManyToManyField(User, through='GroupMembership')
    is_private = models.BooleanField(default=False)
```

## 🔌 API Endpoints

### WebSocket
- `ws://localhost:8000/ws/chat/` - Общий чат
- `ws://localhost:8000/ws/private/{chat_id}/` - Личные сообщения
- `ws://localhost:8000/ws/group/{group_id}/` - Групповые чаты

### HTTP
- `/chat/` - Главная страница чата
- `/chat/private/` - Список личных чатов
- `/chat/groups/` - Список групп
- `/chat/profile/` - Профиль пользователя
- `/chat/user/{id}/` - Просмотр профиля пользователя

## 🚀 Деплой

### Heroku
1. Создайте `Procfile`:
```
web: daphne chat_site.asgi:application --port $PORT --bind 0.0.0.0
```

2. Добавьте переменные окружения:
```bash
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=your-secret-key
```

### Docker
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["daphne", "chat_site.asgi:application", "--port", "8000", "--bind", "0.0.0.0"]
```

## 🤝 Участие в разработке

1. Fork репозитория
2. Создайте ветку для новой функции (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📝 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 👨‍💻 Автор

**Ваше имя**
- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

## 🙏 Благодарности

- Django команде за отличный фреймворк
- Django Channels за WebSocket поддержку
- TailwindCSS за красивый UI
- Всем контрибьюторам проекта

## 📊 Статистика

![GitHub stars](https://img.shields.io/github/stars/yourusername/django-chat)
![GitHub forks](https://img.shields.io/github/forks/yourusername/django-chat)
![GitHub issues](https://img.shields.io/github/issues/yourusername/django-chat)

---

⭐ **Поставьте звезду, если проект вам понравился!**