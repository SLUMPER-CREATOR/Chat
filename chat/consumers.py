import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from .models import Message, OnlineUser

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info(f"WebSocket подключение от пользователя: {self.scope['user']}")
        
        # Временно разрешим анонимным пользователям для тестирования
        if self.scope["user"].is_anonymous:
            logger.warning("Анонимный пользователь подключается (тестовый режим)")
            self.user = None
        else:
            self.user = self.scope["user"]

        self.room_group_name = 'chat_general'

        # Добавить пользователя в онлайн (только если авторизован)
        if self.user:
            await self.add_online_user(self.user)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        username = self.user.username if self.user else "Анонимный"
        logger.info(f"WebSocket соединение принято для пользователя: {username}")

        # Отправить обновление списка онлайн-пользователей всем
        if self.user:
            await self.send_online_users()

    async def disconnect(self, close_code):
        # Удалить пользователя из онлайн (только если авторизован)
        if self.user:
            await self.remove_online_user(self.user)
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        # Обновить список онлайн для остальных
        if self.user:
            await self.send_online_users()

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        username = data['username']

        await self.save_message(username, message)
        
        # Получить аватарку пользователя
        avatar_url = await self.get_user_avatar(username)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
                'avatar_url': avatar_url,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'username': event['username'],
            'avatar_url': event.get('avatar_url'),
        }))

    async def send_online_users(self):
        online_users = await self.get_online_users()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'online_users',
                'users': online_users,
            }
        )

    async def online_users(self, event):
        await self.send(text_data=json.dumps({
            'type': 'online_users',
            'users': event['users'],
        }))

    @sync_to_async
    def add_online_user(self, user):
        OnlineUser.objects.get_or_create(user=user)

    @sync_to_async
    def remove_online_user(self, user):
        OnlineUser.objects.filter(user=user).delete()

    @sync_to_async
    def get_online_users(self):
        return list(OnlineUser.objects.select_related('user').values_list('user__username', flat=True))

    @sync_to_async
    def save_message(self, username, content):
        user = User.objects.get(username=username)
        Message.objects.create(user=user, content=content)
    
    @sync_to_async
    def get_user_avatar(self, username):
        try:
            from .models import UserProfile
            user = User.objects.get(username=username)
            profile = UserProfile.objects.get(user=user)
            if profile.avatar:
                return profile.avatar.url
        except (User.DoesNotExist, UserProfile.DoesNotExist):
            pass
        return None

class PrivateChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'private_chat_{self.chat_id}'
        
        logger.info(f"Подключение к приватному чату {self.chat_id} от пользователя: {self.scope['user']}")
        
        # Проверить, что пользователь имеет доступ к этому чату
        if self.scope["user"].is_anonymous:
            logger.warning("Анонимный пользователь пытается подключиться к приватному чату")
            await self.close()
            return
            
        # Проверить доступ к чату
        has_access = await self.check_chat_access(self.scope["user"], self.chat_id)
        if not has_access:
            logger.warning(f"Пользователь {self.scope['user'].username} не имеет доступа к чату {self.chat_id}")
            await self.close()
            return
        
        self.user = self.scope["user"]
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        logger.info(f"Приватный чат {self.chat_id} подключен для пользователя: {self.user.username}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        username = data['username']
        chat_id = data['chat_id']

        # Сохранить сообщение
        await self.save_private_message(username, message, chat_id)
        
        # Получить аватарку пользователя
        avatar_url = await self.get_user_avatar(username)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'private_message',
                'message': message,
                'username': username,
                'avatar_url': avatar_url,
                'timestamp': await self.get_current_timestamp(),
            }
        )

    async def private_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'private_message',
            'message': event['message'],
            'username': event['username'],
            'avatar_url': event.get('avatar_url'),
            'timestamp': event['timestamp'],
        }))

    @sync_to_async
    def check_chat_access(self, user, chat_id):
        try:
            from .models import PrivateChat
            chat = PrivateChat.objects.get(id=chat_id, participants=user)
            return True
        except PrivateChat.DoesNotExist:
            return False

    @sync_to_async
    def save_private_message(self, username, content, chat_id):
        try:
            from .models import PrivateChat, PrivateMessage
            user = User.objects.get(username=username)
            chat = PrivateChat.objects.get(id=chat_id)
            PrivateMessage.objects.create(chat=chat, sender=user, content=content)
        except (User.DoesNotExist, PrivateChat.DoesNotExist):
            logger.error(f"Ошибка сохранения приватного сообщения: пользователь {username}, чат {chat_id}")

    @sync_to_async
    def get_current_timestamp(self):
        from django.utils import timezone
        return timezone.now().isoformat()
    
    @sync_to_async
    def get_user_avatar(self, username):
        try:
            from .models import UserProfile
            user = User.objects.get(username=username)
            profile = UserProfile.objects.get(user=user)
            if profile.avatar:
                return profile.avatar.url
        except (User.DoesNotExist, UserProfile.DoesNotExist):
            pass
        return None

class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.room_group_name = f'group_chat_{self.group_id}'
        
        logger.info(f"Подключение к групповому чату {self.group_id} от пользователя: {self.scope['user']}")
        
        # Проверить, что пользователь имеет доступ к этой группе
        if self.scope["user"].is_anonymous:
            logger.warning("Анонимный пользователь пытается подключиться к групповому чату")
            await self.close()
            return
            
        # Проверить членство в группе
        is_member = await self.check_group_membership(self.scope["user"], self.group_id)
        if not is_member:
            logger.warning(f"Пользователь {self.scope['user'].username} не является участником группы {self.group_id}")
            await self.close()
            return
        
        self.user = self.scope["user"]
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        logger.info(f"Групповой чат {self.group_id} подключен для пользователя: {self.user.username}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        username = data['username']
        group_id = data['group_id']

        # Сохранить сообщение
        await self.save_group_message(username, message, group_id)
        
        # Получить аватарку пользователя
        avatar_url = await self.get_user_avatar_group(username)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'group_message',
                'message': message,
                'username': username,
                'avatar_url': avatar_url,
                'timestamp': await self.get_current_timestamp_group(),
            }
        )

    async def group_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'group_message',
            'message': event['message'],
            'username': event['username'],
            'avatar_url': event.get('avatar_url'),
            'timestamp': event['timestamp'],
        }))

    @sync_to_async
    def check_group_membership(self, user, group_id):
        try:
            from .models import Group
            group = Group.objects.get(id=group_id, members=user)
            return True
        except Group.DoesNotExist:
            return False

    @sync_to_async
    def save_group_message(self, username, content, group_id):
        try:
            from .models import Group, GroupMessage
            user = User.objects.get(username=username)
            group = Group.objects.get(id=group_id)
            GroupMessage.objects.create(group=group, sender=user, content=content)
        except (User.DoesNotExist, Group.DoesNotExist):
            logger.error(f"Ошибка сохранения группового сообщения: пользователь {username}, группа {group_id}")

    @sync_to_async
    def get_current_timestamp_group(self):
        from django.utils import timezone
        return timezone.now().isoformat()

    @sync_to_async
    def get_user_avatar_group(self, username):
        try:
            from .models import UserProfile
            user = User.objects.get(username=username)
            profile = UserProfile.objects.get(user=user)
            if profile.avatar:
                return profile.avatar.url
        except (User.DoesNotExist, UserProfile.DoesNotExist):
            pass
        return None