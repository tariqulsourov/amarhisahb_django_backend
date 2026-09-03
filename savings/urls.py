from django.urls import path, re_path

from savings.views import *

app_name = 'savings'

urlpatterns = [
    path('my-wallets/', UserSavingsList, name='my_savings'),
    path('search-savings/', SearchUserSavingsList, name='search_savings'),
    path('edit-saving/<int:id>,', editSavings, name='edit_saving'),
    path('delete-saving/<int:id>', deleteSavings, name='delete_saving'),
    path('edit-wallet/<int:id>,', editWallet, name='edit_wallet'),
    path('delete-wallet/<int:id>', deleteWallet, name='delete_wallet'),
    path('transfer-balance/', transferBalance, name='transfer_balance'),

    path('edit-wallet-name/<int:id>', edit_wallet_name, name='edit_wallet_name'),
    path('edit-wallet-amount/<int:id>', edit_wallet_amount, name='edit_wallet_amount'),
]