from django import forms
from .models import Stock, Trade
from .utils import get_smartapi_session
from django.core.exceptions import ValidationError
from decimal import Decimal


class TradeForm(forms.Form):

    stock = forms.ModelChoiceField(
         queryset=Stock.objects.all(),
         widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
     )

    token = forms.CharField(
         max_length=20,
         widget=forms.HiddenInput()
     )

    ORDERTYPE = (
        (1, 'MARKET'),
        (2, 'STOPLOSS'),
        (3, 'LIMIT')
    )
    order = forms.ChoiceField(
        choices=ORDERTYPE,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    TRANSACTIONTYPE = (
        (1, 'BUY'),
        (2, 'SELL'),
    )
    transaction = forms.ChoiceField(
        choices=TRANSACTIONTYPE,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )


    price = forms.DecimalField(
        widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control form-control-sm'}),
        max_digits=10, 
        decimal_places=2
    )

    quantity = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm'})
    )


    def clean(self):
        cleaned_data = super().clean()
        stock = cleaned_data.get("stock")
        price = cleaned_data.get("price")

        if stock:
            try:
                stock = Stock.objects.filter(stock=stock).first()
                print(stock)
                if stock:
                    session = get_smartapi_session()
                    market_data = session["obj"].ltpData("NSE", stock.stock, stock.token)
                    print(market_data)
                    
                    if market_data.get("status") and "data" in market_data:
                        cleaned_data["token"] = stock.token
                        fetched_price = Decimal(market_data["data"].get("ltp", 0)).quantize(Decimal('0.000'))
                        if price:
                            cleaned_data["price"] = Decimal(price).quantize(Decimal('0.00'))
                        else:
                            cleaned_data["price"] = fetched_price
                    else:
                        self.add_error("price", "Failed to retrieve market price.")
                else:
                    self.add_error("stock", "Selected stock does not have a token.")
            except Exception as e:
                self.add_error("stock", f"Error retrieving market data: {e}")
        
        return cleaned_data