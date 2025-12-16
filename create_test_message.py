#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_site.settings')
django.setup()

from django.contrib.auth.models import User
from chat.models import Message, UserProfile

# Создать тестового пользователя если его нет
user, created = User.objects.get_or_create(
    username='testuser',
    defaults={'email': 'test@example.com'}
)

if created:
    user.set_password('testpass123')
    user.save()
    print(f"Создан пользователь: {user.username}")

# Создать профиль для пользователя
profile, created = UserProfile.objects.get_or_create(user=user)
if created:
    print(f"Создан профиль для: {user.username}")

# Создать тестовое сообщение
message = Message.objects.create(
    user=user,
    content="Привет! Это тестовое сообщение для проверки чата."
)
print(f"Создано сообщение: {message.content}")

print("Готово! Теперь в чате должно быть видно сообщение.")