from django.db import models

# Create your models here.


class Site(models.Model):
    domain = models.CharField(max_length=250)
    ip = models.GenericIpAddressField()
    rating = models.IntegerField()
    visitors_per_day = models.IntegerField()
