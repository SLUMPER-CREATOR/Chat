# 🚀 Руководство по развертыванию

Это руководство поможет вам развернуть Django Chat Application на различных платформах.

## 📋 Содержание

- [Подготовка к развертыванию](#подготовка-к-развертыванию)
- [Heroku](#heroku)
- [DigitalOcean](#digitalocean)
- [AWS](#aws)
- [Docker](#docker)
- [VPS/Dedicated Server](#vpsdedicated-server)

## 🔧 Подготовка к развертыванию

### 1. Настройки для продакшена

Создайте файл `chat_site/production_settings.py`:

```python
from .settings import *
import os

# Безопасность
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# База данных
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Redis для Channel Layers
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(os.environ.get('REDIS_URL', 'redis://localhost:6379'))],
        },
    },
}

# Статические файлы
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Медиа файлы (для продакшена лучше использовать S3)
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Безопасность
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Логирование
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 2. Обновите requirements.txt

```txt
# Добавьте для продакшена
psycopg2-binary==2.9.7
channels-redis==4.1.0
whitenoise==6.5.0
gunicorn==21.2.0
```

## 🟣 Heroku

### Подготовка

1. **Установите Heroku CLI:**
   ```bash
   # Windows
   winget install Heroku.CLI
   
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Linux
   curl https://cli-assets.heroku.com/install.sh | sh
   ```

2. **Войдите в Heroku:**
   ```bash
   heroku login
   ```

### Развертывание

1. **Создайте приложение:**
   ```bash
   heroku create your-chat-app-name
   ```

2. **Добавьте аддоны:**
   ```bash
   # PostgreSQL
   heroku addons:create heroku-postgresql:mini
   
   # Redis
   heroku addons:create heroku-redis:mini
   ```

3. **Настройте переменные окружения:**
   ```bash
   heroku config:set SECRET_KEY="your-secret-key-here"
   heroku config:set DJANGO_SETTINGS_MODULE="chat_site.production_settings"
   ```

4. **Разверните приложение:**
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

5. **Примените миграции:**
   ```bash
   heroku run python manage.py migrate
   heroku run python manage.py createsuperuser
   ```

## 🌊 DigitalOcean

### App Platform

1. **Создайте файл `.do/app.yaml`:**
   ```yaml
   name: django-chat
   services:
   - name: web
     source_dir: /
     github:
       repo: yourusername/django-chat
       branch: main
     run_command: daphne chat_site.asgi:application --port $PORT --bind 0.0.0.0
     environment_slug: python
     instance_count: 1
     instance_size_slug: basic-xxs
     envs:
     - key: SECRET_KEY
       value: your-secret-key
     - key: DJANGO_SETTINGS_MODULE
       value: chat_site.production_settings
   
   databases:
   - name: db
     engine: PG
     version: "13"
     size_slug: db-s-1vcpu-1gb
   
   static_sites:
   - name: static
     source_dir: /staticfiles
   ```

### Droplet (VPS)

1. **Создайте Droplet с Ubuntu 22.04**

2. **Подключитесь по SSH:**
   ```bash
   ssh root@your-droplet-ip
   ```

3. **Установите зависимости:**
   ```bash
   apt update && apt upgrade -y
   apt install python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server
   ```

4. **Настройте PostgreSQL:**
   ```bash
   sudo -u postgres createuser --interactive
   sudo -u postgres createdb django_chat
   ```

5. **Клонируйте и настройте проект:**
   ```bash
   cd /var/www
   git clone https://github.com/yourusername/django-chat.git
   cd django-chat
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

6. **Настройте Nginx:**
   ```nginx
   # /etc/nginx/sites-available/django-chat
   server {
       listen 80;
       server_name yourdomain.com;
       
       location /static/ {
           alias /var/www/django-chat/staticfiles/;
       }
       
       location /media/ {
           alias /var/www/django-chat/media/;
       }
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

7. **Создайте systemd сервис:**
   ```ini
   # /etc/systemd/system/django-chat.service
   [Unit]
   Description=Django Chat Application
   After=network.target
   
   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/var/www/django-chat
   Environment=PATH=/var/www/django-chat/venv/bin
   ExecStart=/var/www/django-chat/venv/bin/daphne chat_site.asgi:application --port 8000 --bind 127.0.0.1
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

## ☁️ AWS

### Elastic Beanstalk

1. **Установите EB CLI:**
   ```bash
   pip install awsebcli
   ```

2. **Инициализируйте проект:**
   ```bash
   eb init django-chat
   ```

3. **Создайте окружение:**
   ```bash
   eb create production
   ```

4. **Настройте переменные окружения в AWS Console**

### EC2 + RDS + ElastiCache

1. **Создайте EC2 инстанс**
2. **Настройте RDS PostgreSQL**
3. **Создайте ElastiCache Redis**
4. **Настройте Load Balancer**
5. **Используйте S3 для медиа файлов**

## 🐳 Docker

### Docker Compose для продакшена

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  web:
    build: .
    command: daphne chat_site.asgi:application --port 8000 --bind 0.0.0.0
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    expose:
      - 8000
    env_file:
      - .env.prod
    depends_on:
      - db
      - redis

  nginx:
    build: ./nginx
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - 80:80
      - 443:443
    depends_on:
      - web

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    env_file:
      - .env.prod.db

  redis:
    image: redis:7-alpine

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### Запуск в продакшене

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 🖥️ VPS/Dedicated Server

### Полная настройка Ubuntu сервера

1. **Обновление системы:**
   ```bash
   apt update && apt upgrade -y
   ```

2. **Установка зависимостей:**
   ```bash
   apt install python3 python3-pip python3-venv nginx postgresql redis-server supervisor certbot python3-certbot-nginx
   ```

3. **Настройка файрвола:**
   ```bash
   ufw allow OpenSSH
   ufw allow 'Nginx Full'
   ufw enable
   ```

4. **SSL сертификат:**
   ```bash
   certbot --nginx -d yourdomain.com
   ```

5. **Supervisor конфигурация:**
   ```ini
   # /etc/supervisor/conf.d/django-chat.conf
   [program:django-chat]
   command=/var/www/django-chat/venv/bin/daphne chat_site.asgi:application --port 8000
   directory=/var/www/django-chat
   user=www-data
   autostart=true
   autorestart=true
   redirect_stderr=true
   stdout_logfile=/var/log/django-chat.log
   ```

## 📊 Мониторинг и логирование

### Настройка логирования

```python
# В production_settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django-chat/django.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file'],
    },
}
```

### Мониторинг с помощью Sentry

```bash
pip install sentry-sdk[django]
```

```python
# В settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="YOUR_SENTRY_DSN",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)
```

## 🔒 Безопасность

### Чеклист безопасности

- [ ] DEBUG = False
- [ ] Сильный SECRET_KEY
- [ ] HTTPS настроен
- [ ] Файрвол настроен
- [ ] База данных защищена
- [ ] Регулярные бэкапы
- [ ] Мониторинг логов
- [ ] Обновления безопасности

### Автоматические бэкапы

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump django_chat > /backups/db_backup_$DATE.sql
tar -czf /backups/media_backup_$DATE.tar.gz /var/www/django-chat/media/
```

## 📈 Оптимизация производительности

### Настройки базы данных

```python
# Для PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'MAX_CONNS': 20,
            'OPTIONS': {
                'MAX_CONNS': 20,
            }
        },
    }
}
```

### Кэширование

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

---

**Удачного развертывания! 🚀**