from django.urls import path, re_path

from income.views import *

app_name = 'income'

urlpatterns = [
    path('my-income/', UserIncomeList, name='my_income'),
    path('search-incmes/', SearchUserIncomeList, name='search_incomes'),
    path('edit-income/<int:id>', editIncome, name='edit_income'),
    path('delete-income/<int:id>', deleteIncome, name='delete_income'),
    path('get-cost-graph-data/', getIncomeGraphData, name = 'get_income_graph_data'),
]