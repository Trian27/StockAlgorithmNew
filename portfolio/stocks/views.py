from django.shortcuts import render, get_object_or_404
from django.template import loader
import requests, time
from .models import Stock
from .forms import StockForm
import datetime
from django.http import JsonResponse, HttpResponse

def home(request):
    template = loader.get_template("stocks/home.html")
    context = {}
    return HttpResponse(template.render(context, request))

def buy_stock(request, stock_id):
    if request.method == 'POST':
        stock = get_object_or_404(Stock, pk = stock_id)
        num_shares = request.POST.get('num_shares')
        stock.shares = stock.shares + num_shares
        stock.save()
        data = {'message': 'Stock bought successfully'}
        return JsonResponse(data, status=200)
    else:
        data = {'error': 'Invalid request'}
        return JsonResponse(data, status=400)
    
def sell_stock(request, stock_id):
    if request.method == 'POST':
        stock = get_object_or_404(Stock, pk = stock_id)
        num_shares = request.POST.get('num_shares')
        if num_shares > stock.shares:
            stock.delete()
        else:
            stock.shares = stock.shares + num_shares
            stock.save()
        data = {'message': 'Stock sold successfully'}
        return JsonResponse(data, status=200)
    else:
        data = {'error': 'Invalid request'}
        return JsonResponse(data, status=400)

def track_new_stock(request):
    if request.method == 'POST':
        form = StockForm(request.POST)
        stock = None
        if form.is_valid():
            stock = form.save(commit=False)
            stock.ticker = stock.ticker.upper()
            if validate_ticker(stock.ticker):
                stock.save()
                data = {'message': 'Stock tracked successfully'}
                return JsonResponse(data, status=200)
            else:
                data = {'error': 'Invalid stock ticker'}
                return JsonResponse(data, status=400)
        else:
            data = {'error': 'Form failed to validate'}
            return JsonResponse(data, status=400)
    else:
        data = {'error': 'Invalid request'}
        return JsonResponse(data, status=400)

def validate_ticker(ticker):
    params = {"function": "SYMBOL_SEARCH", "keywords": ticker, "apikey": "https://www.alphavantage.co/"}
    response = requests.get("https://www.alphavantage.co/query", params)
    data = response.json()
    try:
        return data["bestMatches"][0]["1. symbol"] == ticker
    except Exception as ex:
        return False


# Index page for endpoint "stocks/"
def index(request):
    # Query database for list of all stocks
    stock_list = Stock.objects.all()
    price_list= []
    total_val = 0
    name = []
    quantity = []

    for i in range(0, len(stock_list)):
        asset = stock_list[i]
        name.append(asset.ticker)
        quantity.append(str(asset.num_shares))

        prices_ind = asset.price_set.all()
        prices_ind.delete()
        params = {"function": "TIME_SERIES_MONTHLY_ADJUSTED", "symbol": name[i], "apikey": "https://www.alphavantage.co/"}
        response = requests.get("https://www.alphavantage.co/query", params)
        data = response.json()
        
        if 'Monthly Adjusted Time Series' not in data:
            template = loader.get_template("stocks/api_request_limit_exceeded.html")
            return HttpResponse(template.render({}, request))
        for x in data['Monthly Adjusted Time Series']:
            if x.find("2024") != -1 or x.find("2023") != -1 or x.find("2022") != -1:
                #switch to find the current year through datetime and then calculuate last 3
                t_date = datetime.datetime.strptime(x,'%Y-%m-%d').date()
                asset.price_set.create(date = t_date, price = data['Monthly Adjusted Time Series'][x]['5. adjusted close'])
                #when creating price, make sure has 2 decimal places: ex. $21.8 = $21.80
        prices_ind = asset.price_set.all()        
        price_list.append(prices_ind[0])   
        total_val += price_list[i].price * int(quantity[i])

    stock_dicts = []
    for i in range(0, len(stock_list)):
        stock_dicts.append({'stock_id': str(stock_list[i].id),'ticker': stock_list[i].ticker, 'shares': stock_list[i].num_shares, 'price': price_list[i].price, 'time': price_list[i].date})
    template = loader.get_template("stocks/index.html")
    context = {"stock_dicts": stock_dicts,}
    return HttpResponse(template.render(context, request))

def statistics(request, stock_id):
    stock = get_object_or_404(Stock, pk = stock_id)
    return render(request, 'stocks/statistics.html', {'stock': stock})

