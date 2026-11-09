from django.db import models
from account.models import User
from savings.models import Wallet

class InvestmentEntity(models.Model):
    DIRECTION_CHOICES = [
        ('outgoing', 'Outgoing Investment (Asset / My Capital)'),
        ('incoming', 'Incoming Investment (Investor / External Capital)'),
    ]

    ENTITY_TYPE_CHOICES = [
        ('stock', 'Stocks / Shares'),
        ('mutual_fund', 'Mutual Fund'),
        ('fixed_deposit', 'Fixed Deposit / DPS'),
        ('crypto', 'Cryptocurrency'),
        ('gold', 'Gold / Precious Metals'),
        ('real_estate', 'Real Estate / Land'),
        ('own_business_batch', 'Own Business: Inventory / Batch'),
        ('own_business_running', 'Own Business: Running Capital'),
        ('investor_equity', 'Investor Capital / Equity'),
        ('other', 'Other Investment'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('matured', 'Matured'),
        ('liquidated', 'Liquidated'),
        ('archived', 'Archived'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investments')
    name = models.CharField(max_length=120, null=False, blank=False)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default='outgoing')
    entity_type = models.CharField(max_length=30, choices=ENTITY_TYPE_CHOICES, default='other')
    
    # Financial Basis
    total_capital_invested = models.IntegerField(default=0, help_text="Active invested capital basis (outgoing) or capital liability (incoming)")
    current_valuation = models.IntegerField(default=0, help_text="Current fair market valuation or active equity")
    total_profit_realized = models.IntegerField(default=0, help_text="All-time realized dividends/profits (outgoing) or total profit distributed (incoming)")
    
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional configuration like expected ROI %, partner split %, maturity date, notes")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.get_direction_display()} - {self.get_entity_type_display()})"

    @property
    def unrealized_gain(self):
        """For outgoing market assets: valuation - capital invested"""
        if self.direction == 'outgoing':
            return self.current_valuation - self.total_capital_invested
        return 0

    @property
    def roi_percentage(self):
        """Calculates total return on investment percentage (realized profit + unrealized gain) / capital basis"""
        if self.direction == 'outgoing' and self.total_capital_invested > 0:
            total_return = self.total_profit_realized + self.unrealized_gain
            return round((total_return / self.total_capital_invested) * 100, 2)
        return 0.0


class InvestmentTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('capital_inject', 'Capital Injection / Buy / Deposit'),
        ('capital_withdraw', 'Capital Withdrawal / Recovery / Buyback'),
        ('profit_received', 'Profit Received / Dividend'),
        ('profit_paid', 'Profit Paid Out to Investor'),
    ]

    entity = models.ForeignKey(InvestmentEntity, on_delete=models.CASCADE, related_name='transactions')
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name='investment_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.IntegerField(null=False, blank=False)
    transaction_date = models.DateField(null=False, blank=False)
    notes = models.CharField(max_length=255, null=True, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-transaction_date', '-id']

    def __str__(self):
        return f"{self.entity.name} - {self.transaction_type}: {self.amount} BDT"


class ValuationLog(models.Model):
    entity = models.ForeignKey(InvestmentEntity, on_delete=models.CASCADE, related_name='valuation_logs')
    previous_valuation = models.IntegerField()
    new_valuation = models.IntegerField()
    notes = models.CharField(max_length=255, null=True, blank=True, default='')
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.entity.name}: {self.previous_valuation} -> {self.new_valuation} BDT"
