# chat/urls.py
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from . import views

def test_websocket(request):
    return render(request, 'test_websocket.html')

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return redirect('profile')

urlpatterns = [
    path('', views.room, name='room'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('logout/', logout_view, name='logout'),
    path('private/', views.private_chats, name='private_chats'),
    path('private/<int:chat_id>/', views.private_chat_room, name='private_chat_room'),
    path('start-chat/<int:user_id>/', views.start_private_chat, name='start_private_chat'),
    path('groups/', views.groups_list, name='groups_list'),
    path('groups/create/', views.create_group, name='create_group'),
    path('groups/<int:group_id>/', views.group_room, name='group_room'),
    path('groups/<int:group_id>/join/', views.join_group, name='join_group'),
    path('groups/<int:group_id>/leave/', views.leave_group, name='leave_group'),
    path('user/<int:user_id>/', views.user_profile_view, name='user_profile'),
    path('like/<int:user_id>/', views.toggle_like, name='toggle_like'),
    path('test/', test_websocket, name='test_websocket'),
]