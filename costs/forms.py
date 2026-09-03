from django import forms

from .models import Costs, CostRelated

class CostRelatedForm(forms.ModelForm):
    class Meta:
        model = CostRelated
        fields = ['short_info','short_description','cost_field']

class CostForm(forms.ModelForm):
    class Meta:
        model = Costs
        fields = ['amount', 'description', 'wallet', 'cost_date']

        