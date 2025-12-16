from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.forms import ModelForm
from .models import Message, OnlineUser, UserProfile

@login_required
def room(request):
    # Получить или создать профиль для текущего пользователя
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Получить сообщения с попыткой загрузить профили пользователей
    messages = Message.objects.select_related('user').prefetch_related('user__userprofile').order_by('timestamp')[:100]
    online_users = OnlineUser.objects.select_related('user').values_list('user__username', flat=True)
    
    # Создать профили для пользователей, у которых их нет
    users_without_profiles = []
    for msg in messages:
        if not hasattr(msg.user, 'userprofile'):
            users_without_profiles.append(msg.user)
    
    if users_without_profiles:
        for user in users_without_profiles:
            UserProfile.objects.get_or_create(user=user)
    
    return render(request, 'chat/room.html', {
        'messages': messages,
        'online_users': list(online_users),
        'user_profile': user_profile,
    })

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('room')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

from django import forms

class ProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 
                'rows': 3,
                'placeholder': 'Расскажите немного о себе...'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            })
        }

@login_required
def profile(request):
    # Получить или создать профиль
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    user_messages = Message.objects.filter(user=request.user).order_by('-timestamp')[:50]
    total_messages = Message.objects.filter(user=request.user).count()
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    
    context = {
        'profile': profile,
        'form': form,
        'user_messages': user_messages,
        'total_messages': total_messages,
        'join_date': request.user.date_joined,
    }
    return render(request, 'chat/profile.html', context)

@login_required
def private_chats(request):
    """Список всех приватных чатов пользователя"""
    from .models import PrivateChat, PrivateMessage
    
    # Получить все чаты пользователя
    chats = PrivateChat.objects.filter(participants=request.user).prefetch_related('participants', 'messages')
    
    # Подготовить данные для отображения
    chat_data = []
    for chat in chats:
        other_user = chat.get_other_user(request.user)
        last_message = chat.messages.last()
        unread_count = chat.messages.filter(is_read=False).exclude(sender=request.user).count()
        
        chat_data.append({
            'chat': chat,
            'other_user': other_user,
            'last_message': last_message,
            'unread_count': unread_count,
        })
    
    # Получить всех пользователей для начала нового чата
    all_users = User.objects.exclude(id=request.user.id).select_related('userprofile')
    
    context = {
        'chat_data': chat_data,
        'all_users': all_users,
    }
    return render(request, 'chat/private_chats.html', context)

@login_required
def private_chat_room(request, chat_id):
    """Комната для приватного чата"""
    from .models import PrivateChat, PrivateMessage
    
    try:
        chat = PrivateChat.objects.get(id=chat_id, participants=request.user)
    except PrivateChat.DoesNotExist:
        messages.error(request, 'Чат не найден или у вас нет доступа к нему.')
        return redirect('private_chats')
    
    # Отметить сообщения как прочитанные
    chat.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    # Получить сообщения
    chat_messages = chat.messages.select_related('sender', 'sender__userprofile').all()
    other_user = chat.get_other_user(request.user)
    
    context = {
        'chat': chat,
        'messages': chat_messages,
        'other_user': other_user,
    }
    return render(request, 'chat/private_chat_room.html', context)

@login_required
def start_private_chat(request, user_id):
    """Начать приватный чат с пользователем"""
    from .models import PrivateChat
    
    try:
        other_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Пользователь не найден.')
        return redirect('private_chats')
    
    if other_user == request.user:
        messages.error(request, 'Нельзя создать чат с самим собой.')
        return redirect('private_chats')
    
    # Проверить, существует ли уже чат между этими пользователями
    existing_chat = PrivateChat.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).first()
    
    if existing_chat:
        return redirect('private_chat_room', chat_id=existing_chat.id)
    
    # Создать новый чат
    chat = PrivateChat.objects.create()
    chat.participants.add(request.user, other_user)
    
    messages.success(request, f'Чат с {other_user.username} создан!')
    return redirect('private_chat_room', chat_id=chat.id)

@login_required
def groups_list(request):
    """Список всех групп пользователя"""
    from .models import Group, GroupMembership
    
    # Группы пользователя
    user_groups = Group.objects.filter(members=request.user).prefetch_related('members', 'messages')
    
    # Публичные группы (не приватные)
    public_groups = Group.objects.filter(is_private=False).exclude(members=request.user)[:10]
    
    # Подготовить данные для групп пользователя
    group_data = []
    for group in user_groups:
        last_message = group.messages.last()
        membership = GroupMembership.objects.get(user=request.user, group=group)
        
        group_data.append({
            'group': group,
            'last_message': last_message,
            'membership': membership,
            'member_count': group.members.count(),
        })
    
    context = {
        'group_data': group_data,
        'public_groups': public_groups,
    }
    return render(request, 'chat/groups_list.html', context)

