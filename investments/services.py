import calendar
from datetime import date, datetime
from django.db import transaction
from django.db.models import Sum
from rest_framework.exceptions import ValidationError

from investments.models import InvestmentEntity, InvestmentTransaction, ValuationLog
from savings.models import Wallet, MonthlyBalanceSummary


def parse_date_safely(val):
    """
    Safely normalizes various date representations (str, datetime, date, None) into a date object.
    """
    if not val:
        return date.today()
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        val = val.strip()
        if len(val) >= 10:
            val = val[:10]
        for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%d/%m/%Y'):
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                pass
    return date.today()


def get_last_date_of_month(target_date):
    """
    Returns a date object representing the last calendar date of the month for target_date.
    Accepts str, date, or datetime.
    """
    target_date = parse_date_safely(target_date)
    year, month = target_date.year, target_date.month
    _, last_day = calendar.monthrange(year, month)
    return date(year, month, last_day)


def sync_monthly_summary(user, transaction_date):
    """
    Keeps the historical MonthlyBalanceSummary aligned with total liquid wallet cash.
    """
    last_date = get_last_date_of_month(transaction_date)
    total_liquid = Wallet.objects.filter(wallet_of=user).aggregate(total=Sum('wallet_status'))['total'] or 0
    try:
        summary = MonthlyBalanceSummary.objects.get(user=user, last_date_of_month=last_date)
        summary.total_balance = total_liquid
        summary.save(update_fields=['total_balance'])
    except MonthlyBalanceSummary.DoesNotExist:
        MonthlyBalanceSummary.objects.create(
            user=user,
            last_date_of_month=last_date,
            total_balance=total_liquid
        )


@transaction.atomic
def process_investment_transaction(user, entity, wallet, transaction_type, amount, transaction_date, notes=''):
    """
    Executes an atomic investment transaction according to the Dual-Direction Accounting Rules.
    Validates wallet ownership, sufficient funds, and updates running entity & wallet values.
    """
    if wallet.wallet_of_id != user.id:
        raise ValidationError({"error": "The selected wallet does not belong to your account."})
    if entity.user_id != user.id:
        raise ValidationError({"error": "The selected investment does not belong to your account."})
    if amount <= 0:
        raise ValidationError({"error": "Amount must be greater than zero."})

    # Ensure transaction_date is always a valid date object
    safe_date = parse_date_safely(transaction_date)

    direction = entity.direction

    # Validation: Disallow cross-direction transaction types
    if direction == 'outgoing':
        if transaction_type == 'profit_paid':
            raise ValidationError({"error": "Outgoing investments cannot log 'profit_paid'. Did you mean 'profit_received'?"})
        if transaction_type not in ['capital_inject', 'capital_withdraw', 'profit_received']:
            raise ValidationError({"error": f"Invalid transaction type '{transaction_type}' for outgoing investment."})
    elif direction == 'incoming':
        if transaction_type == 'profit_received':
            raise ValidationError({"error": "Incoming investments cannot log 'profit_received'. Did you mean 'profit_paid'?"})
        if transaction_type not in ['capital_inject', 'capital_withdraw', 'profit_paid']:
            raise ValidationError({"error": f"Invalid transaction type '{transaction_type}' for incoming investment."})

    # Execute Transaction based on Direction and Type
    if direction == 'outgoing':
        if transaction_type == 'capital_inject':
            # Outflow: Wallet -> Investment
            if wallet.wallet_status < amount:
                raise ValidationError({"error": f"Insufficient balance in '{wallet.wallet_name}'. Current balance is ৳{wallet.wallet_status:,}."})
            wallet.wallet_status -= amount
            entity.total_capital_invested += amount
            entity.current_valuation += amount
            if entity.status in ['liquidated', 'matured']:
                entity.status = 'active'

        elif transaction_type == 'capital_withdraw':
            # Inflow: Investment Recovery/Sale -> Wallet
            wallet.wallet_status += amount
            # Cost-to-cash recovery logic:
            deduct_capital = min(amount, entity.total_capital_invested)
            excess = amount - deduct_capital
            entity.total_capital_invested -= deduct_capital
            entity.current_valuation = max(0, entity.current_valuation - amount)
            if excess > 0:
                entity.total_profit_realized += excess

            # Auto mark liquidated if remaining capital & valuation are both 0
            if entity.total_capital_invested == 0 and entity.current_valuation == 0:
                entity.status = 'liquidated'

        elif transaction_type == 'profit_received':
            # Inflow: Dividend / Yield / Pure Profit -> Wallet
            wallet.wallet_status += amount
            entity.total_profit_realized += amount

    elif direction == 'incoming':
        if transaction_type == 'capital_inject':
            # Inflow: Investor funds entered business wallet
            wallet.wallet_status += amount
            entity.total_capital_invested += amount
            if entity.status in ['liquidated', 'matured']:
                entity.status = 'active'

        elif transaction_type == 'profit_paid':
            # Outflow: Paying profit split to investor
            if wallet.wallet_status < amount:
                raise ValidationError({"error": f"Insufficient balance in '{wallet.wallet_name}' to pay investor. Current balance is ৳{wallet.wallet_status:,}."})
            wallet.wallet_status -= amount
            entity.total_profit_realized += amount

        elif transaction_type == 'capital_withdraw':
            # Outflow: Buyback / Returning investor's capital
            if wallet.wallet_status < amount:
                raise ValidationError({"error": f"Insufficient balance in '{wallet.wallet_name}' for capital buyback. Current balance is ৳{wallet.wallet_status:,}."})
            wallet.wallet_status -= amount
            entity.total_capital_invested = max(0, entity.total_capital_invested - amount)
            if entity.total_capital_invested == 0:
                entity.status = 'liquidated'

    # Save mutated objects
    wallet.save(update_fields=['wallet_status'])
    entity.save(update_fields=['total_capital_invested', 'current_valuation', 'total_profit_realized', 'status', 'updated_at'])

    # Create transaction record with validated date object
    tx = InvestmentTransaction.objects.create(
        entity=entity,
        wallet=wallet,
        transaction_type=transaction_type,
        amount=amount,
        transaction_date=safe_date,
        notes=notes
    )

    # Sync monthly liquid summary
    sync_monthly_summary(user, safe_date)

    return tx


@transaction.atomic
def record_valuation_update(user, entity, new_valuation, notes=''):
    """
    Updates the market valuation of an outgoing asset without altering wallet liquid cash.
    """
    if entity.user_id != user.id:
        raise ValidationError({"error": "The selected investment does not belong to your account."})
    if new_valuation < 0:
        raise ValidationError({"error": "Valuation cannot be negative."})

    old_valuation = entity.current_valuation
    entity.current_valuation = new_valuation
    entity.save(update_fields=['current_valuation', 'updated_at'])

    log = ValuationLog.objects.create(
        entity=entity,
        previous_valuation=old_valuation,
        new_valuation=new_valuation,
        notes=notes
    )
    return log
