from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .utils import get_smartapi_session
from .forms import PaperTradeForm, OrdersForm
import pandas as pd
import json
import logging
import requests
from .models import Symbol, PaperTrade
from datetime import datetime
from django.utils.timezone import now


def index(request):
    session = get_smartapi_session()
    if not session:
        return render(request, 'error.html', {'error': 'Failed to initialize session.'})

    candle_data_json = ""
    search_results = []

    # # Initial rendering
    request.session['initial_form_posted'] = False

    if not request.session.get('initial_form_posted', False):
        symboltoken = '99926000'
        interval = 'FIFTEEN_MINUTE'
        fromdate = '2024-01-01 09:15'
        todate = todate = datetime.now().strftime('%Y-%m-%d %H:%M')

        historic_param = {
            "exchange": "NSE",
            "symboltoken": symboltoken,
            "interval": interval,
            "fromdate": fromdate,
            "todate": todate,
        }

        try:
            chart_data = session['obj'].getCandleData(historic_param)
            columns = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
            candle_data = pd.DataFrame(chart_data['data'], columns=columns)
            candle_data_json = candle_data.to_json(orient='records')
            request.session['initial_form_posted'] = True

        except Exception as error:
            return render(request, 'error.html', {error})

       
    if request.method == 'POST':
        form_type = request.POST.get('form_type', None)
        if form_type == 'candle_data_form':
            form_type = request.POST.get('form_type')
            symboltoken = request.POST.get('symboltoken')
            interval = request.POST.get('interval')

            historic_param = {
                "exchange": "NSE",
                "symboltoken": symboltoken,
                "interval": interval,
                "fromdate": '2024-01-01 09:15',
                "todate": datetime.now().strftime('%Y-%m-%d %H:%M')
                }
        
            try:
                chart_data = session['obj'].getCandleData(historic_param)
                columns = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
                candle_data = pd.DataFrame(chart_data['data'], columns=columns)
                candle_data_json = candle_data.to_json(orient='records')

            except Exception as e:
                return render(request, 'error.html', {'error': 'Failed to fetch candle data.'})


        if form_type == 'search_form':
            symbol = request.POST.get('symbol').upper()
            url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
            try:
                data = requests.get(url).json()
                matching_data = [item for item in data if symbol in item['symbol']]
                search_results = matching_data[:10]
            except Exception as e:
                return render(request, 'error.html', {'error': 'Failed to fetch symbol data.'})

        if form_type == 'add_symbol_form':
            selected_data = request.POST.get('add_symbol').split('|')
            symbol, symboltoken = selected_data[0], selected_data[1]
            if not Symbol.objects.filter(symbol=symbol, symboltoken=symboltoken).exists():
                Symbol.objects.create(symbol=symbol, symboltoken=symboltoken)

        if form_type == 'remove_symbol_form':
            symbol_token = request.POST.get('remove_symbol')
            try:
                symbol = Symbol.objects.get(symboltoken=symbol_token)
                symbol.delete()
            except Symbol.DoesNotExist:
                return render(request, 'error.html', {'error': 'Symbol not found in watchlist.'})


    try:
        user = session['obj'].getProfile(session['refreshToken'])['data']
        holdings = session['obj'].allholding()
        tradeBook = session['obj'].tradeBook()
        watch_list = Symbol.objects.all()
        

        context = {
            "user": user,
            "holdings": holdings,
            "tradeBook": tradeBook,
            "candle_data_json": candle_data_json,
            "search_results": search_results,
            "watch_list" : watch_list,
            }
        return render(request, 'index.html', context)
    except Exception as e:
        return render(request, 'error.html', {'error': 'Failed to load data. Please try again.'})



def place_order(request):
    session = get_smartapi_session()
    if not session:
        return render(request, 'error.html', {'error': 'Session initialization failed.'})
    
    if request.method == "POST":
        form = OrdersForm(request.POST)
        if form.is_valid():
            try:
                response = session['obj'].placeOrderFullResponse(form.cleaned_data)
                return render(request, 'order_confirmation.html', {'response': response})
            except Exception as e:
                return render(request, 'error.html', {'error': 'Order placement failed.'})
        else:
            return render(request, 'order.html', {'form': form, 'errors': form.errors})
    
    form = OrdersForm()
    return render(request, "order.html", {'form': form})




def get_symbol_data(request):
    session = get_smartapi_session()
    tradingsymbol_id = request.GET.get("tradingsymbol")

    if tradingsymbol_id:
        try:
            symbol = Symbol.objects.get(id=tradingsymbol_id)

            market_data = session['obj'].ltpData("NSE", symbol.symbol, symbol.symboltoken)
            
            if market_data.get("status") and "data" in market_data:
                price = market_data["data"].get("ltp", 0)
                return JsonResponse({
                    "symboltoken": symbol.symboltoken,
                    "price": price
                })
            else:
                return JsonResponse({"error": "Failed to retrieve market data get_symbol_data"}, status=500)
        
        except Symbol.DoesNotExist:
            return JsonResponse({"error": "Symbol not found"}, status=404)
    
    return JsonResponse({"error": "Invalid parameters"}, status=400)



def order_page(request):
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        close_price = request.POST.get("close_price")
        
        try:
            # Validate input
            order = get_object_or_404(PaperTrade, id=order_id, is_live=True)
            close_price = float(close_price)  # Ensure it's a valid number
            
            # Close the order
            order.close_order(close_price=close_price)
            return JsonResponse({"success": "Order closed successfully!"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    
    # Show open orders
    open_orders = PaperTrade.objects.filter(is_live=True)
    closed_orders = PaperTrade.objects.filter(is_live=False).order_by('-id')
    context = {
        "open_orders": open_orders,
        "closed_orders": closed_orders
        }
    return render(request, "orderpage.html", context)




def paper_trade(request):
    if request.method == 'POST':
        form = PaperTradeForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            symbol = cleaned_data.get("tradingsymbol")
            symboltoken = cleaned_data.get("symboltoken")
            variety = cleaned_data.get("variety")
            transactiontype = cleaned_data.get("transactiontype")
            ordertype = cleaned_data.get("ordertype")
            producttype = cleaned_data.get("producttype")
            price = cleaned_data.get("price")
            quantity = cleaned_data.get("quantity")
            
            PaperTrade.objects.create(
                tradingsymbol=symbol,
                symboltoken=symboltoken,
                variety=variety,
                transactiontype=transactiontype,
                ordertype=ordertype,
                producttype=producttype,
                price=price,
                quantity=quantity,
            )
            
            return redirect("order_page")
        else:
            return JsonResponse({"status": "error", "message": "Form validation failed.", "errors": form.errors})
    
    form = PaperTradeForm()
    return render(request, 'papertrade.html', {'form': form})

def portfolio(request):
    session = get_smartapi_session()
    user = session['obj'].getProfile(session['refreshToken'])['data']
    holdings = session['obj'].allholding()
    tradeBook = session['obj'].tradeBook()
    context = {
        'user': user,
        'holdings': holdings,
        'tradeBook': tradeBook
    }
    return render(request, 'portfolio.html', context)