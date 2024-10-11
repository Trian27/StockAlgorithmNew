from django.contrib import admin

from .models import Stock, Price_By_Month, Price_By_Day
# Register your models here.

admin.site.register(Stock)
admin.site.register(Price_By_Month)
admin.site.register(Price_By_Day)
