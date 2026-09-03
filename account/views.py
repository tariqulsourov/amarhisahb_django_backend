# LEGACY VIEW FILE: Used only for old HTML templates. Safe to remove once fully transitioned to React.
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic import ListView, CreateView, FormView, RedirectView
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.core.paginator import Paginator
from django.contrib import messages, auth
from django.db.models import Q, Sum
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
# from requests import request

from account.models import *
from account.forms import *

from datetime import datetime, date, time, timezone, timedelta
from savings.models import PredefinedWalletList, Wallet, MonthlyBalanceSummary
from costs.models import CostRelated, Costs
from income.models import Incomes, IncomeRelated
import json
import calendar
# Create your views here.

def testFn(request):
    return render(request, 'income/income_list_mobile.html', {})

@login_required(login_url="/account/login/")
def home(request):
    create_user_type()
    admin_register()
    create_predefined_wallet()
    if request.user.is_authenticated:
        return redirect('account:user_dashboard')
    else:
        return render(request, 'home.html', {})

def create_predefined_wallet():
    table = PredefinedWalletList()
    wallet_data = PredefinedWalletList.objects.all()
    wallet_list = ['my-wallet',
                    'ab-bank',
                    'aibl',
                    'basic',
                    'bcb',
                    'bkash',
                    'brac',
                    'city',
                    'dbbl',
                    'ebl',
                    'fsib',
                    'hsbc',
                    'ibbl',
                    'ibbl-m',
                    'ific',
                    'nagad',
                    'one-bank',
                    'rocket',
                    'southeast',
                    'standard',
                    'ucb',
                    'union',
                    'uttara',
                    ]
    wallet_img_ext = '.png'
    if len(wallet_data) == 0:
        print('blank wallet')
        for wallet in wallet_list:
            obj = PredefinedWalletList()
            obj.name = wallet
            obj.image = wallet + wallet_img_ext
            # obj.created_at = date.today()
            # obj.updated_at = date.today()
            obj.save()
            print('wallet created')

def create_user_type():
    table = UserType()
    usertype_table_data = UserType.objects.all()
    if len(usertype_table_data) == 0:
        obj = UserType()
        obj.id = 1
        obj.user_type = 'admin'
        obj.created_at = date.today()
        obj.updated_at = date.today
        obj.save()
        print('obj created')

        obj = UserType()
        obj.id = 2
        obj.user_type = 'regular_user'
        obj.created_at = date.today()
        obj.updated_at = date.today
        obj.save()

def admin_register():
    table = User()
    user_table_data = User.objects.all()
    if len(user_table_data) == 0:
        obj = User()
        obj.id = 1
        obj.first_name = 'Tariqul'
        obj.password = make_password('29910171Oct')
        obj.last_name = ''
        obj.is_superuser = 1
        obj.is_staff = 1
        obj.is_active = 1
        obj.date_joined = date.today()
        obj.email = 'tariqulislamsourov@gmail.com'
        obj.phone = '+8801986395483'
        obj.updated_at = date.today()
        obj.user_type = UserType.objects.get(user_type='admin', id=1)
        obj.save()
@login_required(login_url="/account/login/")
def userDashboard(request):
    try:
        get_user_settings = UsersSettings.objects.get(user = request.user)
        if get_user_settings.prefered_view == 'mobile':
            template_name = 'mb_user_dashboard.html'
        else:
            template_name = 'user_dashboard.html'
    except:
        get_user_settings = False
        template_name = 'mb_user_dashboard.html'

    wallets = Wallet.objects.filter(wallet_of = request.user)

    if get_user_settings is False:
        the_obj = UsersSettings()
        the_obj.user = request.user
        the_obj.prefered_view = 'mobile'
        the_obj.using_hand = 'right'
        the_obj.save()
        get_user_settings = UsersSettings.objects.get(user = request.user)

    all_my_wallet = Wallet.objects.filter(wallet_of = request.user)
    total_of_all_wallet = all_my_wallet.aggregate(the_count=Sum('wallet_status'))
    wallet_balance = total_of_all_wallet['the_count']
    print(wallets)
    context = {'user_settings': get_user_settings,
                'wallets': wallets,
                'wallet_balance': wallet_balance}
    return render(request, template_name, context)


