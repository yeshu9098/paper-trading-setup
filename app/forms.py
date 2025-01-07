from django import forms
from .models import Symbol, PaperTrade
from .utils import get_smartapi_session
from django.core.exceptions import ValidationError
from decimal import Decimal


class PaperTradeForm(forms.Form):

    tradingsymbol = forms.ModelChoiceField(
         queryset=Symbol.objects.all(),
         widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
     )

    symboltoken = forms.CharField(
        max_length=20,
        widget=forms.HiddenInput()
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
        tradingsymbol = cleaned_data.get("tradingsymbol")
        price = cleaned_data.get("price")

        if tradingsymbol:
            try:
                symbol = Symbol.objects.filter(symbol=tradingsymbol).first()
                
                if symbol:
                    session = get_smartapi_session()
                    market_data = session["obj"].ltpData("NSE", symbol.symbol, symbol.symboltoken)
                    
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

    tradingsymbol = forms.ModelChoiceField(
         queryset=Symbol.objects.all(),
         widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
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

    DURATION = (
        (1, 'DAY'),
        (2, 'IOC'),
    )
    duration = forms.ChoiceField(
        choices=DURATION,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    price = forms.DecimalField(
        widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control form-control-sm'}),
        max_digits=10, 
        decimal_places=2
    )

    squareoff = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )

    stoploss = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )

    quantity = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm'})
    )


    def clean(self):
        cleaned_data = super().clean()
        tradingsymbol = cleaned_data.get("tradingsymbol")
        price = cleaned_data.get("price")

        if tradingsymbol:
            try:
                symbol = Symbol.objects.filter(symbol=tradingsymbol).first()
                
                if symbol:
                    session = get_smartapi_session()
                    market_data = session["obj"].ltpData("NSE", symbol.symbol, symbol.symboltoken)
                    
                    if market_data.get("status") and "data" in market_data:
                        cleaned_data["tradingsymbol"] = symbol.symbol
                        cleaned_data["symboltoken"] = symbol.symboltoken
                        fetched_price = market_data["data"].get("ltp", 0)
                        if price:
                            cleaned_data["price"] = fetched_price
                            print(cleaned_data["price"])
                        else:
                            cleaned_data["price"] = fetched_price
                            print(cleaned_data["price"])
                    else:
                        self.add_error("price", "Failed to retrieve market price.")
                else:
                    self.add_error("tradingsymbol", "Selected symbol does not have a token.")
            except Exception as e:
                self.add_error("tradingsymbol", f"Error retrieving market data: {e}")
        
        return cleaned_data