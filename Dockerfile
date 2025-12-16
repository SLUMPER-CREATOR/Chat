# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем директории для статических и медиа файлов
RUN mkdir -p staticfiles media

# Собираем статические файлы
RUN python manage.py collectstatic --noinput

# Применяем миграции
RUN python manage.py migrate

# Открываем порт
EXPOSE 8000

# Команда запуска
CMD ["daphne", "chat_site.asgi:application", "--port", "8000", "--bind", "0.0.0.0"]