def get_total_amounts_dash(request):

    wallet_id = request.GET.get('wallet')
    month = request.GET.get('month')

    if month == '':
        today_date = date.today()
        year, month = today_date.year, today_date.month
        first_date_of_this_month = datetime(year, month, 1).date()
        last_date_of_this_month = today_date    # not last but todays date

    else:
        month = request.GET.get('month').split('-')
        year, month = int(month[0]), int(month[1])
        first_date_of_this_month = datetime(year, month, 1).date()
        if month == 2:
            try:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
                last_date_of_this_month = datetime(year, month, 28).date()
            except:
                last_date_of_this_month = datetime(year, month, 29).date()
        else:
            try:
                last_date_of_this_month = datetime(year, month, 31).date()
            except:
                last_date_of_this_month = datetime(year, month, 30).date()
        print(first_date_of_this_month)
        print(last_date_of_this_month)

    if wallet_id == '':
        all_my_wallet = Wallet.objects.filter(wallet_of = request.user)
        total_of_all_wallet = all_my_wallet.aggregate(the_count=Sum('wallet_status'))
        wallet_balance = total_of_all_wallet['the_count']
        total_cost_row = Costs.objects.filter(cost_related_id__create_by_id = request.user.id, cost_date__range = [first_date_of_this_month, last_date_of_this_month]).aggregate(the_count=Sum('amount'))
        total_income_row = Incomes.objects.filter(income_related_id__create_by_id = request.user.id, income_date__range = [first_date_of_this_month, last_date_of_this_month]).aggregate(the_count=Sum('amount'))
    else:
        wallet_balance = Wallet.objects.get(id = wallet_id).wallet_status
        total_cost_row = Costs.objects.filter(cost_related_id__create_by_id = request.user.id, cost_date__range = [first_date_of_this_month, last_date_of_this_month], wallet_id = wallet_id).aggregate(the_count=Sum('amount'))
        total_income_row = Incomes.objects.filter(income_related_id__create_by_id = request.user.id, income_date__range = [first_date_of_this_month, last_date_of_this_month], wallet_id = wallet_id).aggregate(the_count=Sum('amount'))
    total_cost = total_cost_row['the_count']
    total_income = total_income_row['the_count']
    summary = {
        "wallet_balance": wallet_balance,
        "total_cost": total_cost,
        "total_income": total_income
    }
    json_data = json.dumps(summary)
    
    return HttpResponse(json_data, content_type="application/json")


def get_month_name(number):
    month_number = number  # For example, March

    month_name = calendar.month_name[month_number]

    return month_name

def getGraphData(request):

    today_date = date.today()
    year, month = today_date.year, today_date.month
    first_date_of_this_month = datetime(year, month, 1).date()
    last_date_of_this_month = today_date    # not last but todays date

    joining_date = request.user.date_joined
    joining_date = joining_date.date()
    print(joining_date.month)
    print(first_date_of_this_month.month)
    delta = (first_date_of_this_month.year - joining_date.year) * 12 + (first_date_of_this_month.month - joining_date.month)
    # number_of_month = int(delta)
    print(delta)
    if delta > 6:
        delta = 6
    # print(number_of_month)
    formated_month = f'{month:02}'
    year_month_combination = str(year)+'-'+str(formated_month)
    current_month_total_cost_row = Costs.objects.filter(cost_related_id__create_by_id = request.user.id, cost_date__range = [first_date_of_this_month, last_date_of_this_month]).aggregate(the_count=Sum('amount'))
    current_month_total_income_row = Incomes.objects.filter(income_related_id__create_by_id = request.user.id, income_date__range = [first_date_of_this_month, last_date_of_this_month]).aggregate(the_count=Sum('amount'))
    try:
        get_current_month_accounts_summary = MonthlyBalanceSummary.objects.get(user=request.user, last_date_of_month__icontains = year_month_combination)
    except:
        get_current_month_accounts_summary.total_balance = 0
    graph_data = {}
    # print(get_current_month_accounts_summary.last_date_of_month)
    # print(today_date)
    graph_data['month_1'] = {
        "month": get_month_name(first_date_of_this_month.month),
        "cost": current_month_total_cost_row['the_count'],
        "income": current_month_total_income_row['the_count'],
        "summary": get_current_month_accounts_summary.total_balance
    }
    print(graph_data)

    for i in range(1, delta):
        
        first_prev_month_last_day = first_date_of_this_month - timedelta(days=1)
        first_prev_month_first_day = first_prev_month_last_day.replace(day=1)

        first_date_of_this_month = first_prev_month_first_day

        print(first_prev_month_last_day)
        first_prev_month_total_cost_row = Costs.objects.filter(cost_related_id__create_by_id = request.user.id, cost_date__range = [first_prev_month_first_day, first_prev_month_last_day]).aggregate(the_count=Sum('amount'))
        first_prev_month_total_income_row = Incomes.objects.filter(income_related_id__create_by_id = request.user.id, income_date__range = [first_prev_month_first_day, first_prev_month_last_day]).aggregate(the_count=Sum('amount'))
        final_balance_amount = 0
        try:
            get_first_prev_month_accounts_summary = MonthlyBalanceSummary.objects.get(user=request.user, last_date_of_month__icontains = first_prev_month_last_day)
            final_balance_amount = get_first_prev_month_accounts_summary.total_balance
        except:
            final_balance_amount = 0
        graph_data[f'month_{i+1}'] = {
            "month": get_month_name(first_prev_month_first_day.month),
            "cost": first_prev_month_total_cost_row['the_count'],
            "income": first_prev_month_total_income_row['the_count'],
            "summary": final_balance_amount
        }

    json_data = json.dumps(graph_data)
    print(json_data)

    return HttpResponse(json_data, content_type="application/json")

