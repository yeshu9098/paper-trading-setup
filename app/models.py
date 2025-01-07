from django.db import models
from django.utils import timezone
from decimal import Decimal

# Create your models here.

class PaperTrade(models.Model):

    symboltoken = models.CharField(max_length=20)   
    tradingsymbol = models.CharField(max_length=20)
    variety = models.CharField(max_length=20)
    transactiontype = models.CharField(max_length=20)
    ordertype = models.CharField(max_length=20)
    producttype = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    quantity = models.IntegerField(verbose_name="Quantity")
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Date Created")
    is_live = models.BooleanField(default=True)
    close_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Close Price")
    profit_loss = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    close_date = models.DateTimeField(null=True, blank=True, verbose_name="Close Date")

    def close_order(self, close_price):
        if not self.is_live:
            raise ValueError("Order is already closed.")
        self.is_live = False
        self.close_price = close_price
        self.close_date = timezone.now()
        order_price = Decimal(self.price)
        close_price_decimal = Decimal(close_price)
        self.transactiontype = int(self.transactiontype)
        
        if self.transactiontype == 1:
            self.profit_loss = (close_price_decimal - order_price) * self.quantity

        else:
            self.profit_loss = (order_price - close_price_decimal) * self.quantity

        self.save()


    def __str__(self):
        return f"{self.tradingsymbol} at {self.price} token: {self.symboltoken}"





class Symbol(models.Model):
    symbol = models.CharField(max_length=200)
    symboltoken = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.symbol}"