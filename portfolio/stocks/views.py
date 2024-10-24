from django.shortcuts import render, get_object_or_404
from django.template import loader
import requests, time
from .models import Stock, Price_By_Day, Price_By_Month
from .forms import StockForm
import datetime
from django.http import JsonResponse, HttpResponse
from django.db import IntegrityError
from datetime import date

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
        try:
            if form.is_valid():
                stock = form.save(commit=False)
                stock.ticker = stock.ticker.upper()
                if validate_ticker(stock.ticker):
                    stock.save()
                    day_prices = get_price_by_days_for_stock(stock.ticker)
                    month_prices = get_price_by_months_for_stock(stock.ticker)
                    if (day_prices == "api_request_limit_exceeded" or month_prices == "api_request_limit_exceeded"):
                        template = loader.get_template("stocks/api_request_limit_exceeded.html")
                        return HttpResponse(template.render({}, request))
                    data = {'message': 'Stock tracked successfully'}
                    return JsonResponse(data, status=200)
                else:
                    data = {'error': 'Invalid stock ticker'}
                    return JsonResponse(data, status=400)
            else:
                data = {'error': 'Form failed to validate'}
                return JsonResponse(data, status=400)
        except IntegrityError:
            return JsonResponse({'error': 'Stock is already being tracked'}, status=400)
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
    stock_dicts = []
    
    for stock in stock_list:
        try:
            curr_daily_price = Price_By_Day.objects.latest('date')
            stock_dicts.append({'stock_id': stock.id,'ticker': stock.ticker, 'shares': stock.num_shares, 'curr_daily_price': curr_daily_price.price_by_day, 'time': curr_daily_price.date})
        except Price_By_Day.DoesNotExist:
            break
    # total_val = 0
    # name = []
    # quantity = []

    # for i in range(0, len(stock_list)):
    #     asset = stock_list[i]
    #     name.append(asset.ticker)
    #     quantity.append(str(asset.num_shares))

    #     price_by_months_ind = asset.price_by_month_set.all()
    #     price_by_months_ind.delete()
    #     params = {"function": "TIME_SERIES_MONTHLY_ADJUSTED", "symbol": name[i], "apikey": "https://www.alphavantage.co/"}
    #     response = requests.get("https://www.alphavantage.co/query", params)
    #     data = response.json()
        
    #     if 'Monthly Adjusted Time Series' not in data:
    #         template = loader.get_template("stocks/api_request_limit_exceeded.html")
    #         return HttpResponse(template.render({}, request))
    #     for x in data['Monthly Adjusted Time Series']:
    #         if x.find("2024") != -1 or x.find("2023") != -1 or x.find("2022") != -1:
    #             #switch to find the current year through datetime and then calculuate last 3
    #             t_date = datetime.datetime.strptime(x,'%Y-%m-%d').date()
    #             asset.price_by_month_set.create(date = t_date, price_by_month = data['Monthly Adjusted Time Series'][x]['5. adjusted close'])
    #             #when creating price_by_month, make sure has 2 decimal places: ex. $21.8 = $21.80
    #     price_by_months_ind = asset.price_by_month_set.all()        
    #     price_by_month_list.append(price_by_months_ind[0])   
    #     total_val += price_by_month_list[i].price_by_month * int(quantity[i])

    # stock_dicts = []
    # for i in range(0, len(stock_list)):
    #     stock_dicts.append({'stock_id': str(stock_list[i].id),'ticker': stock_list[i].ticker, 'shares': stock_list[i].num_shares, 'price_by_month': price_by_month_list[i].price_by_month, 'time': price_by_month_list[i].date})
    template = loader.get_template("stocks/index.html")
    context = {"stock_dicts": stock_dicts, "date": date.today()}
    return HttpResponse(template.render(context, request))

def statistics(request, stock_id):
    stock = get_object_or_404(Stock, pk = stock_id)
    return render(request, 'stocks/statistics.html', {'stock': stock})

"""
function: update_price_by_months
description: will run automatically through CronJobs every month to remove old month price object & add the new one
parameters: request -> http request
returns: None
"""
def update_price_by_months(request):
    stock_list = Stock.objects.all()
    for stock in stock_list:

        params = {"function": "TIME_SERIES_MONTHLY_ADJUSTED", "symbol": stock.ticker, "apikey": "https://www.alphavantage.co/"}
        response = requests.get("https://www.alphavantage.co/query", params)
        data = response.json()
        
        if 'Monthly Adjusted Time Series' not in data:
            template = loader.get_template("stocks/api_request_limit_exceeded.html")
            return HttpResponse(template.render({}, request))
        
        curr_data = next(iter(data['Monthly Adjusted Time Series'].values()))
        t_date = datetime.datetime.strptime(curr_data,'%Y-%m-%d').date()

        Price_By_Month.objects.order_by('date').first().delete()
        Price_By_Month.create(stock = stock, date = t_date, price_by_day = curr_data['5. adjusted close'])
    return

