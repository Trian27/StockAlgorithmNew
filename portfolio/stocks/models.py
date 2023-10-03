from django.db import models

# Tri-An will put in models for stocks and prices.
class Stock(models.Model):
    ticker = models.CharField(max_length=5)
    num_shares = models.IntegerField(default=0)

    def __str__(self):
        return self.ticker

class Price(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, null=True)

    date = models.DateField()
    price = models.FloatField(default = 0.0)
    
    def __str__(self):
        return str(self.price)
