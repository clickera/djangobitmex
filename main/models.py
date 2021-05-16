import datetime

from django.db import models


class Account(models.Model):
    name = models.CharField(max_length=300, unique=True)
    api_key = models.CharField(max_length=100)
    api_secret = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Order(models.Model):
    order_id = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20)
    volume = models.IntegerField()
    side = models.CharField(max_length=10, choices=(
        ('Buy', 'Buy'),
        ('Sell', 'Sell')
    )),
    timestamp = models.DateTimeField(default=datetime.datetime.today)
    price = models.DecimalField(decimal_places=3, max_digits=5)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="order_account")