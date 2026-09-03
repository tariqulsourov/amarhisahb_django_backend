# LEGACY VIEW FILE: Used only for old HTML templates. Safe to remove once fully transitioned to React.
from django.shortcuts import render, redirect
from django.db.models import Count, Sum
from django.contrib.auth.decorators import login_required
from income.forms import IncomeRelatedForm, IncomeForm
from income.models import Incomes, IncomeRelated
from account.models import UsersSettings
from costs.views import eachPageObject, create_first_last_date
from savings.models import MonthlyBalanceSummary
from datetime import datetime, date, timedelta
from savings.models import Wallet
from xhtml2pdf import pisa
import json
from django.http import HttpResponse
# Create your views here.
@login_required(login_url="/account/login/")
def UserIncomeList(request):
    if request.user.is_authenticated:
        # template_name = 'income/income_list.html'
        get_user_settings = UsersSettings.objects.get(user = request.user)
        if get_user_settings.prefered_view == 'mobile':
            template_name = 'income/income_list_mobile.html'
        else:
            template_name = 'income/income_list.html'
        income_related_form = IncomeRelatedForm
        income_form = IncomeForm
        if request.GET.get('date_to') == None and request.GET.get('date_from') == None:
            current_date = date.today()
        all_my_wallet = Wallet.objects.filter(wallet_of = request.user)
        first_date_of_this_month, last_date_of_this_month, prev_month_first_day, prev_month_last_day, next_month_first_day, next_month_last_day = create_first_last_date(current_date)
        all_income_list = Incomes.objects.filter(income_related_id__create_by_id = request.user.id, income_date__range = [first_date_of_this_month, last_date_of_this_month]).order_by('-income_date','-id')
        total_income_of_running_month = all_income_list.aggregate(the_count=Sum('amount'))
        all_income_related_by_this_user = IncomeRelated.objects.filter(create_by_id= request.user.id)

        if request.method == "POST":
            income_related_form = IncomeRelatedForm(request.POST)
            income_form = IncomeForm(request.POST)
            monthly_summary = MonthlyBalanceSummary()
            wallet = Wallet.objects.get(id = int(request.POST.get('wallet')))
            income_amount = int(request.POST.get('amount'))
            if request.POST.get('income_date') == None or request.POST.get('income_date') == '':
                income_date_status = date.today()
                today_date = income_date_status
            else:
                income_date_status = request.POST.get('income_date')
                today_date = datetime.strptime(income_date_status, '%Y-%m-%d')

            # new for monthly summery ------------------------------------
            year = today_date.year
            month = today_date.month
            if month == 2:
                try:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
                    last_date_of_running_month = datetime(year, month, 28)
                except:
                    last_date_of_running_month = datetime(year, month, 29)
            else:
                try:
                    last_date_of_running_month = datetime(year, month, 31)
                except:
                    last_date_of_running_month = datetime(year, month, 30)
            try:
                get_monthly_summary = MonthlyBalanceSummary.objects.get(user = request.user, last_date_of_month = last_date_of_running_month)
            except:
                get_monthly_summary = False
            all_my_wallet = Wallet.objects.filter(wallet_of = request.user)
            total_of_all_wallet = all_my_wallet.aggregate(the_count=Sum('wallet_status'))
            # new for monthly summery ------------------------------------

            if income_related_form.is_valid()==False and request.POST.get('select_short_info') != '':
                prev_income_related_info = request.POST.get('select_short_info')
                print(income_form)
                if income_form.is_valid():
                    income_form = income_form.save(commit=False)
                    income_form.income_related_id_id = int(prev_income_related_info)
                    income_form.income_date = income_date_status
                    print(income_form.income_related_id_id)
                    print(income_form)
                    income_form.save()
                    wallet.wallet_status = wallet.wallet_status + income_amount
                    wallet.save()
                    # new for monthly summery ------------------------------------
                    if get_monthly_summary:
                        get_monthly_summary.total_balance = get_monthly_summary.total_balance + int(request.POST.get('amount'))
                        get_monthly_summary.save()
                    else:
                        monthly_summary.total_balance = int(total_of_all_wallet['the_count']) + int(request.POST.get('amount'))
                        monthly_summary.last_date_of_month = last_date_of_running_month
                        monthly_summary.user = request.user
                        monthly_summary.save()
                    # new for monthly summery ------------------------------------
                    
            else:
                if income_related_form.is_valid():
                    income_related_form = income_related_form.save(commit=False)
                    income_related_form.create_by_id = int(request.user.id)
                    print(income_related_form.create_by_id)
                    income_related_form.save()

                    last_entry_by_this_user = IncomeRelated.objects.filter(create_by = request.user, short_info=income_related_form.short_info).latest('created_at')
                    print(income_form)
                    if income_form.is_valid():
                        income_form = income_form.save(commit=False)
                        income_form.income_related_id_id = int(last_entry_by_this_user)
                        income_form.income_date = income_date_status
                        print(income_form.income_related_id_id)
                        print(income_form)
                        income_form.save()
                        wallet.wallet_status = wallet.wallet_status + income_amount
                        wallet.save()
                        # new for monthly summery ------------------------------------
                        if get_monthly_summary:
                            get_monthly_summary.total_balance = get_monthly_summary.total_balance + int(request.POST.get('amount'))
                            get_monthly_summary.save()
                        else:
                            monthly_summary.total_balance = int(total_of_all_wallet['the_count']) + int(request.POST.get('amount'))
                            monthly_summary.last_date_of_month = last_date_of_running_month
                            monthly_summary.user = request.user
                            monthly_summary.save()
                        # new for monthly summery ------------------------------------
            return redirect('income:my_income')

        print(type(prev_month_first_day))

        obj_per_page = 31 # number of items to be shown per page
        per_page_link = 5    # number of buttons in pagination
        context = eachPageObject(request, all_income_list, obj_per_page, per_page_link)
        context['all_my_wallet'] = all_my_wallet
        context['all_income_related']=all_income_related_by_this_user
        context['total']=total_income_of_running_month['the_count']
        context['today_date']=date.today()
        context['prev_month_first_date'] = str(prev_month_first_day)
        context['prev_month_last_date'] = str(prev_month_last_day)
        context['next_month_first_date'] = str(next_month_first_day)
        context['next_month_last_date'] = str(next_month_last_day)
        context['current_month'] = datetime.strftime(datetime.strptime(str(current_date), '%Y-%m-%d'), '%m-%Y')
        print(context)

        return render(request, template_name, context)

    else:
        return redirect('account:login_page')

