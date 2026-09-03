from django import forms

from .models import Incomes, IncomeRelated

class IncomeRelatedForm(forms.ModelForm):
    class Meta:
        model = IncomeRelated
        fields = ['short_info','short_description','income_source']

class IncomeForm(forms.ModelForm):
    class Meta:
        model = Incomes
        fields = ['amount', 'description', 'wallet', 'income_date']

        