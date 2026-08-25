from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('auth/', views.auth_view, name='auth'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('orders/', views.order_list, name='order_list'),
]