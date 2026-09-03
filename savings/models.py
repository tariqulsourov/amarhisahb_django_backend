from django.db import models
from account.models import User

# Create your models here.

class PredefinedWalletList(models.Model):
    name = models.CharField(max_length=20, null=False, blank=False)
    full_name = models.CharField(max_length=30, null=True, blank=True, default='')
    url = models.CharField(max_length=100, blank=True, null=True, default='')
    image = models.CharField(max_length=255, null=False, blank=False)
    created_at = models.DateField(auto_now_add=True)

class Wallet(models.Model):
    
    wallet_name = models.CharField(max_length=30, null=False, blank=False, default='')
    wallet_info = models.ForeignKey(PredefinedWalletList, blank=True, null=True, default=1, on_delete=models.CASCADE)
    wallet_number = models.CharField(max_length=24, null=True, blank=True)
    wallet_status = models.IntegerField(null=True, blank=True)
    wallet_of = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    class Meta:
        unique_together = ("wallet_info", "wallet_of")

    def __int__(self):
        return self.id

class SavingRelated(models.Model):
    create_by = models.ForeignKey(User, on_delete=models.CASCADE)
    short_info = models.CharField(max_length=50, null=False, blank=False, default='')
    short_description = models.CharField(max_length=255, null=True, blank=True, default='')
    saving_where = models.CharField(max_length=50, null=True, blank=True, default='')
    created_at = models.DateField(auto_now_add=True)

    def __int__(self):
        return self.id

class Savings(models.Model):
    # saving_related_id = models.ForeignKey(SavingRelated, on_delete=models.CASCADE)
    amount = models.IntegerField(blank=False, null=False)
    description = models.CharField(max_length=255, null=False, blank=True, default="")
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    saving_date = models.DateField(null=True, blank=True)
    create_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def __int__(self):
        return self.id

class TransferDetails(models.Model):
    transfer_from_wallet = models.CharField(max_length=20, null=False, blank=False, default='')
    transfer_to_wallet = models.CharField(max_length=20, null=False, blank=False, default='')
    prev_amount_of_transfered_from = models.IntegerField(blank=False, null=False)
    current_amount_of_transfered_from = models.IntegerField(blank=False, null=False)
    prev_amount_of_transfered_to = models.IntegerField(blank=False, null=False)
    current_amount_of_transfered_to = models.IntegerField(blank=False, null=False)
    transfered_amount = models.IntegerField(blank=False, null=False)
    tansfered_date = models.DateField(auto_now_add=True)
    description = models.CharField(max_length=255, null=True, blank=True, default='')
    transfer_date = models.DateField(null=True, blank=True)
    create_by = models.ForeignKey(User, on_delete=models.CASCADE)
    updated_at = models.DateField(auto_now=True)

    def __int__(self):
        return self.id
    
class MonthlyBalanceSummary(models.Model):
    last_date_of_month = models.DateField(null=False, blank=False)
    total_balance = models.IntegerField(null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LoanEntry(models.Model):
    LOAN_TYPES = [
        ('take', 'Take Loan'),
        ('give', 'Give Loan'),
        ('repay', 'Repay Loan'),
        ('collect', 'Collect Return'),
    ]
    person_name = models.CharField(max_length=100, null=False, blank=False)
    amount = models.IntegerField(null=False, blank=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    entry_date = models.DateField(null=False, blank=False)
    description = models.CharField(max_length=255, null=True, blank=True, default='')
    entry_type = models.CharField(max_length=10, choices=LOAN_TYPES, null=False, blank=False)
    create_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.person_name} - {self.entry_type} - {self.amount}"


class ScheduledTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('cost', 'Cost'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=6, choices=TRANSACTION_TYPES, null=False, blank=False)
    amount = models.IntegerField(null=False, blank=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    cost_category = models.ForeignKey('costs.CostRelated', on_delete=models.SET_NULL, null=True, blank=True)
    income_category = models.ForeignKey('income.IncomeRelated', on_delete=models.SET_NULL, null=True, blank=True)
    scheduled_date = models.DateField(null=False, blank=False)
    description = models.CharField(max_length=255, null=True, blank=True, default='')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount} on {self.scheduled_date}"

