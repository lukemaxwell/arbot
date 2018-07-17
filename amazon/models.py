from django.db import models


class Item(models.Model):
    url = models.CharField(max_length=250, unique=True)
    title = models.CharField(max_length=250)
    asin = models.CharField(max_length=250, unique=True)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    currency = models.CharField(max_length=20)
    review_count = models.IntegerField()
    rating = models.DecimalField(max_digits=3, decimal_places=2)
    category = models.CharField(max_length=250)
    description = models.TextField()
    spam_rating = models.CharField(blank=True, max_length=1, null=True)

    def __str__(self):
        return self.title


class Review(models.Model):
    url = models.CharField(max_length=250, unique=True)
    title = models.CharField(max_length=250)
    rating = models.DecimalField(max_digits=3, decimal_places=2)
    date = models.DateField()
    body = models.TextField()
    author_username = models.CharField(max_length=250)
    author_url = models.CharField(max_length=250)
    verified_purchase = models.BooleanField()
    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    def __str__(self):
        return '{}...'.format(self.body[:100])


class ReviewLabel(models.Model):
    name = models.CharField(max_length=250)
    review = models.ForeignKey(Review, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'review',)
