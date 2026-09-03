from django.contrib import admin
from django.urls import path,re_path, include

from account.views import *
app_name = 'account'

urlpatterns = [
    
    path('login/', LoginView.as_view(), name='login_page'),
    path('logout/', LogoutView.as_view(), name='logout' ),
    path('register-user/', userResister, name='register_user'),
    path('user-dashboard/', userDashboard, name='user_dashboard'),
    path('device-view-choice/', deviceView, name='device_view_choice'),
    path('using-hand-choice/', useingHand, name= 'using_hand_choice'),
    path('get-wallet-amounts-dash/', get_total_amounts_dash, name = 'get_wallet_amounts_dahs'),
    path('get-graph-data/', getGraphData, name = 'get_graph_data'),
    path('cash-flow-source/', cashFlowSourceList, name='my_cash_flow_source'),
    path('edit-cost-source/<int:id>', editCostSource, name='edit_cost_source'),
    path('edit-income-source/<int:id>', editIncomeSource, name='edit_income_source'),
    path('delete-cost-source/<int:id>', deleteCostSource, name='delete_cost_source'),
    path('delete-income-source/<int:id>', deleteIncomeSource, name='delete_income_source'),
]