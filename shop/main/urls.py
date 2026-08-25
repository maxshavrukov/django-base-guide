from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    # Статические и специальные страницы
    path('delivery-and-payment/', views.delivery_and_payment, name='delivery_and_payment'),
    path('contacts/', views.contacts, name='contacts'),
    path('new/', views.new_products, name='new_products'),
    path('search/', views.search_results, name='search'),
    # Категория по slug — строго последняя
    path('<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),

]
