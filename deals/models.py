from django.db import models

# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=250)


class Deal(models.Model):
    description = models.CharField(max_length=250)
    url = models.CharField(max_length=250)
    price = models.DecimalField(decimal_places=2, max_digits=100)
    currency = models.CharField(max_length=20)
    views = models.IntegerField()
    # category = models.
