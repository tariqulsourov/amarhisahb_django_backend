from rest_framework import serializers
from costs.models import CostRelated, Costs
from savings.serializers import WalletSerializer

class CostRelatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostRelated
        fields = ['id', 'short_info', 'short_description', 'cost_field', 'created_at']

class CostsSerializer(serializers.ModelSerializer):
    cost_related_detail = CostRelatedSerializer(source='cost_related_id', read_only=True)
    wallet_detail = WalletSerializer(source='wallet', read_only=True)

    class Meta:
        model = Costs
        fields = [
            'id', 'cost_related_id', 'cost_related_detail',
            'amount', 'description', 'wallet', 'wallet_detail',
            'cost_date', 'created_at', 'updated_at'
        ]
