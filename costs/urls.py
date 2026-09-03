from django.urls import path, re_path

from costs.views import *

app_name = 'costs'

urlpatterns = [
    path('my-costs/', UserCostList, name='my_costs'),
    path('search-costs/', SearchUserCostList, name='search_costs'),
    path('edit-cost/<int:id>', editCost, name='edit_cost'),
    path('delete-cost/<int:id>', deleteCost, name='delete_cost'),
    path('download-cost/', downloadCost, name='download_cost'),
    path('get-cost-graph-data/', getCostGraphData, name = 'get_cost_graph_data'),

]