from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
from datetime import date, datetime
from django.db.models import Sum

from costs.models import CostRelated, Costs
from costs.serializers import CostRelatedSerializer, CostsSerializer
from savings.models import Wallet, MonthlyBalanceSummary

class CostRelatedViewSet(viewsets.ModelViewSet):
    serializer_class = CostRelatedSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CostRelated.objects.filter(create_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(create_by=self.request.user)

    @transaction.atomic
    def perform_destroy(self, instance):
        user = self.request.user
        default_cat, created = CostRelated.objects.get_or_create(
            create_by=user,
            short_info="System Default Cost Category",
            defaults={'short_description': 'System default fallback category'}
        )
        if instance.id == default_cat.id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"error": "Cannot delete the system default fallback category."})
        
        # Reassign all costs using this category to the default category
        Costs.objects.filter(cost_related_id=instance).update(cost_related_id=default_cat)
        instance.delete()

class CostsViewSet(viewsets.ModelViewSet):
    serializer_class = CostsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_id = self.request.user.id
        queryset = Costs.objects.filter(
            cost_related_id__create_by_id=user_id
        ).select_related('cost_related_id', 'wallet', 'wallet__wallet_info').order_by('-cost_date', '-id')

        wallet_id = self.request.query_params.get('wallet')
        if wallet_id:
            queryset = queryset.filter(wallet_id=wallet_id)

        month = self.request.query_params.get('month')
        if month:
            parts = month.split('-')
            if len(parts) == 2:
                try:
                    queryset = queryset.filter(cost_date__year=int(parts[0]), cost_date__month=int(parts[1]))
                except (ValueError, TypeError):
                    pass

        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        user = self.request.user
        wallet_id = self.request.data.get('wallet')
        wallet = get_object_or_404(Wallet, id=wallet_id, wallet_of=user)
        amount = int(self.request.data.get('amount', 0))

        # 1. Update wallet status (costs deduct from wallet balance)
        wallet.wallet_status -= amount
        wallet.save()

        # 2. Save the cost record
        cost = serializer.save(wallet=wallet)

        # 3. Update Monthly Balance Summary
        cost_date = cost.cost_date or date.today()
        year, month = cost_date.year, cost_date.month
        if month == 2:
            try:
                last_date_of_month = datetime(year, month, 28).date()
            except ValueError:
                last_date_of_month = datetime(year, month, 29).date()
        else:
            try:
                last_date_of_month = datetime(year, month, 31).date()
            except ValueError:
                last_date_of_month = datetime(year, month, 30).date()

        # Fetch total current balance of all user wallets
        total_of_all_wallets = Wallet.objects.filter(wallet_of=user).aggregate(total=Sum('wallet_status'))['total'] or 0

        try:
            monthly_summary = MonthlyBalanceSummary.objects.get(user=user, last_date_of_month=last_date_of_month)
            monthly_summary.total_balance -= amount
            monthly_summary.save()
        except MonthlyBalanceSummary.DoesNotExist:
            MonthlyBalanceSummary.objects.create(
                user=user,
                last_date_of_month=last_date_of_month,
                total_balance=total_of_all_wallets
            )

    @transaction.atomic
    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()
        old_amount = instance.amount
        old_wallet = instance.wallet

        new_amount = int(self.request.data.get('amount', old_amount))
        new_wallet_id = self.request.data.get('wallet')

        # Determine target wallet
        if new_wallet_id and int(new_wallet_id) != old_wallet.id:
            new_wallet = get_object_or_404(Wallet, id=new_wallet_id, wallet_of=user)
            # Revert old wallet and update new wallet
            old_wallet.wallet_status += old_amount
            old_wallet.save()
            new_wallet.wallet_status -= new_amount
            new_wallet.save()
            target_wallet = new_wallet
        else:
            old_wallet.wallet_status = old_wallet.wallet_status + old_amount - new_amount
            old_wallet.save()
            target_wallet = old_wallet

        # Save update
        cost = serializer.save(wallet=target_wallet)

        # Update Monthly Summary if amount changed (subtract difference from summary)
        amount_diff = new_amount - old_amount
        if amount_diff != 0:
            cost_date = cost.cost_date or date.today()
            year, month = cost_date.year, cost_date.month
            if month == 2:
                try:
                    last_date_of_month = datetime(year, month, 28).date()
                except ValueError:
                    last_date_of_month = datetime(year, month, 29).date()
            else:
                try:
                    last_date_of_month = datetime(year, month, 31).date()
                except ValueError:
                    last_date_of_month = datetime(year, month, 30).date()

            try:
                monthly_summary = MonthlyBalanceSummary.objects.get(user=user, last_date_of_month=last_date_of_month)
                monthly_summary.total_balance -= amount_diff
                monthly_summary.save()
            except MonthlyBalanceSummary.DoesNotExist:
                total_of_all_wallets = Wallet.objects.filter(wallet_of=user).aggregate(total=Sum('wallet_status'))['total'] or 0
                MonthlyBalanceSummary.objects.create(
                    user=user,
                    last_date_of_month=last_date_of_month,
                    total_balance=total_of_all_wallets
                )

    @transaction.atomic
    def perform_destroy(self, instance):
        user = self.request.user
        amount = instance.amount
        wallet = instance.wallet

        # 1. Revert wallet balance (refund cost to wallet)
        wallet.wallet_status += amount
        wallet.save()

        # 2. Update monthly balance summary
        cost_date = instance.cost_date or date.today()
        year, month = cost_date.year, cost_date.month
        if month == 2:
            try:
                last_date_of_month = datetime(year, month, 28).date()
            except ValueError:
                last_date_of_month = datetime(year, month, 29).date()
        else:
            try:
                last_date_of_month = datetime(year, month, 31).date()
            except ValueError:
                last_date_of_month = datetime(year, month, 30).date()

        try:
            monthly_summary = MonthlyBalanceSummary.objects.get(user=user, last_date_of_month=last_date_of_month)
            monthly_summary.total_balance += amount
            monthly_summary.save()
        except MonthlyBalanceSummary.DoesNotExist:
            pass

        instance.delete()
