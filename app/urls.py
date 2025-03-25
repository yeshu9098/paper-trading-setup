from django.urls import path
from . import views, tests
from . import consumers


urlpatterns = [
    path('', views.index, name='index'),
    path('place_order/', views.place_order, name='place_order'),
    path('trade/', views.trade, name='trade'),
    path('orderspage/', views.order_page, name='order_page'),
    path('close-order/', views.close_order, name='close_order'),
    path('get-stock-data/', views.get_stock_data, name='get_stock_data'),
    path('holdings/', views.holdings, name='holdings'),
    path('analytics/', views.analytics, name='analytics')
]