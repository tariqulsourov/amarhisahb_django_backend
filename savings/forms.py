from django import forms

from .models import SavingRelated, Savings, Wallet

class SavingsRelatedForm(forms.ModelForm):
    class Meta:
        model = SavingRelated
        fields = ['short_info','short_description','saving_where']

class SavingsForm(forms.ModelForm):
    class Meta:
        model = Savings
        fields = ['amount', 'description', 'wallet', 'saving_date']

class WalletForm(forms.ModelForm):
    class Meta:
        model = Wallet
        fields = ['wallet_name', 'wallet_info', 'wallet_number', 'wallet_status']

        