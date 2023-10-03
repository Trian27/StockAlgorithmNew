from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader
import requests, time
from .models import Stock
import datetime

HTML_SRING = """<h1>Home Page</h1>""" #just for testing
def home(request):
    return HttpResponse(HTML_SRING)


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

        #name = []
        #name.append([s.ticker for s in stock_list])
        name.append(asset.ticker)
        #quantity = []
        #quantity.append([str(s.num_shares) for s in stock_list])
        quantity.append(str(asset.num_shares))
        #by resetting name & quantity everytime,
            #it made both of them lists within a list. Why?

        prices_ind = asset.price_set.all()
        prices_ind.delete()
        params = {"function": "TIME_SERIES_MONTHLY_ADJUSTED", "symbol": name[i], "apikey" : "https://www.alphavantage.co/"}
        #params = {"function": "TIME_SERIES_MONTHLY_ADJUSTED", "symbol": name[0][i], "apikey" : "https://www.alphavantage.co/"}
        #when accessing name list, why is it name[0][i] instead of name[i]?
        response = requests.get("https://www.alphavantage.co/query", params)
        data = response.json()
        time.sleep(12)
        
        for x in data['Monthly Adjusted Time Series']:
            if x.find("2023") != -1 or x.find("2022") != -1 or x.find("2021") != -1:
                #switch to find the current year through datetime and then calculuate last 3
                t_date = datetime.datetime.strptime(x,'%Y-%m-%d').date()
                asset.price_set.create(date = t_date, price = data['Monthly Adjusted Time Series'][x]['5. adjusted close'])
                #when creating price, make sure has 2 decimal places: ex. $21.8 = $21.80
        prices_ind = asset.price_set.all()        
        price_list.append(prices_ind[0])   
        #can probably shorten: price_list.append(asset.price_set.(somehow filter)) 
        total_val += price_list[i].price * int(quantity[i])

    stock_dicts = []
    for i in range(0, len(stock_list)):
        #when stock models are deleted, id doesn't get deleted as well
        #ex. there is no stock with id of 1, but SOXL has an id of 12
        stock_dicts.append({'stock_id': str(stock_list[i].id),'ticker': stock_list[i].ticker, 'shares': stock_list[i].num_shares, 'price': price_list[i].price, 'time': price_list[i].date})
    template = loader.get_template("stocks/index.html")
    context = {"stock_dicts": stock_dicts,}
    return HttpResponse(template.render(context, request))
    

def statistics(request, stock_id):
    stock = get_object_or_404(Stock, pk = stock_id)
    return render(request, 'stocks/statistics.html', {'stock': stock})
    #<!-- ${{stock.price_set.all()[:1].get()}} per share -->
    #<!-- Above doesn't work in statistics.html. also for some reason comment causes an error -->



