from datetime import date
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from investments.models import InvestmentEntity, InvestmentTransaction, ValuationLog
from investments.serializers import (
    InvestmentEntitySerializer,
    InvestmentTransactionSerializer,
    ValuationLogSerializer
)
from investments.services import process_investment_transaction, record_valuation_update
from savings.models import Wallet

class InvestmentEntityViewSet(viewsets.ModelViewSet):
    serializer_class = InvestmentEntitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = InvestmentEntity.objects.filter(user=user)

        direction = self.request.query_params.get('direction')
        if direction in ['outgoing', 'incoming']:
            queryset = queryset.filter(direction=direction)

        status_param = self.request.query_params.get('status')
        if status_param and status_param != 'all':
            queryset = queryset.filter(status=status_param)

        entity_type = self.request.query_params.get('entity_type')
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        initial_wallet_id = serializer.validated_data.pop('initial_wallet_id', None)
        initial_amount = serializer.validated_data.pop('initial_amount', None)

        entity = serializer.save(user=user)

        # Handle optional initial funding directly upon creation
        if initial_wallet_id and initial_amount and initial_amount > 0:
            wallet = get_object_or_404(Wallet, id=initial_wallet_id, wallet_of=user)
            process_investment_transaction(
                user=user,
                entity=entity,
                wallet=wallet,
                transaction_type='capital_inject',
                amount=initial_amount,
                transaction_date=date.today(),
                notes="Initial capital investment"
            )

    @action(detail=True, methods=['get', 'post'], url_path='transactions')
    def transactions(self, request, pk=None):
        entity = self.get_object()
        user = request.user

        if request.method == 'GET':
            txs = entity.transactions.all()
            serializer = InvestmentTransactionSerializer(txs, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            wallet_id = request.data.get('wallet')
            transaction_type = request.data.get('transaction_type')
            amount = request.data.get('amount')
            transaction_date_str = request.data.get('transaction_date') or str(date.today())
            notes = request.data.get('notes', '')

            if not wallet_id or not transaction_type or not amount:
                return Response(
                    {"error": "wallet, transaction_type, and amount are required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                amount_int = int(amount)
                if amount_int <= 0:
                    raise ValueError()
            except ValueError:
                return Response(
                    {"error": "Amount must be a positive integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            wallet = get_object_or_404(Wallet, id=wallet_id, wallet_of=user)

            tx = process_investment_transaction(
                user=user,
                entity=entity,
                wallet=wallet,
                transaction_type=transaction_type,
                amount=amount_int,
                transaction_date=transaction_date_str,
                notes=notes
            )

            # Return newly created transaction alongside refreshed entity stats
            tx_data = InvestmentTransactionSerializer(tx).data
            entity_data = InvestmentEntitySerializer(entity).data
            return Response({
                "transaction": tx_data,
                "entity": entity_data
            }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='update-valuation')
    def update_valuation(self, request, pk=None):
        entity = self.get_object()
        user = request.user
        new_valuation = request.data.get('new_valuation')
        notes = request.data.get('notes', '')

        if new_valuation is None:
            return Response({"error": "new_valuation is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            val_int = int(new_valuation)
            if val_int < 0:
                raise ValueError()
        except ValueError:
            return Response({"error": "Valuation must be a non-negative integer."}, status=status.HTTP_400_BAD_REQUEST)

        log = record_valuation_update(
            user=user,
            entity=entity,
            new_valuation=val_int,
            notes=notes
        )

        return Response({
            "valuation_log": ValuationLogSerializer(log).data,
            "entity": InvestmentEntitySerializer(entity).data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='archive')
    def archive(self, request, pk=None):
        entity = self.get_object()
        entity.status = 'archived'
        entity.save(update_fields=['status', 'updated_at'])
        return Response({"success": f"'{entity.name}' has been archived."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        user = request.user
        entities = InvestmentEntity.objects.filter(user=user)

        outgoing_entities = entities.filter(direction='outgoing')
        incoming_entities = entities.filter(direction='incoming')

        # Outgoing Metrics
        total_invested_capital = outgoing_entities.aggregate(total=Sum('total_capital_invested'))['total'] or 0
        current_portfolio_value = outgoing_entities.aggregate(total=Sum('current_valuation'))['total'] or 0
        total_realized_profit = outgoing_entities.aggregate(total=Sum('total_profit_realized'))['total'] or 0
        unrealized_gain = current_portfolio_value - total_invested_capital

        roi_percentage = 0.0
        if total_invested_capital > 0:
            roi_percentage = round(((total_realized_profit + unrealized_gain) / total_invested_capital) * 100, 2)

        # Incoming Metrics
        total_investors_capital_held = incoming_entities.aggregate(total=Sum('total_capital_invested'))['total'] or 0
        total_profit_paid_out = incoming_entities.aggregate(total=Sum('total_profit_realized'))['total'] or 0

        # Net Investment Equity
        net_investment_equity = current_portfolio_value - total_investors_capital_held

        return Response({
            "outgoing": {
                "total_invested_capital": total_invested_capital,
                "current_portfolio_value": current_portfolio_value,
                "unrealized_gain": unrealized_gain,
                "total_realized_profit": total_realized_profit,
                "roi_percentage": roi_percentage,
                "active_count": outgoing_entities.filter(status='active').count()
            },
            "incoming": {
                "total_investors_capital_held": total_investors_capital_held,
                "total_profit_paid_out": total_profit_paid_out,
                "active_count": incoming_entities.filter(status='active').count()
            },
            "net_investment_equity": net_investment_equity
        })


class InvestmentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InvestmentTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = InvestmentTransaction.objects.filter(entity__user=user)

        entity_id = self.request.query_params.get('entity')
        if entity_id:
            queryset = queryset.filter(entity_id=entity_id)

        wallet_id = self.request.query_params.get('wallet')
        if wallet_id:
            queryset = queryset.filter(wallet_id=wallet_id)

        tx_type = self.request.query_params.get('transaction_type')
        if tx_type:
            queryset = queryset.filter(transaction_type=tx_type)

        return queryset