def editIncome(request,id):
    if request.user.is_authenticated:
        template_name = 'income/edit_income.html'
        get_this_income_data = Incomes.objects.get(id=id)
        get_this_related_data = IncomeRelated.objects.get(id=get_this_income_data.income_related_id)
        all_income_related = IncomeRelated.objects.filter(create_by_id= request.user.id)
        the_wallet = Wallet.objects.get(id = get_this_income_data.wallet_id)
        if request.method == 'POST':
            print(request.POST.get('income_date'))
            # get_this_related_data.short_info = request.POST.get('select_short_info')
            # get_this_related_data.short_description = request.POST.get('short_description')
            # get_this_related_data.income_source = request.POST.get('income_source')
            get_this_income_data.income_related_id_id = int(request.POST.get('select_short_info'))
            the_wallet.wallet_status = (int(get_this_income_data.wallet.wallet_status) - int(get_this_income_data.amount)) + int(request.POST.get('amount'))
            get_this_income_data.description = request.POST.get('description')
            get_this_income_data.amount = request.POST.get('amount')
            if request.POST.get('income_date') == None or request.POST.get('income_date') == '':
                pass
            else:
                get_this_income_data.income_date = request.POST.get('income_date')

            the_wallet.save()
            get_this_income_data.save()

            return redirect('income:my_income')
        
        context ={
            "this_income_related_data": get_this_related_data,
            "this_income_data": get_this_income_data,
            "all_income_related": all_income_related
        }
        return render(request, template_name, context)
    else:
        return redirect('account:login_page')

def deleteIncome(request,id):
    
    get_this_income_data = Incomes.objects.get(id=id)
    the_wallet = Wallet.objects.get(id = get_this_income_data.wallet_id)
    the_wallet.wallet_status = (int(get_this_income_data.wallet.wallet_status) - int(get_this_income_data.amount))
    get_this_related_data = IncomeRelated.objects.get(id=get_this_income_data.income_related_id)

    the_wallet.save()
    # get_this_related_data.delete()
    get_this_income_data.delete()

    return redirect('income:my_income')


