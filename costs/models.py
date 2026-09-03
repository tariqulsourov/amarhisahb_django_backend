from django.db import models
from account.models import User
from savings.models import Wallet, PredefinedWalletList
# Create your models here.

class CostRelated(models.Model):
    create_by = models.ForeignKey(User, on_delete=models.CASCADE)
    short_info = models.CharField(max_length=50, null=False, blank=False, default='')
    short_description = models.CharField(max_length=255, null=True, blank=True, default='')
    cost_field = models.CharField(max_length=50, null=True, blank=True, default='')
    created_at = models.DateField(auto_now_add=True)

    def __int__(self):
        return self.id

class Costs(models.Model):
    cost_related_id = models.ForeignKey(CostRelated, on_delete=models.CASCADE)
    amount = models.IntegerField(blank=False, null=False)
    description = models.CharField(max_length=255, null=False, blank=True, default="")
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    cost_date = models.DateField(null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def __int__(self):
        return self.id