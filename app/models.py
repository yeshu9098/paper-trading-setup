from django.db import models
from django.utils import timezone
from decimal import Decimal


class Stock(models.Model):
    stock = models.CharField(max_length=200)
    token = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.stock}"


class Trade(models.Model):
    stock = models.CharField(max_length=50)
    token = models.CharField(max_length=20)
    transaction = models.CharField(max_length=20)
    # order = models.CharField(max_length=20)
    price = models.IntegerField()
    quantity = models.IntegerField()
    is_live = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Date Created")
    close_date = models.DateTimeField(null=True, blank=True, verbose_name="Close Date")
    close_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Close Price")
    profit_loss = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def close_order(self, close_price):
        if not self.is_live:
            raise ValueError("Order is already closed.")
        self.is_live = False
        self.close_price = close_price
        self.close_date = timezone.now()
        order_price_decimal = Decimal(self.price)
        close_price_decimal = Decimal(close_price)
        self.transaction = int(self.transaction)
        
        if self.transaction == 1:
            self.profit_loss = (close_price_decimal - order_price_decimal) * self.quantity

        else:
            self.profit_loss = (order_price_decimal - close_price_decimal) * self.quantity

        self.save()


    def __str__(self):
        return f"{self.stock} at {self.price} token: {self.token}"
