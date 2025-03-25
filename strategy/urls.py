from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('app.urls')),
    #path('watchlist/', include('data.urls')),
    path("admin/", admin.site.urls),
]
