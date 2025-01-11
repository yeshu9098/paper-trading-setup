from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .utils import get_smartapi_session
from .forms import TradeForm
import pandas as pd
import json
import requests
from .models import Stock, Trade
from datetime import datetime
from django.utils.timezone import now
import os
from django.conf import settings
from django.db.models import Sum, Avg, Count, Max, Min, Case, When, FloatField



def load_cached_scrip_data():
    filepath = os.path.join(settings.BASE_DIR, "OpenAPIScripMaster.json")
    with open(filepath, 'r') as file:
        return json.load(file)

def index(request):
    session = get_smartapi_session()
    if not session:
        return render(request, 'error.html', {'error': 'Failed to initialize session.'})

    candle_data_json = ""
    search_results = []

    # # Initial rendering
    request.session['initial_form_posted'] = False

    if not request.session.get('initial_form_posted', False):
        token = '3045'
        interval = 'FIFTEEN_MINUTE'
        fromdate = '2024-01-01 09:15'
        todate = todate = datetime.now().strftime('%Y-%m-%d %H:%M')

        historic_param = {
            "exchange": "NSE",
            "symboltoken": token,
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
            token = request.POST.get('token')
            interval = request.POST.get('interval')

            historic_param = {
                "exchange": "NSE",
                "symboltoken": token,
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
            print(symbol)
            # url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
            # try:
            #     data = requests.get(url).json()
            try:
                data = load_cached_scrip_data()
                if not data:
                    raise Exception("Failed to load scrip data.")
            
                matching_data = [item for item in data if symbol in item['symbol']]
                print(matching_data)
                search_results = matching_data[:50]
            except Exception as e:
                return render(request, 'error.html', {'error': 'Failed to fetch symbol data.'})

        if form_type == 'add_stock_form':
            selected_data = request.POST.get('add_stock').split('|')
            stock, token = selected_data[0], selected_data[1]
            if not Stock.objects.filter(stock=stock, token=token).exists():
                Stock.objects.create(stock=stock, token=token)

        if form_type == 'remove_stock_form':
            token = request.POST.get('remove_stock')
            try:
                stock = Stock.objects.get(token=token)
                stock.delete()
            except Stock.DoesNotExist:
                return render(request, 'error.html', {'error': 'Stock not found in watchlist.'})


    try:
        user = session['obj'].getProfile(session['refreshToken'])['data']
        holdings = session['obj'].allholding()
        watch_list = Stock.objects.all()
        

        context = {
            "user": user,
            "holdings": holdings,
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




def get_stock_data(request):
    session = get_smartapi_session()
    stock_id = request.GET.get("stock")

    print(stock_id)
    if stock_id:
        try:
            stock = Stock.objects.get(id=stock_id)

            market_data = session['obj'].ltpData("NSE", stock.stock, stock.token)
            print(market_data)
            
            if market_data.get("status") and "data" in market_data:
                price = market_data["data"].get("ltp", 0)
                return JsonResponse({
                    "token": stock.token,
                    "price": price
                })
            else:
                return JsonResponse({"error": "Failed to retrieve market data get_stock_data"}, status=500)
        
        except Stock.DoesNotExist:
            return JsonResponse({"error": "Symbol not found"}, status=404)
    
    return JsonResponse({"error": "Invalid parameters"}, status=400)



def order_page(request):
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        close_price = request.POST.get("close_price")
        
        try:
            order = get_object_or_404(Trade, id=order_id, is_live=True)
            close_price = float(close_price)
            
            order.close_order(close_price=close_price)
            return JsonResponse({"success": "Order closed successfully!"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    
    open_orders = Trade.objects.filter(is_live=True)
    closed_orders = Trade.objects.filter(is_live=False).order_by('-id')
    context = {
        "open_orders": open_orders,
        "closed_orders": closed_orders
        }
    return render(request, "orderpage.html", context)




def trade(request):
    if request.method == 'POST':
        form = TradeForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            stock = cleaned_data.get("stock")
            token = cleaned_data.get("token")
            transaction = cleaned_data.get("transaction")
            order = cleaned_data.get("order")
            price = cleaned_data.get("price")
            quantity = cleaned_data.get("quantity")
            
            Trade.objects.create(
                stock=stock,
                token=token,
                transaction=transaction,
                order=order,
                price=price,
                quantity=quantity,
            )
            
            return redirect("order_page")
        else:
            return JsonResponse({"status": "error", "message": "Form validation failed.", "errors": form.errors})
    
    form = TradeForm()
    return render(request, 'trade.html', {'form': form})



def holdings(request):
    session = get_smartapi_session()
    user = session['obj'].getProfile(session['refreshToken'])['data']
    holdings = session['obj'].allholding()
    context = {
        'user': user,
        'holdings': holdings,
    }
    return render(request, 'holdings.html', context)




def analytics(request):
    trades = Trade.objects.filter(is_live=False)

    total_orders = trades.count()

    profit = trades.filter(profit_loss__gt=0).aggregate(total_profit=Sum('profit_loss'))['total_profit'] or 0
    loss = trades.filter(profit_loss__lt=0).aggregate(total_loss=Sum('profit_loss'))['total_loss'] or 0
    total_profit_trades = trades.filter(profit_loss__gt=0).count()
    total_loss_trades = trades.filter(profit_loss__lt=0).count()

    win_rate = (total_profit_trades / total_orders * 100) if total_orders > 0 else 0

    net_profit_loss = profit + loss

    avg_profit = trades.filter(profit_loss__gt=0).aggregate(avg_profit=Avg('profit_loss'))['avg_profit'] or 0
    avg_loss = trades.filter(profit_loss__lt=0).aggregate(avg_loss=Avg('profit_loss'))['avg_loss'] or 0

    max_profit = trades.filter(profit_loss__gt=0).aggregate(max_profit=Max('profit_loss'))['max_profit'] or 0
    max_loss = trades.filter(profit_loss__lt=0).aggregate(max_loss=Min('profit_loss'))['max_loss'] or 0

    live_trades = Trade.objects.filter(is_live=True).count()

    stock_breakdown = trades.values('stock').annotate(
        total_trades=Count('id'),
        total_profit=Sum(Case(
            When(profit_loss__gt=0, then='profit_loss'),
            default=0,
            output_field=FloatField()
        )),
        total_loss=Sum(Case(
            When(profit_loss__lt=0, then='profit_loss'),
            default=0,
            output_field=FloatField()
        )),
    )

    profit_loss = {
        'Profit': float(profit),
        'Loss': abs(float(loss)),
    }

    context = {
        "trades": trades,
        "total_orders": total_orders,
        "profit_loss": json.dumps(profit_loss),
        "total_profit_trades": total_profit_trades,
        "total_loss_trades": total_loss_trades,
        "live_trades": live_trades,
        "win_rate": round(win_rate, 2),
        "net_profit_loss": round(net_profit_loss, 2),
        "avg_profit": round(avg_profit, 2),
        "avg_loss": round(abs(avg_loss), 2),
        "max_profit": round(max_profit, 2),
        "max_loss": round(abs(max_loss), 2),
        "stock_breakdown": stock_breakdown,
    }

    return render(request, "analytics.html", context)