@login_required
def create_group(request):
    """Создать новую группу"""
    if request.method == 'POST':
        from .models import Group, GroupMembership
        
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        is_private = request.POST.get('is_private') == 'on'
        avatar = request.FILES.get('avatar')
        
        if not name:
            messages.error(request, 'Название группы обязательно.')
            return render(request, 'chat/create_group.html')
        
        if Group.objects.filter(name=name).exists():
            messages.error(request, 'Группа с таким названием уже существует.')
            return render(request, 'chat/create_group.html')
        
        # Создать группу
        group = Group.objects.create(
            name=name,
            description=description,
            creator=request.user,
            is_private=is_private,
            avatar=avatar
        )
        
        # Добавить создателя как администратора
        GroupMembership.objects.create(
            user=request.user,
            group=group,
            role='admin'
        )
        
        messages.success(request, f'Группа "{name}" создана!')
        return redirect('group_room', group_id=group.id)
    
    return render(request, 'chat/create_group.html')

@login_required
def group_room(request, group_id):
    """Комната группового чата"""
    from .models import Group, GroupMessage, GroupMembership
    
    try:
        group = Group.objects.get(id=group_id, members=request.user)
    except Group.DoesNotExist:
        messages.error(request, 'Группа не найдена или у вас нет доступа к ней.')
        return redirect('groups_list')
    
    # Получить сообщения
    group_messages = group.messages.select_related('sender', 'sender__userprofile').all()
    
    # Получить участников
    memberships = GroupMembership.objects.filter(group=group).select_related('user', 'user__userprofile')
    
    # Роль текущего пользователя
    user_membership = GroupMembership.objects.get(user=request.user, group=group)
    
    context = {
        'group': group,
        'messages': group_messages,
        'memberships': memberships,
        'user_membership': user_membership,
    }
    return render(request, 'chat/group_room.html', context)

@login_required
def join_group(request, group_id):
    """Присоединиться к группе"""
    from .models import Group, GroupMembership
    
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        messages.error(request, 'Группа не найдена.')
        return redirect('groups_list')
    
    if group.is_private:
        messages.error(request, 'Это приватная группа. Нужно приглашение.')
        return redirect('groups_list')
    
    if GroupMembership.objects.filter(user=request.user, group=group).exists():
        messages.info(request, 'Вы уже участник этой группы.')
        return redirect('group_room', group_id=group.id)
    
    # Присоединиться к группе
    GroupMembership.objects.create(
        user=request.user,
        group=group,
        role='member'
    )
    
    messages.success(request, f'Вы присоединились к группе "{group.name}"!')
    return redirect('group_room', group_id=group.id)

@login_required
def leave_group(request, group_id):
    """Покинуть группу"""
    from .models import Group, GroupMembership
    
    try:
        group = Group.objects.get(id=group_id, members=request.user)
        membership = GroupMembership.objects.get(user=request.user, group=group)
    except (Group.DoesNotExist, GroupMembership.DoesNotExist):
        messages.error(request, 'Группа не найдена.')
        return redirect('groups_list')
    
    if membership.role == 'admin' and group.members.count() > 1:
        # Проверить, есть ли другие администраторы
        other_admins = GroupMembership.objects.filter(group=group, role='admin').exclude(user=request.user)
        if not other_admins.exists():
            messages.error(request, 'Нельзя покинуть группу. Назначьте другого администратора.')
            return redirect('group_room', group_id=group.id)
    
    membership.delete()
    
    # Если это был последний участник, удалить группу
    if group.members.count() == 0:
        group.delete()
        messages.info(request, 'Группа была удалена, так как в ней не осталось участников.')
    else:
        messages.success(request, f'Вы покинули группу "{group.name}".')
    
    return redirect('groups_list')

@login_required
def toggle_like(request, user_id):
    """Поставить или убрать лайк пользователю"""
    from .models import UserLike
    from django.http import JsonResponse
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)
    
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Пользователь не найден'}, status=404)
    
    if target_user == request.user:
        return JsonResponse({'error': 'Нельзя лайкнуть самого себя'}, status=400)
    
    # Проверить, есть ли уже лайк
    like, created = UserLike.objects.get_or_create(
        from_user=request.user,
        to_user=target_user
    )
    
    if not created:
        # Лайк уже есть, убираем его
        like.delete()
        liked = False
    else:
        # Новый лайк
        liked = True
    
    # Получить новое количество лайков
    likes_count = target_user.received_likes.count()
    
    return JsonResponse({
        'liked': liked,
        'likes_count': likes_count,
        'message': f'Лайк {"поставлен" if liked else "убран"}'
    })

@login_required
def user_profile_view(request, user_id):
    """Просмотр профиля другого пользователя"""
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Пользователь не найден.')
        return redirect('private_chats')
    
    # Получить или создать профиль
    profile, created = UserProfile.objects.get_or_create(user=target_user)
    
    # Проверить, лайкнул ли текущий пользователь этого пользователя
    from .models import UserLike
    is_liked = UserLike.objects.filter(from_user=request.user, to_user=target_user).exists()
    
    # Статистика пользователя
    user_messages = Message.objects.filter(user=target_user).order_by('-timestamp')[:20]
    total_messages = Message.objects.filter(user=target_user).count()
    
    # Группы пользователя (только публичные)
    from .models import Group
    user_groups = Group.objects.filter(members=target_user, is_private=False)[:5]
    
    context = {
        'target_user': target_user,
        'profile': profile,
        'is_liked': is_liked,
        'likes_count': profile.get_likes_count(),
        'user_messages': user_messages,
        'total_messages': total_messages,
        'user_groups': user_groups,
        'join_date': target_user.date_joined,
    }
    return render(request, 'chat/user_profile.html', context)