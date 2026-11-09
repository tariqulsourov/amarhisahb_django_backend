# ACTIVE REST API VIEWS: Required for the new React frontend and Mobile application.
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum
from datetime import date, datetime, timedelta

from account.models import User, UsersSettings, PushSubscription
from account.serializers import UserSerializer, UserRegistrationSerializer, UsersSettingsSerializer
from account.vapid import get_vapid_public_key_b64
from savings.models import Wallet, MonthlyBalanceSummary, LoanEntry
from costs.models import Costs
from income.models import Incomes
from investments.models import InvestmentEntity

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        data = request.data
        
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.phone = data.get('phone', user.phone)
        user.save()

        # Handle updating user settings (preferred view, using hand)
        try:
            settings_obj = UsersSettings.objects.get(user=user)
        except UsersSettings.DoesNotExist:
            settings_obj = UsersSettings(user=user)

        if 'prefered_view' in data:
            settings_obj.prefered_view = data.get('prefered_view')
        if 'using_hand' in data:
            settings_obj.using_hand = data.get('using_hand')
        if 'reminder_time' in data:
            settings_obj.reminder_time = data.get('reminder_time')
        if 'reminder_enabled' in data:
            settings_obj.reminder_enabled = data.get('reminder_enabled')

        settings_obj.save()

        serializer = UserSerializer(user)
        return Response(serializer.data)

class VapidPublicKeyView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        public_key = get_vapid_public_key_b64()
        return Response({"public_key": public_key}, status=status.HTTP_200_OK)

class PushSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        endpoint = request.data.get('endpoint')
        keys = request.data.get('keys', {})
        p256dh = keys.get('p256dh')
        auth = keys.get('auth')

        if not endpoint or not p256dh or not auth:
            return Response(
                {"error": "Missing subscription parameters (endpoint, keys.p256dh, keys.auth)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update or create subscription for this specific endpoint
        subscription, created = PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                'user': user,
                'p256dh': p256dh,
                'auth': auth
            }
        )
        return Response({"success": "Subscription registered successfully."}, status=status.HTTP_201_CREATED)

class DashboardSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # 1. Fetch Wallets and Total Balance
        wallets = Wallet.objects.filter(wallet_of=user)
        total_balance = wallets.aggregate(total=Sum('wallet_status'))['total'] or 0

        # 2. Get current month dates
        today_date = date.today()
        year, month = today_date.year, today_date.month
        first_date_of_this_month = datetime(year, month, 1).date()
        last_date_of_this_month = today_date

        # 3. Calculate running month costs & income
        total_cost = Costs.objects.filter(
            cost_related_id__create_by_id=user.id, 
            cost_date__range=[first_date_of_this_month, last_date_of_this_month]
        ).aggregate(total=Sum('amount'))['total'] or 0

        total_income = Incomes.objects.filter(
            income_related_id__create_by_id=user.id, 
            income_date__range=[first_date_of_this_month, last_date_of_this_month]
        ).aggregate(total=Sum('amount'))['total'] or 0

        # 4. Construct monthly graph data (last 6 months)
        graph_data = []
        temp_first_date = first_date_of_this_month
        joining_date = user.date_joined.date()
        
        # Calculate delta (months active, max 6)
        delta_months = (today_date.year - joining_date.year) * 12 + (today_date.month - joining_date.month)
        if delta_months > 6:
            delta_months = 6
        if delta_months < 1:
            delta_months = 1

        for i in range(delta_months):
            # Calculate start and end date for target month
            if i == 0:
                month_start = temp_first_date
                month_end = today_date
            else:
                month_end = temp_first_date - timedelta(days=1)
                month_start = month_end.replace(day=1)
                temp_first_date = month_start

            # Calculate cost & income totals for this specific month range
            m_cost = Costs.objects.filter(
                cost_related_id__create_by_id=user.id,
                cost_date__range=[month_start, month_end]
            ).aggregate(total=Sum('amount'))['total'] or 0

            m_income = Incomes.objects.filter(
                income_related_id__create_by_id=user.id,
                income_date__range=[month_start, month_end]
            ).aggregate(total=Sum('amount'))['total'] or 0

            # Get historical summary balance for this month
            # Format: 'YYYY-MM'
            year_month_str = f"{month_start.year}-{month_start.month:02d}"
            try:
                summary_record = MonthlyBalanceSummary.objects.get(
                    user=user, 
                    last_date_of_month__icontains=year_month_str
                )
                m_balance = summary_record.total_balance
            except Exception:
                m_balance = 0

            graph_data.append({
                "month_name": month_start.strftime("%B"),
                "year_month": year_month_str,
                "cost": m_cost,
                "income": m_income,
                "balance": m_balance
            })

        # 5. Calculate Investment Metrics
        entities = InvestmentEntity.objects.filter(user=user)
        outgoing_entities = entities.filter(direction='outgoing')
        incoming_entities = entities.filter(direction='incoming')

        total_invested_capital = outgoing_entities.aggregate(total=Sum('total_capital_invested'))['total'] or 0
        current_portfolio_value = outgoing_entities.aggregate(total=Sum('current_valuation'))['total'] or 0
        total_realized_profit = outgoing_entities.aggregate(total=Sum('total_profit_realized'))['total'] or 0
        unrealized_gain = current_portfolio_value - total_invested_capital

        roi_percentage = 0.0
        if total_invested_capital > 0:
            roi_percentage = round(((total_realized_profit + unrealized_gain) / total_invested_capital) * 100, 2)

        total_investors_capital_held = incoming_entities.aggregate(total=Sum('total_capital_invested'))['total'] or 0
        total_profit_paid_out = incoming_entities.aggregate(total=Sum('total_profit_realized'))['total'] or 0
        net_investment_equity = current_portfolio_value - total_investors_capital_held

        # 6. Calculate Loan Metrics
        loans = LoanEntry.objects.filter(create_by=user)
        total_take = sum(l.amount for l in loans if l.entry_type == 'take')
        total_repay = sum(l.amount for l in loans if l.entry_type == 'repay')
        total_give = sum(l.amount for l in loans if l.entry_type == 'give')
        total_collect = sum(l.amount for l in loans if l.entry_type == 'collect')

        payables = total_take - total_repay
        receivables = total_give - total_collect

        # 7. Formulate Total Net Worth
        # Net Worth = Liquid Cash + Investment Portfolio Value + Receivables - Payables - Investor Liabilities
        net_worth = total_balance + current_portfolio_value + receivables - payables - total_investors_capital_held

        # Return combined payload (fully backward-compatible + enriched with Net Worth)
        return Response({
            "total_balance": total_balance,
            "current_month_cost": total_cost,
            "current_month_income": total_income,
            "wallets": [{
                "id": w.id,
                "wallet_name": w.wallet_name,
                "wallet_status": w.wallet_status,
                "wallet_number": w.wallet_number,
                "image": w.wallet_info.image if w.wallet_info else None
            } for w in wallets],
            "graph_data": graph_data,
            "investments_summary": {
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
            },
            "loans_summary": {
                "receivables": receivables,
                "payables": payables
            },
            "net_worth": net_worth
        })

