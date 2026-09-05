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
            rel = getattr(obj, 'income_related_id', None)
            if rel:
                return {
                    'id': rel.id,
                    'short_info': rel.short_info,
                    'short_description': rel.short_description or '',
                    'income_source': rel.income_source or '',
                }
        except Exception:
            pass
        return None

    def get_wallet_detail(self, obj):
        try:
            w = getattr(obj, 'wallet', None)
            if w:
                w_info = getattr(w, 'wallet_info', None)
                return {
                    'id': w.id,
                    'wallet_name': w.wallet_name,
                    'wallet_number': w.wallet_number or '',
                    'wallet_status': w.wallet_status if w.wallet_status is not None else 0,
                    'wallet_info_detail': {
                        'id': w_info.id,
                        'name': w_info.name,
                        'image': w_info.image,
                    } if w_info else None
                }
        except Exception:
            pass
        return None

