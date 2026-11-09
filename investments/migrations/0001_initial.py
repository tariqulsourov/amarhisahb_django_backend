from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('savings', '0018_scheduledtransaction_last_notified_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvestmentEntity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('direction', models.CharField(choices=[('outgoing', 'Outgoing Investment (Asset / My Capital)'), ('incoming', 'Incoming Investment (Investor / External Capital)')], default='outgoing', max_length=10)),
                ('entity_type', models.CharField(choices=[('stock', 'Stocks / Shares'), ('mutual_fund', 'Mutual Fund'), ('fixed_deposit', 'Fixed Deposit / DPS'), ('crypto', 'Cryptocurrency'), ('gold', 'Gold / Precious Metals'), ('real_estate', 'Real Estate / Land'), ('own_business_batch', 'Own Business: Inventory / Batch'), ('own_business_running', 'Own Business: Running Capital'), ('investor_equity', 'Investor Capital / Equity'), ('other', 'Other Investment')], default='other', max_length=30)),
                ('total_capital_invested', models.IntegerField(default=0, help_text='Active invested capital basis (outgoing) or capital liability (incoming)')),
                ('current_valuation', models.IntegerField(default=0, help_text='Current fair market valuation or active equity')),
                ('total_profit_realized', models.IntegerField(default=0, help_text='All-time realized dividends/profits (outgoing) or total profit distributed (incoming)')),
                ('status', models.CharField(choices=[('active', 'Active'), ('matured', 'Matured'), ('liquidated', 'Liquidated'), ('archived', 'Archived')], default='active', max_length=15)),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional configuration like expected ROI %, partner split %, maturity date, notes')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='investments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='ValuationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('previous_valuation', models.IntegerField()),
                ('new_valuation', models.IntegerField()),
                ('notes', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('recorded_at', models.DateTimeField(auto_now_add=True)),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='valuation_logs', to='investments.investmententity')),
            ],
            options={
                'ordering': ['-recorded_at'],
            },
        ),
        migrations.CreateModel(
            name='InvestmentTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('capital_inject', 'Capital Injection / Buy / Deposit'), ('capital_withdraw', 'Capital Withdrawal / Recovery / Buyback'), ('profit_received', 'Profit Received / Dividend'), ('profit_paid', 'Profit Paid Out to Investor')], max_length=20)),
                ('amount', models.IntegerField()),
                ('transaction_date', models.DateField()),
                ('notes', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='investments.investmententity')),
                ('wallet', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='investment_transactions', to='savings.wallet')),
            ],
            options={
                'ordering': ['-transaction_date', '-id'],
            },
        ),
    ]
