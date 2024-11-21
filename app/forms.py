from django import forms
from .models import Symbol, PaperTrade
from .utils import get_smartapi_session
from django.core.exceptions import ValidationError
from decimal import Decimal

class PaperTradeForm(forms.ModelForm):

    tradingsymbol = forms.ModelChoiceField(
        queryset=Symbol.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    price = forms.DecimalField(
        label="Price", 
        required=False, 
        widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control form-control-sm'}),
        max_digits=10, 
        decimal_places=2
    )
    symboltoken = forms.CharField(
        label="Symbol Token", 
        required=False, 
        widget=forms.TextInput(
            attrs={'readonly': 'readonly', 'class': 'form-control form-control-sm'}))

    class Meta:
        model = PaperTrade
        fields = [
            'exchange',
            'tradingsymbol',
            'symboltoken',
            'variety',
            'transactiontype',
            'ordertype',
            'producttype',
            'duration',
            'price',
            'quantity',
        ]
        labels = {
            'exchange': 'Exchange',
            'symboltoken': 'Symbol Token',
            'tradingsymbol': 'Trading Symbol',
            'variety': 'Variety',
            'transactiontype': 'Transaction Type',
            'ordertype': 'Order Type',
            'producttype': 'Product Type',
            'duration': 'Duration',
            'price': 'Price',
            'quantity': 'Quantity',
        }
        widgets = {
            'exchange': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'variety': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'transactiontype': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'ordertype': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'producttype': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'duration': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'quantity': forms.NumberInput(attrs={'min': 1, 'class': 'form-control form-control-sm'}),
        }

    # def clean_price(self):
    #     price = self.cleaned_data.get('price')
    #     if price is not None:
    #         price = price.quantize(Decimal('0.00'))
    #         self.cleaned_data['price'] = price  

    #         if price.as_tuple().exponent < -2:
    #             raise ValidationError("Price cannot have more than 2 decimal places.")
    #     return price

    def clean(self):
        cleaned_data = super().clean()
        tradingsymbol = cleaned_data.get("tradingsymbol")
        exchange_value = cleaned_data.get("exchange")
        price = cleaned_data.get("price")
        
        exchange_map = {
            '1': 'NSE',
            '2': 'NFO',
        }
        exchange = exchange_map.get(str(exchange_value))
        
        if not exchange:
            self.add_error("exchange", "Invalid exchange value.")
            return cleaned_data

        if tradingsymbol:
            try:
                symbol = Symbol.objects.filter(symbol=tradingsymbol).first()
                
                if symbol:
                    session = get_smartapi_session()
                    market_data = session["obj"].ltpData(exchange, symbol.symbol, symbol.symboltoken)
                    
                    if market_data.get("status") and "data" in market_data:
                        cleaned_data["symboltoken"] = symbol.symboltoken
                        fetched_price = Decimal(market_data["data"].get("ltp", 0)).quantize(Decimal('0.00'))
                        if price:
                            cleaned_data["price"] = Decimal(price).quantize(Decimal('0.00'))
                        else:
                            cleaned_data["price"] = fetched_price
                    else:
                        self.add_error("price", "Failed to retrieve market price.")
                else:
                    self.add_error("tradingsymbol", "Selected symbol does not have a token.")
            except Exception as e:
                self.add_error("tradingsymbol", f"Error retrieving market data: {e}")
        
        return cleaned_data






class OrdersForm(forms.Form):
    EXCHANGE = (
        (2, 'NSE'),
        (3, 'NFO'),
    )
    exchange = forms.ChoiceField(
        choices=EXCHANGE,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    tradingsymbol = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )

    symboltoken = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )

    VARIETY = (
        (1, 'NORMAL'),
        (2, 'STOPLOSS'),
        (3, 'AMO'),
        (4, 'ROBO'),
    )
    variety = forms.ChoiceField(
        choices=VARIETY,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    TRANSACTIONTYPE = (
        (1, 'BUY'),
        (2, 'SELL'),
    )
    transactiontype = forms.ChoiceField(
        choices=TRANSACTIONTYPE,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    ORDERTYPE = (
        (1, 'MARKET'),
        (2, 'LIMIT'),
        (3, 'STOPLOSS_LIMIT'),
        (4, 'STOPLOSS_MARKET'),
    )
    ordertype = forms.ChoiceField(
        choices=ORDERTYPE,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    PRODUCTTYPE = (
        (1, 'DELIVERY'),
        (2, 'CARRYFORWARD'),
        (3, 'MARGIN'),
        (4, 'INTRADAY'),
        (5, 'BO')
    )
    producttype = forms.ChoiceField(
        choices=PRODUCTTYPE,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    # DURATION = (
    #     (1, 'DAY'),
    #     (2, 'IOC'),
    # )
    # duration = forms.ChoiceField(
    #     choices=DURATION,
    #     widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    # )

    price = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm'})
    )

    # squareoff = forms.CharField(
    #     max_length=100,
    #     widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    # )

    # stoploss = forms.CharField(
    #     max_length=100,
    #     widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    # )

    quantity = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm'})
    )