def SearchUserIncomeList(request):
    if request.user.is_authenticated:
        get_user_settings = UsersSettings.objects.get(user = request.user)
        if get_user_settings.prefered_view == 'mobile':
            template_name = 'income/income_list_mobile.html'
        else:
            template_name = 'income/income_list.html'
        income_related_form = IncomeRelatedForm
        income_form = IncomeForm
        all_my_wallet = Wallet.objects.filter(wallet_of = request.user)
        if request.GET.get('date_to') == None and request.GET.get('date_from') == None:
            current_date = datetime.today()
        elif request.GET.get('date_from') == '' and request.GET.get('date_to') == '':
            current_date = datetime.today()
        elif request.GET.get('date_from') == '':
            current_date = datetime.strptime(request.GET.get('date_to'), '%Y-%m-%d')
        elif request.GET.get('date_to') == '':
            current_date = datetime.strptime(request.GET.get('date_from'), '%Y-%m-%d')
        else:
            current_date = datetime.strptime(request.GET.get('date_to'), '%Y-%m-%d')

        first_date_of_this_month, last_date_of_this_month, prev_month_first_day, prev_month_last_day, next_month_first_day, next_month_last_day = create_first_last_date(current_date)
        search_income_title = request.GET.get('income_title', '')
        search_income_field = request.GET.get('income_field', '')
        if request.GET.get('date_from') == '':
            search_date_from = datetime.strptime('2022-01-01', '%Y-%m-%d')
        else:
            search_date_from = datetime.strptime(request.GET.get('date_from'), '%Y-%m-%d')
        if request.GET.get('date_to') == '':
            search_date_to = date.today()
        else:
            search_date_to = datetime.strptime(request.GET.get('date_to'), '%Y-%m-%d')

        if request.GET.get('wallet') == '' or request.GET.get('wallet') == None:
            all_income_list = Incomes.objects.filter(income_related_id__create_by_id = request.user.id, income_related_id__short_info__icontains = search_income_title, income_related_id__income_source__icontains = search_income_field , income_date__range = [search_date_from, search_date_to]).order_by('-income_date','-id')
        else:
            all_income_list = Incomes.objects.filter(income_related_id__create_by_id = request.user.id, income_related_id__short_info__icontains = search_income_title, income_related_id__income_source__icontains = search_income_field , income_date__range = [search_date_from, search_date_to], wallet_id = request.GET.get('wallet')).order_by('-income_date','-id')
        total_income_of_running_month = all_income_list.aggregate(the_count=Sum('amount'))
        print(total_income_of_running_month['the_count'])
        all_income_related_by_this_user = IncomeRelated.objects.filter(create_by_id= request.user.id)

        if request.method == "POST":
            income_related_form = IncomeRelatedForm(request.POST)
            income_form = IncomeForm(request.POST)
            wallet = Wallet.objects.get(id = int(request.POST.get('wallet')))
            income_amount = int(request.POST.get('amount'))
            if request.POST.get('income_date') == None or request.POST.get('income_date') == '':
                income_date_status = date.today()
            else:
                income_date_status = request.POST.get('income_date')

            if income_related_form.is_valid()==False and request.POST.get('select_short_info') != '':
                prev_income_related_info = request.POST.get('select_short_info')
                print(income_form)
                if income_form.is_valid():
                    income_form = income_form.save(commit=False)
                    income_form.income_related_id_id = int(prev_income_related_info)
                    income_form.income_date = income_date_status
                    print(income_form.income_related_id_id)
                    print(income_form)
                    income_form.save()
                    wallet.wallet_status = wallet.wallet_status + income_amount
                    wallet.save()
            else:
                if income_related_form.is_valid():
                    income_related_form = income_related_form.save(commit=False)
                    income_related_form.create_by_id = int(request.user.id)
                    print(income_related_form.create_by_id)
                    income_related_form.save()

                    last_entry_by_this_user = IncomeRelated.objects.filter(create_by = request.user, short_info=income_related_form.short_info).latest('created_at')
                    print(income_form)
                    if income_form.is_valid():
                        income_form = income_form.save(commit=False)
                        income_form.income_related_id_id = int(last_entry_by_this_user)
                        income_form.income_date = income_date_status
                        print(income_form.income_related_id_id)
                        print(income_form)
                        income_form.save()
                        wallet.wallet_status = wallet.wallet_status + income_amount
                        wallet.save()

            return redirect('income:my_income')
        full_url = request.GET
        obj_per_page = 100 # number of items to be shown per page
        per_page_link = 5    # number of buttons in pagination
        context = eachPageObject(request, all_income_list, obj_per_page, per_page_link)
        context['all_my_wallet'] = all_my_wallet
        context['all_income_related']=all_income_related_by_this_user
        context['total']=total_income_of_running_month['the_count']
        context['today_date']=date.today()
        context['prev_month_first_date'] = str(prev_month_first_day)
        context['prev_month_last_date'] = str(prev_month_last_day)
        context['next_month_first_date'] = str(next_month_first_day)
        context['next_month_last_date'] = str(next_month_last_day)
        context['current_month'] = datetime.strftime(datetime.strptime(str(current_date.date()), '%Y-%m-%d'), '%m-%Y')
        context['request_parameter']=full_url
        print(context)

        return render(request, template_name, context)
    else:
        return redirect('account:login_page')

def getIncomeGraphData(request):
    if request.GET.get('date_to') == None and request.GET.get('date_from') == None:
        current_date = date.today()

    first_date_of_this_month, last_date_of_this_month, prev_month_first_day, prev_month_last_day, next_month_first_day, next_month_last_day = create_first_last_date(current_date)
    all_cost_list = Incomes.objects.filter(income_related_id__create_by_id = request.user.id, income_date__range = [first_date_of_this_month, last_date_of_this_month]).order_by('-income_date', '-id')

    queryset = all_cost_list.values('income_related_id').annotate(count_sector_cnt=Sum('amount')).order_by('-count_sector_cnt')[:5]
    result = queryset.values('income_related_id', 'count_sector_cnt')
    print(result)
    graph_data = {}
    for each_result in result:
        cost_sector_id = each_result['income_related_id']
        count = each_result['count_sector_cnt']
        cost_sector = IncomeRelated.objects.get(id = cost_sector_id).short_info
        print(cost_sector)
        graph_data[cost_sector]={
            'income_count': count
        }

    json_data = json.dumps(graph_data)
    print(json_data)
    return HttpResponse(json_data, content_type = 'application/json')