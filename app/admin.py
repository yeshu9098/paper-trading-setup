from django.contrib import admin
from .models import Trade, Stock

# Register your models here.

@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('id', 'stock', 'transaction', 'quantity', 'price', 'date_created')

admin.site.register(Stock)