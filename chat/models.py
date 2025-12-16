from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}"

class OnlineUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} — онлайн"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    
    def __str__(self):
        return f"Профиль {self.user.username}"
    
    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None
    
    def get_likes_count(self):
        """Получить количество лайков пользователя"""
        return self.user.received_likes.count()
    
    def get_given_likes_count(self):
        """Получить количество лайков, которые пользователь поставил"""
        return self.user.given_likes.count()

class PrivateChat(models.Model):
    participants = models.ManyToManyField(User, related_name='private_chats')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        users = list(self.participants.all())
        if len(users) >= 2:
            return f"Чат между {users[0].username} и {users[1].username}"
        return f"Чат {self.id}"
    
    def get_other_user(self, current_user):
        """Получить собеседника для текущего пользователя"""
        return self.participants.exclude(id=current_user.id).first()

class PrivateMessage(models.Model):
    chat = models.ForeignKey(PrivateChat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"

class Group(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=500, blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(User, related_name='chat_groups', through='GroupMembership')
    avatar = models.ImageField(upload_to='group_avatars/', blank=True, null=True)
    is_private = models.BooleanField(default=False)  # Приватная группа требует приглашения
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None

class GroupMembership(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('moderator', 'Модератор'),
        ('member', 'Участник'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'group']
    
    def __str__(self):
        return f"{self.user.username} в {self.group.name} ({self.role})"

class GroupMessage(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.username} в {self.group.name}: {self.content[:30]}"

class UserLike(models.Model):
    """Лайки между пользователями"""
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_likes')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['from_user', 'to_user']
    
    def __str__(self):
        return f"{self.from_user.username} лайкнул {self.to_user.username}"