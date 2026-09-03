# ACTIVE REST API VIEWS: Required for the new React frontend and Mobile application.
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum
from datetime import date, datetime, timedelta

from account.models import User, UsersSettings, PushSubscription
from account.serializers import UserSerializer, UserRegistrationSerializer, UsersSettingsSerializer
from account.vapid import get_vapid_public_key_b64
from savings.models import Wallet, MonthlyBalanceSummary
from costs.models import Costs
from income.models import Incomes

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
        
        settings_data = data.get('settings', {})
        settings_obj.prefered_view = settings_data.get('prefered_view', settings_obj.prefered_view)
        settings_obj.using_hand = settings_data.get('using_hand', settings_obj.using_hand)
        settings_obj.reminder_time = settings_data.get('reminder_time', settings_obj.reminder_time)
        settings_obj.reminder_enabled = settings_data.get('reminder_enabled', settings_obj.reminder_enabled)
        settings_obj.save()

        serializer = UserSerializer(user)
        return Response(serializer.data)


class VapidPublicKeyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        public_key = get_vapid_public_key_b64()
        return Response({"public_key": public_key})


class PushSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        endpoint = request.data.get('endpoint')
        keys = request.data.get('keys', {})
        p256dh = keys.get('p256dh')
        auth = keys.get('auth')

        if not all([endpoint, p256dh, auth]):
            return Response(
                {"error": "endpoint, keys.p256dh, and keys.auth are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update or create the subscription for the user
        PushSubscription.objects.update_or_create(
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

        # Return combined payload
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
            "graph_data": graph_data
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

