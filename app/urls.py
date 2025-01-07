from django.urls import path
from . import views, tests
from . import consumers


urlpatterns = [
    path('', views.index, name='index'),
    path('place_order/', views.place_order, name='place_order'),
    path('paper_trade/', views.paper_trade, name='paper_trade'),
    path('orderspage/', views.order_page, name='order_page'),
    path('get-symbol-data/', views.get_symbol_data, name='get_symbol_data'),
    path('portfolio/', views.portfolio, name='portfolio')
]

websocket_urlpatterns = [
     path('ws/live-data/', consumers.LiveDataConsumer.as_asgi()),
]