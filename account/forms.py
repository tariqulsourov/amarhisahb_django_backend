from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate

import re

from account.models import *
from django.forms.widgets import DateInput


from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class AdminRegistrationForm(UserCreationForm):

    def __init__(self, *args, **kwargs):
        super(AdminRegistrationForm, self).__init__(*args, **kwargs)

        self.fields['first_name'].required = True
        self.fields['email'].required = True
        self.fields['password1'].required = True
        self.fields['password2'].required = True

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2', 'phone']

        error_messages = {
             'first_name': {
                'required': 'Name is required',
            },
            'email': {
                'required': 'email is required.'
            },
            'password1': {
                'required': 'Password is required.'
            },
            'password2': {
                'required': 'Confirm password is required.'
            },
        }

    def passwordMatching(self, *args, **kwargs):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 != password2:
            raise forms.ValidationError('password missmatchd')
        else:
            pass

    def save(self, commit=True):
        user = super(AdminRegistrationForm, self).save(commit=False)
        user.user_type = UserType.objects.get(user_type='admin')
        if commit:
            user.save()
        return user

class UserRegistrationForm(UserCreationForm):

    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)

        self.fields['first_name'].required = True
        self.fields['email'].required = True
        self.fields['password1'].required = True
        self.fields['password2'].required = True

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2', 'phone']

        error_messages = {
             'first_name': {
                'required': 'Name is required',
            },
            'email': {
                'required': 'email is required.'
            },
            'password1': {
                'required': 'Password is required.'
            },
            'password2': {
                'required': 'Confirm password is required.'
            },
        }

    def passwordMatching(self, *args, **kwargs):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 != password2:
            raise forms.ValidationError('password missmatched')
        else:
            pass

    def save(self, commit=True):
        user = super(UserRegistrationForm, self).save(commit=False)
        user.user_type = UserType.objects.get(user_type='regular_user')
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(
        label= "Password",
        strip=False,
        widget=forms.PasswordInput,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.fields['email'].widget.attrs.update({'placeholder': 'Please enter Email'})
        self.fields['password'].widget.attrs.update({'placeholder': 'Please enter Password'})
        
    def clean(self, *args, **kwargs):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        print(email)
        print(password)

        if email and password:
            self.user = authenticate(email= email, password= password)

            if self.user is None:
                raise forms.ValidationError("Email or password is invalid")
            if not self.user.check_password(password):
                raise forms.ValidationError("Password does not match")
            if not self.user.is_active:
                raise forms.ValidationError("User is not active")

        return super(LoginForm, self).clean(*args, **kwargs)

    def get_user(self):
        return self.user