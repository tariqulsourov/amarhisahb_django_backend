from rest_framework import serializers
from costs.models import CostRelated, Costs
from savings.serializers import WalletSerializer

class CostRelatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostRelated
        fields = ['id', 'short_info', 'short_description', 'cost_field', 'created_at']

class CostsSerializer(serializers.ModelSerializer):
    cost_related_detail = serializers.SerializerMethodField()
    wallet_detail = serializers.SerializerMethodField()

    class Meta:
        model = Costs
        fields = [
            'id', 'cost_related_id', 'cost_related_detail',
            'amount', 'description', 'wallet', 'wallet_detail',
            'cost_date', 'created_at', 'updated_at'
        ]

    def get_cost_related_detail(self, obj):
        try:
            if obj.cost_related_id_id:
                return CostRelatedSerializer(obj.cost_related_id).data
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

