from django.contrib import admin
from .models import PaperTrade, Symbol

# Register your models here.

@admin.register(PaperTrade)
class PaperTradeAdmin(admin.ModelAdmin):
    list_display = ('id', 'tradingsymbol', 'transactiontype', 'quantity', 'price', 'date_created')

admin.site.register(Symbol)