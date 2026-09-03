from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from account.api import UserRegistrationView, UserProfileView, DashboardSummaryView, GoogleLoginView, VapidPublicKeyView, PushSubscriptionView
from savings.api import PredefinedWalletListViewSet, WalletViewSet, SavingsViewSet, BalanceTransferView, LoanEntryViewSet, ScheduledTransactionViewSet
from income.api import IncomeRelatedViewSet, IncomesViewSet
from costs.api import CostRelatedViewSet, CostsViewSet

# Initialize the router for ViewSets
router = DefaultRouter()
router.register(r'predefined-wallets', PredefinedWalletListViewSet, basename='predefined-wallet')
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'savings', SavingsViewSet, basename='saving')
router.register(r'loans', LoanEntryViewSet, basename='loan')
router.register(r'scheduled-transactions', ScheduledTransactionViewSet, basename='scheduled-transaction')
router.register(r'income/categories', IncomeRelatedViewSet, basename='income-category')
router.register(r'income', IncomesViewSet, basename='income')
router.register(r'costs/categories', CostRelatedViewSet, basename='cost-category')
router.register(r'costs', CostsViewSet, basename='cost')

urlpatterns = [
    # JWT Authentication Endpoints
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', UserRegistrationView.as_view(), name='api_register'),
    path('auth/profile/', UserProfileView.as_view(), name='api_profile'),
    path('auth/google/', GoogleLoginView.as_view(), name='api_google_login'),
    path('auth/vapid-public-key/', VapidPublicKeyView.as_view(), name='api_vapid_public_key'),
    path('auth/push-subscription/', PushSubscriptionView.as_view(), name='api_push_subscription'),

    # Dashboard Endpoint
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='api_dashboard_summary'),

    # Balance Transfer Endpoint
    path('wallets/transfer/', BalanceTransferView.as_view(), name='api_wallet_transfer'),

    # ViewSet Router URLs
    path('', include(router.urls)),
]
