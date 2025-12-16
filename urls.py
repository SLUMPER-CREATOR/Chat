from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    path('', login_required(views.room), name='room'),
]