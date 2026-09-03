from rest_framework import serializers
from income.models import IncomeRelated, Incomes
from savings.serializers import WalletSerializer

class IncomeRelatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeRelated
        fields = ['id', 'short_info', 'short_description', 'income_source', 'created_at']

class IncomesSerializer(serializers.ModelSerializer):
    income_related_detail = IncomeRelatedSerializer(source='income_related_id', read_only=True)
    wallet_detail = WalletSerializer(source='wallet', read_only=True)

    class Meta:
        model = Incomes
        fields = [
            'id', 'income_related_id', 'income_related_detail', 
            'amount', 'description', 'wallet', 'wallet_detail', 
            'income_date', 'created_at', 'updated_at'
        ]
