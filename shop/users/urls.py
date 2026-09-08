from django.urls import path

from users import views

app_name = 'users'

urlpatterns = [
    path('auth/', views.auth_view, name='auth'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('personal-data/', views.personal_data_view, name='personal_data'),
    path('bonuses/', views.bonus_history_view, name='bonus_history'),
    path('recently-viewed/', views.recently_viewed_view, name='recently_viewed'),
    path('users/', views.order_list, name='order_list'),
]