"""
function: update_price_by_days
description: will run automatically through CronJobs every month to remove old day price & add the new one
parameters: request -> http request
returns: None
"""
def update_price_by_days(request):
    stock_list = Stock.objects.all()
    for stock in stock_list:

        params = {"function": "TIME_SERIES_DAILY_ADJUSTED", "symbol": stock.ticker, "apikey": "https://www.alphavantage.co/"}
        response = requests.get("https://www.alphavantage.co/query", params)
        data = response.json()
        
        if 'Time Series (Daily)' not in data:
            template = loader.get_template("stocks/api_request_limit_exceeded.html")
            return HttpResponse(template.render({}, request))
    
        curr_data = next(iter(data['Time Series (Daily)'].values()))
        t_date = datetime.datetime.strptime(curr_data,'%Y-%m-%d').date()

        Price_By_Month.objects.order_by('date').first().delete()
        Price_By_Month.create(stock = stock, date = t_date, price_by_day = curr_data['5. adjusted close'])
    return

"""
function: get_price_by_months_for_stock
parameters: ticker  -> stock ticker
returns: a list of all past adjusted monthly stock prices for a single stock, ordered by descending date
#to be used when creating a new stock object to track
"""
def get_price_by_months_for_stock(ticker):
    asset = Stock.objects.get(ticker=ticker)
    price_by_month_list = []

    params = {"function": "TIME_SERIES_MONTHLY_ADJUSTED", "symbol": ticker, "apikey": "https://www.alphavantage.co/"}
    response = requests.get("https://www.alphavantage.co/query", params)
    data = response.json()
    
    if 'Monthly Adjusted Time Series' not in data:
        return "api_request_limit_exceeded"
    
    for x in data['Monthly Adjusted Time Series']:
        if (x[8:10] == "31" or x[8:10] == "30" or x[8:10] == "28"):
            t_date = datetime.datetime.strptime(x,'%Y-%m-%d').date()
            asset.price_by_month_set.create(date = t_date, price_by_month = data['Monthly Adjusted Time Series'][x]['5. adjusted close'])

    price_by_month_list.append(asset.price_by_month_set.all())

    return price_by_month_list

"""
function: get_price_by_days_for_stock
parameters: ticker  -> stock ticker
returns: a list of all past adjusted daily stock prices for a single stock, ordered by descending date
#to be used when creating a new stock object to track
"""
def get_price_by_days_for_stock(ticker):
    asset = Stock.objects.get(ticker=ticker)
    price_by_day_list = []
    params = {"function": "TIME_SERIES_DAILY", "symbol": ticker, "apikey": "https://www.alphavantage.co/"}
    response = requests.get("https://www.alphavantage.co/query", params)
    data = response.json()
    if 'Time Series (Daily)' not in data:
        return "api_request_limit_exceeded"
    
    for x in data['Time Series (Daily)']:
        t_date = datetime.datetime.strptime(x,'%Y-%m-%d').date()
        asset.price_by_day_set.create(date = t_date, price_by_day = data['Time Series (Daily)'][x]['4. close'])

    price_by_day_list.append(asset.price_by_day_set.all())
    
    return price_by_day_list

"""
function: naive_time_series_price_forcasting_by_day
parameters: request -> http request
            ticker  -> stock ticker
returns: a list that forecasts the results for future prices based on daily information
#to be used in analysis
"""
def naive_time_series_price_forcasting_by_day(request, ticker):
    asset = Stock.objects.get(ticker=ticker)
    #cheating here: calcuating by going in reverse
    price_by_day_list = Price_By_Day.filter(stock=asset)
    forecasted_prices_by_day = []
    for x in price_by_day_list:
        #This list has a lag of 1 day
        forecasted_prices_by_day.append(x)

    return forecasted_prices_by_day

"""
function: naive_time_series_price_forcasting_by_month
parameters: request -> http request
            ticker  -> stock ticker
returns: a list that forecasts the results for future prices based on monthly information
#to be used in analysis
"""
def naive_time_series_price_forcasting_by_day(request, ticker):
    asset = Stock.objects.get(ticker=ticker)
    #cheating here: calcuating by going in reverse
    price_by_month_list = Price_By_Month.filter(stock=asset)
    forecasted_prices_by_month = []
    for x in price_by_month_list:
        #This list has a lag of 1 month
        forecasted_prices_by_month.append(x)
    
    return forecasted_prices_by_month





