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

logger = logging.getLogger(__name__)


def index(request):
    session = get_smartapi_session()
    if not session:
        return render(request, 'error.html', {'error': 'Failed to initialize session.'})

    candle_data_json = ""
    search_results = []


    # # Initial rendering

    request.session['initial_form_posted'] = False

    if not request.session.get('initial_form_posted', False):
        symboltoken = '99926000'  #symbol.symboltoken
        interval = 'FIFTEEN_MINUTE'
        fromdate = '2024-09-01 09:15'
        # todate = todate = datetime.now().strftime('%Y-%m-%d %H:%M')
        todate = '2024-11-14 15:30'

        historic_param = {
            "exchange": "NSE",
            "symboltoken": symboltoken,
            "interval": interval,
            "fromdate": fromdate,
            "todate": todate,
        }
        # print(historic_param)

        try:
            chart_data = session['obj'].getCandleData(historic_param)
            columns = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
            candle_data = pd.DataFrame(chart_data['data'], columns=columns)
            candle_data_json = candle_data.to_json(orient='records')
            request.session['initial_form_posted'] = True
            # print(candle_data_json)

        except Exception as e:
            logger.exception(f"Error fetching initial candle data: {e}")
            return render(request, 'error.html', {'error': 'Failed to fetch initial candle data.'})

       
    if request.method == 'POST':
        form_type = request.POST.get('form_type', None)
        if form_type == 'candle_data_form':
            form_type = request.POST.get('form_type')
            symboltoken = request.POST.get('symboltoken')
            interval = request.POST.get('interval')
            # fromdate = request.POST.get('fromdate').replace('T', ' ')
            # todate = request.POST.get('todate').replace('T', ' ')
            

            historic_param = {
                "exchange": "NSE",
                "symboltoken": symboltoken,
                "interval": interval,
                "fromdate": '2024-08-01 09:15',
                "todate": '2024-11-14 15:30'  # datetime.now().strftime('%Y-%m-%d %H:%M')
                }
            print(historic_param)
        
            try:
                chart_data = session['obj'].getCandleData(historic_param)
                columns = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
                candle_data = pd.DataFrame(chart_data['data'], columns=columns)
                candle_data_json = candle_data.to_json(orient='records')
                # print(candle_data_json)

            except Exception as e:
                logger.exception(f"Error fetching candle data: {e}")
                return render(request, 'error.html', {'error': 'Failed to fetch candle data.'})


        if form_type == 'search_form':
            symbol = request.POST.get('symbol').upper()
            url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
            try:
                data = requests.get(url).json()
                matching_data = [item for item in data if symbol in item['symbol']]
                search_results = matching_data[:10]
            except Exception as e:
                logger.exception(f"Error during symbol search: {e}")
                return render(request, 'error.html', {'error': 'Failed to fetch symbol data.'})

        if form_type == 'add_symbol_form':
            selected_data = request.POST.get('add_symbol').split('|')
            symbol, symboltoken = selected_data[0], selected_data[1]
            if not Symbol.objects.filter(symbol=symbol, symboltoken=symboltoken).exists():
                Symbol.objects.create(symbol=symbol, symboltoken=symboltoken)

        if form_type == 'remove_symbol_form':
            symbol_token = request.POST.get('remove_symbol')
            print(symbol_token)
            try:
                symbol = Symbol.objects.get(symboltoken=symbol_token)
                symbol.delete()
            except Symbol.DoesNotExist:
                logger.exception(f"Symbol {symbol_token} not found in watchlist.")


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
        logger.exception(f"Error loading index page: {e}")
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
                logger.exception(f"Error placing order: {e}")
                return render(request, 'error.html', {'error': 'Order placement failed.'})
        else:
            return render(request, 'order.html', {'form': form, 'errors': form.errors})
    
    form = OrdersForm()
    return render(request, "order.html", {'form': form})


def paper_trade(request):
    if request.method == 'POST':
        symbol = Symbol.objects.all()
        form = PaperTradeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("index")
        else:
            return JsonResponse({"status": "error", "message": "Form validation failed.", "errors": form.errors})
    
    form = PaperTradeForm()
    return render(request, 'papertrade.html', {'form': form})





def get_symbol_data(request):
    session = get_smartapi_session()
    tradingsymbol_id = request.GET.get("tradingsymbol")
    exchange_value = request.GET.get("exchange")  

    if tradingsymbol_id and exchange_value:
        try:
            symbol = Symbol.objects.get(id=tradingsymbol_id)
            exchange_map = {
                '1': 'NSE',
                '2': 'NFO',
            }
            exchange = exchange_map.get(exchange_value)
            
            market_data = session['obj'].ltpData(exchange, symbol.symbol, symbol.symboltoken)
            
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
        # Handle closing the order
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
    closed_orders = PaperTrade.objects.filter(is_live=False)
    context = {
        "open_orders": open_orders,
        "closed_orders": closed_orders
        }
    return render(request, "orderpage.html", context)