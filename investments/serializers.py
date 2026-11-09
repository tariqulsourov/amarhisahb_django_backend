from rest_framework import serializers
from investments.models import InvestmentEntity, InvestmentTransaction, ValuationLog
from savings.serializers import WalletSerializer

class ValuationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValuationLog
        fields = ['id', 'entity', 'previous_valuation', 'new_valuation', 'notes', 'recorded_at']
        read_only_fields = ['id', 'recorded_at']


class InvestmentTransactionSerializer(serializers.ModelSerializer):
    wallet_detail = WalletSerializer(source='wallet', read_only=True)

    class Meta:
        model = InvestmentTransaction
        fields = [
            'id', 'entity', 'wallet', 'wallet_detail',
            'transaction_type', 'amount', 'transaction_date',
            'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Transaction amount must be greater than 0.")
        return value


class InvestmentEntitySerializer(serializers.ModelSerializer):
    unrealized_gain = serializers.IntegerField(read_only=True)
    roi_percentage = serializers.FloatField(read_only=True)
    recent_transactions = serializers.SerializerMethodField()
    
    # Optional fields for initial funding during creation
    initial_wallet_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    initial_amount = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = InvestmentEntity
        fields = [
            'id', 'name', 'direction', 'entity_type',
            'total_capital_invested', 'current_valuation', 'total_profit_realized',
            'status', 'metadata', 'unrealized_gain', 'roi_percentage',
            'recent_transactions', 'initial_wallet_id', 'initial_amount',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_recent_transactions(self, obj):
        txs = obj.transactions.all()[:5]
        return InvestmentTransactionSerializer(txs, many=True).data
