from django.db import models

class Stock(models.Model):
    ticker = models.CharField(max_length=5, unique=True)
    num_shares = models.IntegerField(default=0)

    def __str__(self):
        return self.ticker

class Price_By_Day(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, null=True)

    date = models.DateField()
    price_by_day = models.FloatField(default = 0.0)
    
    def __str__(self):
        return str(self.price_by_day)
    
class Price_By_Month(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, null=True)

    date = models.DateField()
    price_by_month = models.FloatField(default = 0.0)
    
    def __str__(self):
        return str(self.price_by_month)