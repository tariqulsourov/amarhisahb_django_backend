from rest_framework import serializers
from income.models import IncomeRelated, Incomes
from savings.serializers import WalletSerializer

class IncomeRelatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeRelated
        fields = ['id', 'short_info', 'short_description', 'income_source', 'created_at']

class IncomesSerializer(serializers.ModelSerializer):
    income_related_detail = serializers.SerializerMethodField()
    wallet_detail = serializers.SerializerMethodField()

    class Meta:
        model = Incomes
        fields = [
            'id', 'income_related_id', 'income_related_detail', 
            'amount', 'description', 'wallet', 'wallet_detail', 
            'income_date', 'created_at', 'updated_at'
        ]

    def get_income_related_detail(self, obj):
        try:
            if obj.income_related_id_id:
                return IncomeRelatedSerializer(obj.income_related_id).data
        except Exception:
            return None
        return None

    def get_wallet_detail(self, obj):
        try:
            if obj.wallet_id:
                return WalletSerializer(obj.wallet).data
        except Exception:
            return None
        return None