from rest_framework_simplejwt.tokens import RefreshToken
from account.google_auth import verify_google_id_token
from account.models import UserType

class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        id_token = request.data.get('id_token')
        if not id_token:
            return Response(
                {"error": "id_token is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_info = verify_google_id_token(id_token)
        if not user_info:
            return Response(
                {"error": "Invalid or expired Google token."},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = user_info['email']
        
        # Get or create the user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create a new regular user
            regular_user_type, _ = UserType.objects.get_or_create(user_type='regular_user')
                
            user = User.objects.create_user(
                email=email,
                password=User.objects.make_random_password(),
                first_name=user_info.get('first_name', ''),
                last_name=user_info.get('last_name', ''),
                user_type=regular_user_type
            )
            
            # Create default settings
            UsersSettings.objects.create(
                user=user,
                prefered_view='mobile',
                using_hand='right'
            )

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


from rest_framework_simplejwt.views import TokenObtainPairView
from account.serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


from io import StringIO
from django.core.management import call_command
from django.conf import settings

class InternalDispatchRemindersView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return self._dispatch(request)

    def post(self, request):
        return self._dispatch(request)

    def _dispatch(self, request):
        secret_token = request.query_params.get('secret') or request.headers.get('X-Internal-Secret')
        configured_secret = getattr(settings, 'INTERNAL_CRON_SECRET', 'amarhishab_cron_secret_2026')

        if not secret_token or secret_token != configured_secret:
            return Response({"error": "Unauthorized. Invalid secret token."}, status=status.HTTP_401_UNAUTHORIZED)

        out_reminders = StringIO()
        try:
            call_command('check_reminders', stdout=out_reminders)
        except Exception as e:
            out_reminders.write(f"Error: {e}\n")

        out_scheduled = StringIO()
        try:
            call_command('process_scheduled_transactions', stdout=out_scheduled)
        except Exception as e:
            out_scheduled.write(f"Error: {e}\n")

        return Response({
            "status": "success",
            "message": "Cron checks executed successfully.",
            "reminders_log": out_reminders.getvalue(),
            "scheduled_log": out_scheduled.getvalue()
        }, status=status.HTTP_200_OK)
