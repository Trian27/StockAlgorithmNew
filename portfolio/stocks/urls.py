from django.urls import path

from . import views

app_name = 'stocks'

urlpatterns = [
    path('', views.index, name='index'),
    path("<int:stock_id>/", views.statistics, name="statistics"),
    #path('home', views.home, name = 'home'),
        #above does not work bc if stocks.urls included, will go to index first
        #would I have to use a UUID? (Don't know how that works)
]