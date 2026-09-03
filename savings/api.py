from datetime import datetime, date
from django.db.models import Sum
from django.core.signing import Signer, BadSignature
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework.decorators import action
from savings.models import PredefinedWalletList, Wallet, SavingRelated, Savings, TransferDetails, LoanEntry, ScheduledTransaction, MonthlyBalanceSummary
from savings.serializers import (
    PredefinedWalletListSerializer, WalletSerializer, 
    SavingRelatedSerializer, SavingsSerializer, TransferDetailsSerializer,
    LoanEntrySerializer, ScheduledTransactionSerializer
)
from costs.models import Costs
from income.models import Incomes

class PredefinedWalletListViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PredefinedWalletList.objects.all()
    serializer_class = PredefinedWalletListSerializer
    permission_classes = [permissions.IsAuthenticated]

class WalletViewSet(viewsets.ModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wallet.objects.filter(wallet_of=self.request.user)

    def perform_create(self, serializer):
        # Default starting balance is 0 unless provided
        serializer.save(
            wallet_of=self.request.user, 
            wallet_status=self.request.data.get('wallet_status', 0)
        )

class BalanceTransferView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        transfers = TransferDetails.objects.filter(create_by=request.user).order_by('-id')
        serializer = TransferDetailsSerializer(transfers, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def post(self, request):
        user = request.user
        transfer_from_id = request.data.get('transfer_from')
        transfer_to_id = request.data.get('transfer_to')
        amount_str = request.data.get('amount')

        if not all([transfer_from_id, transfer_to_id, amount_str]):
            return Response(
                {"error": "transfer_from, transfer_to, and amount are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            amount = int(amount_str)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            return Response(
                {"error": "amount must be a positive integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get wallets ensuring they belong to current user
        wallet_from = get_object_or_404(Wallet, id=transfer_from_id, wallet_of=user)
        wallet_to = get_object_or_404(Wallet, id=transfer_to_id, wallet_of=user)

        if wallet_from.id == wallet_to.id:
            return Response(
                {"error": "Cannot transfer to the same wallet."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if wallet_from.wallet_status < amount:
            return Response(
                {"error": "Insufficient balance in the source wallet."},
                status=status.HTTP_400_BAD_REQUEST
            )

        description = request.data.get('description', '')
        transfer_date = request.data.get('transfer_date') or None

        # Save transfer details
        transfer_record = TransferDetails.objects.create(
            transfer_from_wallet=wallet_from.wallet_name,
            transfer_to_wallet=wallet_to.wallet_name,
            prev_amount_of_transfered_from=wallet_from.wallet_status,
            current_amount_of_transfered_from=wallet_from.wallet_status - amount,
            prev_amount_of_transfered_to=wallet_to.wallet_status,
            current_amount_of_transfered_to=wallet_to.wallet_status + amount,
            transfered_amount=amount,
            description=description,
            transfer_date=transfer_date,
            create_by=user
        )

        # Update wallet statuses
        wallet_from.wallet_status -= amount
        wallet_to.wallet_status += amount
        wallet_from.save()
        wallet_to.save()

        serializer = TransferDetailsSerializer(transfer_record)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SavingsViewSet(viewsets.ModelViewSet):
    serializer_class = SavingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Savings.objects.filter(create_by=self.request.user).order_by('-saving_date')

    def perform_create(self, serializer):
        # Retrieve the wallet associated with the savings entry
        wallet_id = self.request.data.get('wallet')
        wallet = get_object_or_404(Wallet, id=wallet_id, wallet_of=self.request.user)

        amount = int(self.request.data.get('amount', 0))

        # Adjust the wallet status (savings increases the wallet balance)
        wallet.wallet_status += amount
        wallet.save()

        serializer.save(create_by=self.request.user, wallet=wallet)

    @transaction.atomic
    def perform_destroy(self, instance):
        # Adjust wallet status on deletion (deduct the saving from wallet status)
        wallet = instance.wallet
        wallet.wallet_status -= instance.amount
        wallet.save()
        instance.delete()


class LoanEntryViewSet(viewsets.ModelViewSet):
    serializer_class = LoanEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LoanEntry.objects.filter(create_by=self.request.user).order_by('-entry_date')

    @transaction.atomic
    def perform_create(self, serializer):
        wallet_id = self.request.data.get('wallet')
        wallet = get_object_or_404(Wallet, id=wallet_id, wallet_of=self.request.user)
        amount = int(self.request.data.get('amount', 0))
        entry_type = self.request.data.get('entry_type')

        # 'take' (take loan) / 'collect' (receive return) -> increases wallet balance
        # 'give' (give loan) / 'repay' (repay loan) -> decreases wallet balance
        if entry_type in ['take', 'collect']:
            wallet.wallet_status += amount
        elif entry_type in ['give', 'repay']:
            wallet.wallet_status -= amount
        wallet.save()

        serializer.save(create_by=self.request.user, wallet=wallet)

    @transaction.atomic
    def perform_destroy(self, instance):
        wallet = instance.wallet
        # Reverse the effect of the deleted entry
        if instance.entry_type in ['take', 'collect']:
            wallet.wallet_status -= instance.amount
        elif instance.entry_type in ['give', 'repay']:
            wallet.wallet_status += instance.amount
        wallet.save()
        instance.delete()

    @transaction.atomic
    def perform_update(self, serializer):
        instance = self.get_object()
        old_wallet = instance.wallet
        old_amount = instance.amount
        old_type = instance.entry_type

        # 1. Reverse the effect of the old entry from the old wallet
        if old_type in ['take', 'collect']:
            old_wallet.wallet_status -= old_amount
        elif old_type in ['give', 'repay']:
            old_wallet.wallet_status += old_amount
        old_wallet.save()

        # 2. Extract new values
        new_wallet_id = self.request.data.get('wallet', old_wallet.id)
        new_wallet = get_object_or_404(Wallet, id=new_wallet_id, wallet_of=self.request.user)
        new_amount = int(self.request.data.get('amount', old_amount))
        new_type = self.request.data.get('entry_type', old_type)

        # 3. Apply the effect of the new entry to the new wallet
        if new_type in ['take', 'collect']:
            new_wallet.wallet_status += new_amount
        elif new_type in ['give', 'repay']:
            new_wallet.wallet_status -= new_amount
        new_wallet.save()

        serializer.save(wallet=new_wallet)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        user = request.user
        loans = LoanEntry.objects.filter(create_by=user)
        
        # Outstanding Payable = SUM(take) - SUM(repay)
        # Outstanding Receivable = SUM(give) - SUM(collect)
        total_take = sum(l.amount for l in loans if l.entry_type == 'take')
        total_repay = sum(l.amount for l in loans if l.entry_type == 'repay')
        total_give = sum(l.amount for l in loans if l.entry_type == 'give')
        total_collect = sum(l.amount for l in loans if l.entry_type == 'collect')

        payables = total_take - total_repay
        receivables = total_give - total_collect

        return Response({
            'total_payable': payables,
            'total_receivable': receivables
        })


class ScheduledTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduledTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ScheduledTransaction.objects.filter(user=self.request.user).order_by('-scheduled_date')

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        dates = request.data.get('scheduled_dates', [])
        if not dates:
            single_date = request.data.get('scheduled_date')
            if single_date:
                dates = [single_date]
            else:
                return Response({"error": "At least one scheduled date is required."}, status=status.HTTP_400_BAD_REQUEST)

        transaction_type = request.data.get('transaction_type')
        amount = request.data.get('amount')
        wallet_id = request.data.get('wallet')
        cost_category_id = request.data.get('cost_category')
        income_category_id = request.data.get('income_category')
        description = request.data.get('description', '')

        cost_category_id = cost_category_id if cost_category_id else None
        income_category_id = income_category_id if income_category_id else None

        created_items = []
        for d in dates:
            item = ScheduledTransaction.objects.create(
                user=request.user,
                transaction_type=transaction_type,
                amount=amount,
                wallet_id=wallet_id,
                cost_category_id=cost_category_id,
                income_category_id=income_category_id,
                scheduled_date=d,
                description=description
            )
            created_items.append(item)

        serializer = self.get_serializer(created_items, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def approve(self, request, pk=None):
        if request.user.is_authenticated:
            item = get_object_or_404(ScheduledTransaction, id=pk, user=request.user)
        else:
            token = request.query_params.get('token')
            if not token:
                return Response(
                    {"error": "Authentication credentials or pre-signed token is required."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            signer = Signer()
            try:
                unsigned_id = signer.unsign(token)
                if str(unsigned_id) != str(pk):
                    return Response({"error": "Invalid token signature."}, status=status.HTTP_400_BAD_REQUEST)
            except BadSignature:
                return Response({"error": "Invalid token signature."}, status=status.HTTP_400_BAD_REQUEST)
            item = get_object_or_404(ScheduledTransaction, id=pk)

        if item.status != 'pending':
            return Response({"error": "This transaction has already been processed."}, status=status.HTTP_400_BAD_REQUEST)

        # Atomic execution block
        with transaction.atomic():
            self._execute_transaction(item)

        return Response({"success": "Transaction logged and wallet balances updated successfully."})

    def _execute_transaction(self, item):
        user = item.user
        wallet = item.wallet
        amount = item.amount
        entry_date = item.scheduled_date

        if item.transaction_type == 'cost':
            if not item.cost_category:
                raise ValueError("Category is required for cost transactions.")
            
            # Deduct wallet balance
            wallet.wallet_status -= amount
            wallet.save()

            # Create Costs record
            Costs.objects.create(
                amount=amount,
                wallet=wallet,
                cost_date=entry_date,
                description=item.description or '',
                cost_related_id=item.cost_category
            )

            # Update Monthly Balance Summary
            self._update_monthly_summary(user, entry_date, -amount)
        else:
            if not item.income_category:
                raise ValueError("Category is required for income transactions.")

            # Add wallet balance
            wallet.wallet_status += amount
            wallet.save()

            # Create Incomes record
            Incomes.objects.create(
                amount=amount,
                wallet=wallet,
                income_date=entry_date,
                description=item.description or '',
                income_related_id=item.income_category
            )

            # Update Monthly Balance Summary
            self._update_monthly_summary(user, entry_date, amount)

        # Update ScheduledTransaction status
        item.status = 'approved'
        item.save()

    def _update_monthly_summary(self, user, entry_date, amount_delta):
        year, month = entry_date.year, entry_date.month
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

        total_of_all_wallets = Wallet.objects.filter(wallet_of=user).aggregate(total=Sum('wallet_status'))['total'] or 0

        try:
            monthly_summary = MonthlyBalanceSummary.objects.get(user=user, last_date_of_month=last_date_of_month)
            monthly_summary.total_balance += amount_delta
            monthly_summary.save()
        except MonthlyBalanceSummary.DoesNotExist:
            MonthlyBalanceSummary.objects.create(
                user=user,
                last_date_of_month=last_date_of_month,
                total_balance=total_of_all_wallets
            )
