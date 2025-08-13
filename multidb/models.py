from django.db import models

class AppUser(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        app_label = 'multidb'
        db_table = 'users'

class Product(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        app_label = 'multidb'
        db_table = 'products'

class Order(models.Model):
    user_id = models.IntegerField(null=True, blank=True)
    product_id = models.IntegerField(null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)

    class Meta:
        app_label = 'multidb'
        db_table = 'orders'
