from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    
    # Статические страницы
    path('delivery-and-payment/', views.delivery_and_payment, name='delivery_and_payment'),
    path('contacts/', views.contacts, name='contacts'),
    path('new/', views.new_products, name='new_products'),
    path('search/', views.search_results, name='search'),
    
    # Конкретные префиксы (Бренды и Группы)
    path('brand/<slug:brand_slug>/', views.product_list, name='product_list_by_brand'),
    path('group/<slug:group_slug>/', views.product_list, name='product_list_by_group'),
    
    # Детальная страница товара
    path('<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),

    # Категория по slug — строго в самом конце
    path('<slug:category_slug>/', views.product_list, name='product_list_by_category'),
]