def deviceView(request):
    if request.method == "POST":
        get_user_settings = UsersSettings.objects.get(user = request.user)
        data = request.POST.get('screen_size')
        print(data)
        if data == None:
            get_user_settings.prefered_view = 'desktop'
            get_user_settings.save()
        elif data == 'on':
            get_user_settings.prefered_view = 'mobile'
            get_user_settings.save()

    return redirect('account:user_dashboard')

def useingHand(request):
    if request.method == "POST":
        get_user_settings = UsersSettings.objects.get(user = request.user)
        data = request.POST.get('prefered_hand')
        print(data)
        if data == None:
            get_user_settings.using_hand = 'left'
            get_user_settings.save()
        elif data == 'on':
            get_user_settings.using_hand = 'right'
            get_user_settings.save()

    return redirect('account:user_dashboard')

def userResister(request):
    template = 'account/user_register.html'
    form = UserRegistrationForm

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        print(form)
        try:
            if form.is_valid():
                print('form is valid')
                user = form.save(commit=False)                          ##----------- commit=false gets and model and make the form(with data)
                                                                            ##----------- editable and change the data into form
                password = form.cleaned_data.get('password1')
                
                user.set_password(password)
                user.is_superuser = False
                user.is_staff = False
                
                user.save()
                return redirect('account:login_page')        ##---------- redirect to admin dashboard if successful
            else:
                return render(request, 'account/user_register.html', {'form':form})
        except Exception as e:
            print(e)

    return render(request, template, {})


