from django.db import models
from django.utils import timezone

# Create your models here.

class PaperTrade(models.Model):
    EXCHANGE_CHOICES = (
        (1, 'NSE'),
        (2, 'NFO'),
    )
    exchange = models.IntegerField(choices=EXCHANGE_CHOICES, verbose_name="Exchange")

    symboltoken = models.CharField(max_length=100, verbose_name="Symbol Token")
    tradingsymbol = models.CharField(max_length=100, verbose_name="Trading Symbol")

    VARIETY_CHOICES = (
        (1, 'NORMAL'),
        (2, 'BO'),
        (3, 'CO'),
    )
    variety = models.IntegerField(choices=VARIETY_CHOICES, verbose_name="Variety")

    TRANSACTION_TYPE_CHOICES = (
        (1, 'BUY'),
        (2, 'SELL'),
    )
    transactiontype = models.IntegerField(choices=TRANSACTION_TYPE_CHOICES, verbose_name="Transaction Type")

    ORDER_TYPE_CHOICES = (
        (1, 'MARKET'),
        (2, 'LIMIT'),
        (3, 'STOPLOSS_LIMIT'),
        (4, 'STOPLOSS_MARKET'), 
    )
    ordertype = models.IntegerField(choices=ORDER_TYPE_CHOICES, verbose_name="Order Type")

    PRODUCT_TYPE_CHOICES = (
        (1, 'DELIVERY'),
        (2, 'CARRYFORWARD'),
        (3, 'MARGIN'),
        (4, 'INTRADAY'), 
        (5, 'BO'),
    )
    producttype = models.IntegerField(choices=PRODUCT_TYPE_CHOICES, verbose_name="Product Type")

    DURATION_CHOICES = (
        (1, 'DAY'),
        (2, 'IOC'),
    )
    duration = models.IntegerField(choices=DURATION_CHOICES, verbose_name="Duration")

    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    quantity = models.IntegerField(verbose_name="Quantity")
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Date Created")
    is_live = models.BooleanField(default=True)

    close_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Close Price")
    close_date = models.DateTimeField(null=True, blank=True, verbose_name="Close Date")

    def close_order(self, close_price):
        """Mark the order as closed."""
        if not self.is_live:
            raise ValueError("Order is already closed.")
        self.is_live = False
        self.close_price = close_price
        self.close_date = timezone.now()
        self.save()


    def __str__(self):
        return f"{self.tradingsymbol} at {self.price}"


class Symbol(models.Model):
    symbol = models.CharField(max_length=200)
    symboltoken = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.symbol}"