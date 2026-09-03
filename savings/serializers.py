from rest_framework import serializers
from savings.models import PredefinedWalletList, Wallet, SavingRelated, Savings, TransferDetails, LoanEntry, ScheduledTransaction
from costs.models import CostRelated
from income.models import IncomeRelated

class PredefinedWalletListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredefinedWalletList
        fields = ['id', 'name', 'full_name', 'url', 'image']

class WalletSerializer(serializers.ModelSerializer):
    wallet_info_detail = PredefinedWalletListSerializer(source='wallet_info', read_only=True)

    class Meta:
        model = Wallet
        fields = ['id', 'wallet_name', 'wallet_info', 'wallet_info_detail', 'wallet_number', 'wallet_status', 'created_at', 'updated_at']
        read_only_fields = ['wallet_status'] # wallet status changes via incomes/costs/transfers

class SavingRelatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingRelated
        fields = ['id', 'short_info', 'short_description', 'saving_where', 'created_at']

class SavingsSerializer(serializers.ModelSerializer):
    wallet_detail = WalletSerializer(source='wallet', read_only=True)

    class Meta:
        model = Savings
        fields = ['id', 'amount', 'description', 'wallet', 'wallet_detail', 'saving_date', 'created_at', 'updated_at']

class TransferDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransferDetails
        fields = [
            'id', 'transfer_from_wallet', 'transfer_to_wallet', 
            'prev_amount_of_transfered_from', 'current_amount_of_transfered_from',
            'prev_amount_of_transfered_to', 'current_amount_of_transfered_to',
            'transfered_amount', 'tansfered_date', 'description', 'transfer_date', 'updated_at'
        ]


class LoanEntrySerializer(serializers.ModelSerializer):
    wallet_detail = WalletSerializer(source='wallet', read_only=True)

    class Meta:
        model = LoanEntry
        fields = [
            'id', 'person_name', 'amount', 'wallet', 'wallet_detail',
            'entry_date', 'description', 'entry_type', 'created_at', 'updated_at'
        ]


class CostRelatedMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostRelated
        fields = ['id', 'short_info']


class IncomeRelatedMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeRelated
        fields = ['id', 'short_info']


class ScheduledTransactionSerializer(serializers.ModelSerializer):
    wallet_detail = WalletSerializer(source='wallet', read_only=True)
    cost_category_detail = CostRelatedMiniSerializer(source='cost_category', read_only=True)
    income_category_detail = IncomeRelatedMiniSerializer(source='income_category', read_only=True)

    class Meta:
        model = ScheduledTransaction
        fields = [
            'id', 'transaction_type', 'amount', 'wallet', 'wallet_detail',
            'cost_category', 'cost_category_detail',
            'income_category', 'income_category_detail',
            'scheduled_date', 'description', 'status', 'created_at', 'updated_at'
        ]