class LoginView(FormView):                                           ##----------- View function for login. Extending Django FormView class
    # admin_success_url= '/costs/my-costs/'               ##----------- success url if logged in as user_type == admin
    # regular_user_success_url= '/costs/my-costs/'
    admin_success_url= '/account/user-dashboard/'
    regular_user_success_url= '/account/user-dashboard/'
    # doctor_success_url= '/doctor/dashboard/'
    # manager_success_url= '/manager/dashboard/'
    # general_staff_success_url= '/staff/dashboard/'
    general_success_url= '/'                                         ##----------- if user type is undefined


    form_class = LoginForm
    template_name = "account/login.html"

    extra_context = {
        'title': 'Login'
    }
    # user_role = UserType.objects.get(user_type='admin')

    def dispatch(self, request, *args, **kwargs):                     ##----------- Track and redirect as the requisting user is authenticated 
        if self.request.user.is_authenticated:
            return redirect(self.get_success_url())                   ##----------- if authenticated redirect to success url as user_type
        return super().dispatch(self.request, *args, **kwargs)        ##----------- if not authenticated redirect to login page

    def get_success_url(self):                                        ##----------- finds the correct success url as user_type
        if 'next' in self.request.GET and self.request.GET['next'] != '':
            return self.request.GET['next'] 

        else:
            if self.request.user.user_type == UserType.objects.get(user_type='admin'):                ##----------- if admid return the admin dashboard
                print(self.request.user.user_type)
                return self.admin_success_url
            if self.request.user.user_type == UserType.objects.get(user_type='regular_user'):                ##----------- if client return the client dashboard
                print(self.request.user.user_type)
                return self.regular_user_success_url
            # if self.request.user.user_type == UserType.objects.get(user_type='doctor'):                ##----------- if doctor return the doctor dashboard
            #     print(self.request.user.user_type)
            #     return self.doctor_success_url
            # if self.request.user.user_type == UserType.objects.get(user_type='manager'):                ##----------- if manger return the manager dashboard
            #     print(self.request.user.user_type)
            #     return self.manager_success_url
            # if self.request.user.user_type == UserType.objects.get(user_type='general_staff'):                ##----------- if general_staff return the general_staff dashboard
            #     print(self.request.user.user_type)
            #     return self.general_staff_success_url
            else:
                print(self.request.user.user_type)
                return self.general_success_url


    def get_form_class(self):                                         ##----------- get the form of this class
        print(self.form_class(data=self.request.POST))
        return self.form_class

    def form_valid(self, form):                                       ##----------- if submited form is valid get the user and call success_url
        print("valid Form")
        auth.login(self.request, form.get_user())

        # write_log(self.request, self.request.user, "Logged In", CHANGE)

        return redirect(self.get_success_url())

    def form_invalid(self, form):
        print("invalid form")
        return self.render_to_response(self.get_context_data(form=form)) ##------ if submited form is invalid load the form again

    # return render(request, 'login.html', {})

class LogoutView(RedirectView):                                          ##------ Control if user is logging out

    url = '/account/login/'                                                      ##------ url after logout

    def get(self, request, *args, **kwargs):

        # write_log(self.request, self.request.user, "Logged Out", CHANGE)

        auth.logout(request)
        print('Logged out')
        print(request.user)
        messages.success(request, "You are logged out")
        return super(LogoutView, self).get(request, *args, **kwargs)



def passwordReset(request):                                              ##-------- This function is to reset passwod
    if request.method == 'POST':
        email = request.POST.get('email')
        pass1= request.POST.get('password1')
        pass2= request.POST.get('password2')
        # print(email)
        try: 
            email= User.objects.get(email=email)
            if email:                                                    ##-------- Checking if the given email is into user table (registered)
                if pass1 == pass2:                                       ##-------- confirming the new password
                    email.set_password(pass1)                            ##-------- set new password
                    email.save()                                         ##-------- save the password
            return redirect('login_page')                                ## ------- after successful reset redirect to login page
        except Exception as e:
            print(e)
            context = {'message':"You are not registered"}
            return render(request, 'reset_password.html', context)      ##--------- if given email is wrong render with message
    return render(request, 'reset_password.html', {})


def cashFlowSourceList(request):
    template = 'account/cash-flow-source.html'
    get_all_cost_cash_flow_sources = CostRelated.objects.filter(create_by=request.user)
    get_all_cost_income_flow_sources = IncomeRelated.objects.filter(create_by=request.user)
    context = {
        'cash_flow_sources_for_cost': get_all_cost_cash_flow_sources,
        'cash_flow_sources_for_income': get_all_cost_income_flow_sources
    }
    return render(request, template, context)

def editCostSource(request, id):
    source = CostRelated.objects.get(id = id)
    source.short_info = request.POST.get('cost_source_edit')
    source.save()
    return redirect('account:my_cash_flow_source')

def deleteCostSource(request, id):
    source = CostRelated.objects.get(id = id)
    source.delete()
    return redirect('account:my_cash_flow_source')

def editIncomeSource(request, id):
    source = IncomeRelated.objects.get(id = id)
    source.short_info = request.POST.get('income_source_edit')
    source.save()
    return redirect('account:my_cash_flow_source')

def deleteIncomeSource(request, id):
    source = IncomeRelated.objects.get(id = id)
    source.delete()
    return redirect('account:my_cash_flow_source')