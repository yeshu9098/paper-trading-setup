from django.urls import path
from . import views, tests
from . import consumers


urlpatterns = [
    path('', views.index, name='index'),
    path('place_order/', views.place_order, name='place_order'),
    path('trade/', views.trade, name='trade'),
    path('orderspage/', views.order_page, name='order_page'),
    path('get-stock-data/', views.get_stock_data, name='get_stock_data'),
    path('holdings/', views.holdings, name='holdings'),
    path('analytics/', views.analytics, name='analytics')
]

websocket_urlpatterns = [
     path('ws/live-data/', consumers.LiveDataConsumer.as_asgi()),
]