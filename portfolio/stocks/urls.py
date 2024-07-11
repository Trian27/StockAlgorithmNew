from django.urls import path

from . import views

app_name = 'stocks'

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:stock_id>/', views.statistics, name='statistics'),
    path('track_new_stock/', views.track_new_stock, name='track_new_stock')
]