# LEGACY VIEW FILE: Used only for old HTML templates. Safe to remove once fully transitioned to React.
from django.shortcuts import render, redirect
from django.db.models import Count, Sum
from costs.forms import CostRelatedForm, CostForm
from django.core.paginator import Paginator
from costs.models import Costs, CostRelated
from datetime import datetime, date, timedelta
from savings.models import Wallet
from account.models import UsersSettings
from savings.models import MonthlyBalanceSummary
from django.http import HttpResponse
from xhtml2pdf import pisa
import json
# Create your views here.

def eachPageObject(request, obj_list, obj_per_page, per_page_link):

    paginator = Paginator(obj_list, obj_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'pagination_data_list': page_obj, 
        'per_page_objects': obj_per_page, 
        'per_page_link': per_page_link
    }

    return context

def create_first_last_date(current_date):
    # current_date = date.today()
    year = current_date.year
    month = current_date.month

    first_date_of_this_month = datetime(year, month, 1)
    prev_month_last_day = first_date_of_this_month - timedelta(days=1)
    prev_month_first_day = prev_month_last_day.replace(day=1)
    if current_date.month == 2:
        try:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
            last_date_of_this_month = datetime(year, month, 28)
        except:
            last_date_of_this_month = datetime(year, month, 29)
    else:
        try:
            last_date_of_this_month = datetime(year, month, 31)
        except:
            last_date_of_this_month = datetime(year, month, 30)
    print(current_date.month)

    next_month_first_day = last_date_of_this_month + timedelta(days=1)
    add_day_to_next_month = next_month_first_day.replace(day=28) + timedelta(days=4)
    next_month_last_day = add_day_to_next_month - timedelta(days=add_day_to_next_month.day)

    print(first_date_of_this_month.date())
    print(last_date_of_this_month)
    print(prev_month_first_day)
    print(prev_month_last_day)
    print(next_month_first_day)
    print(next_month_last_day)


    return first_date_of_this_month.date(), last_date_of_this_month.date(), prev_month_first_day.date(), prev_month_last_day.date(), next_month_first_day.date(), next_month_last_day.date()

def UserCostList(request):
    if request.user.is_authenticated:
        get_user_settings = UsersSettings.objects.get(user = request.user)
        if get_user_settings.prefered_view == 'mobile':
            template_name = 'costs/cost_list_mobile.html'
        else:
            template_name = 'costs/cost_list.html'
        cost_related_form = CostRelatedForm
        cost_form = CostForm
        if request.GET.get('date_to') == None and request.GET.get('date_from') == None:
            current_date = date.today()

        first_date_of_this_month, last_date_of_this_month, prev_month_first_day, prev_month_last_day, next_month_first_day, next_month_last_day = create_first_last_date(current_date)
        all_my_wallet = Wallet.objects.filter(wallet_of = request.user)
        all_cost_list = Costs.objects.filter(cost_related_id__create_by_id = request.user.id, cost_date__range = [first_date_of_this_month, last_date_of_this_month]).order_by('-cost_date', '-id')
        total_cost_of_running_month = all_cost_list.aggregate(the_count=Sum('amount'))
        print(total_cost_of_running_month['the_count'])
        all_cost_related_by_this_user = CostRelated.objects.filter(create_by_id= request.user.id)

        if request.method == "POST":
            cost_related_form = CostRelatedForm(request.POST)
            cost_form = CostForm(request.POST)
            monthly_summary = MonthlyBalanceSummary()
            wallet = Wallet.objects.get(id = int(request.POST.get('wallet')))
            cost_amount = int(request.POST.get('amount'))
            print("-------------")

            # cost_form = cost_form.save(commit=False)
            if request.POST.get('cost_date') == None or request.POST.get('cost_date') == '':
                cost_date_status = date.today()
                print('inside none')
                print(cost_date_status)
                today_date = cost_date_status
            else:
                cost_date_status = request.POST.get('cost_date')
                print('set other date')
                print(cost_date_status)
                today_date = datetime.strptime(cost_date_status,'%Y-%m-%d')

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
            if cost_related_form.is_valid():
                cost_related_form = cost_related_form.save(commit=False)
                cost_related_form.create_by_id = int(request.user.id)
                # print(cost_related_form.create_by_id)
                cost_related_form.save()

                last_entry_by_this_user = CostRelated.objects.filter(create_by = request.user, short_info = cost_related_form.short_info).latest('created_at')
                # print(cost_form)
                if cost_form.is_valid():
                    cost_form = cost_form.save(commit=False)
                    cost_form.cost_related_id_id = int(last_entry_by_this_user)
                    cost_form.cost_date = cost_date_status
                    # print(cost_form.cost_related_id_id)
                    # print(cost_form)
                    cost_form.save()
                    wallet.wallet_status = wallet.wallet_status - cost_amount
                    wallet.save()

                    # new for monthly summery ------------------------------------
                    if get_monthly_summary:
                        get_monthly_summary.total_balance = get_monthly_summary.total_balance - int(request.POST.get('amount'))
                        get_monthly_summary.save()
                    else:
                        monthly_summary.total_balance = int(total_of_all_wallet['the_count']) - int(request.POST.get('amount'))
                        monthly_summary.last_date_of_month = last_date_of_running_month
                        monthly_summary.user = request.user
                        monthly_summary.save()
                    # new for monthly summery ------------------------------------

            elif cost_related_form.is_valid()==False and request.POST.get('select_short_info') != '':
                prev_cost_related_info = request.POST.get('select_short_info')
                # print(cost_related_form.is_valid())
                if cost_form.is_valid():
                    cost_form = cost_form.save(commit=False)
                    cost_form.cost_related_id_id = int(prev_cost_related_info)
                    cost_form.cost_date = cost_date_status
                    # print(cost_form.cost_related_id_id)
                    # print(cost_form)
                    cost_form.save()
                    wallet.wallet_status = wallet.wallet_status - cost_amount
                    wallet.save()
                    # new for monthly summery ------------------------------------
                    if get_monthly_summary:
                        get_monthly_summary.total_balance = get_monthly_summary.total_balance - int(request.POST.get('amount'))
                        get_monthly_summary.save()
                    else:
                        monthly_summary.total_balance = int(total_of_all_wallet['the_count']) - int(request.POST.get('amount'))
                        monthly_summary.last_date_of_month = last_date_of_running_month
                        monthly_summary.user = request.user
                        monthly_summary.save()
                    # new for monthly summery ------------------------------------

            return redirect('costs:my_costs')

        obj_per_page = 1000 # number of items to be shown per page
        per_page_link = 5    # number of buttons in pagination
        context = eachPageObject(request, all_cost_list, obj_per_page, per_page_link)
        context['all_my_wallet'] = all_my_wallet
        context['all_cost_related']=all_cost_related_by_this_user
        context['total_cost']=total_cost_of_running_month['the_count']
        context['today_date']=date.today()
        context['prev_month_first_date'] = str(prev_month_first_day)
        context['prev_month_last_date'] = str(prev_month_last_day)
        context['next_month_first_date'] = str(next_month_first_day)
        context['next_month_last_date'] = str(next_month_last_day)
        context['current_month'] = datetime.strftime(datetime.strptime(str(current_date), '%Y-%m-%d'), '%m-%Y')
        # print(context)

        return render(request, template_name, context)

    else:
        return redirect('account:login_page')

def getCostGraphData(request):
    if request.GET.get('date_to') == None and request.GET.get('date_from') == None:
        current_date = date.today()

    first_date_of_this_month, last_date_of_this_month, prev_month_first_day, prev_month_last_day, next_month_first_day, next_month_last_day = create_first_last_date(current_date)
    all_cost_list = Costs.objects.filter(cost_related_id__create_by_id = request.user.id, cost_date__range = [first_date_of_this_month, last_date_of_this_month]).order_by('-cost_date', '-id')

    queryset = all_cost_list.values('cost_related_id').annotate(count_sector_cnt=Sum('amount')).order_by('-count_sector_cnt')[:5]
    result = queryset.values('cost_related_id', 'count_sector_cnt')
    print(result)
    graph_data = {}
    for each_result in result:
        cost_sector_id = each_result['cost_related_id']
        count = each_result['count_sector_cnt']
        cost_sector = CostRelated.objects.get(id = cost_sector_id).short_info
        print(cost_sector)
        graph_data[cost_sector]={
            'cost_count': count
        }

    json_data = json.dumps(graph_data)
    print(json_data)
    return HttpResponse(json_data, content_type = 'application/json')

def editCost(request,id):

    if request.user.is_authenticated:
        template_name = 'costs/edit_cost.html'
        get_this_cost_data = Costs.objects.get(id=id)
        get_this_related_data = CostRelated.objects.get(id=get_this_cost_data.cost_related_id)
        all_cost_related = CostRelated.objects.filter(create_by_id= request.user.id)
        the_wallet = Wallet.objects.get(id = get_this_cost_data.wallet_id)
        if request.method == 'POST':

            # get_this_related_data.short_info = request.POST.get('short_info')
            # get_this_related_data.short_description = request.POST.get('short_description')
            # get_this_related_data.cost_field = request.POST.get('cost_field')
            
            get_this_cost_data.cost_related_id_id = int(request.POST.get('select_short_info'))
            get_this_cost_data.description = request.POST.get('description')
            the_wallet.wallet_status = (int(get_this_cost_data.wallet.wallet_status) + int(get_this_cost_data.amount)) - int(request.POST.get('amount'))
            get_this_cost_data.amount = request.POST.get('amount')
            if request.POST.get('cost_date') == None or request.POST.get('cost_date') == "":
                pass
            else:
                get_this_cost_data.cost_date = request.POST.get('cost_date')

            the_wallet.save()
            get_this_cost_data.save()

            return redirect('costs:my_costs')
        
        context ={
            "this_cost_related_data": get_this_related_data,
            "this_cost_data": get_this_cost_data,
            "all_cost_related": all_cost_related
        }
        return render(request, template_name, context)
    else:
        return redirect('account:login_page')
        
def deleteCost(request,id):
    
    get_this_cost_data = Costs.objects.get(id=id)
    the_wallet = Wallet.objects.get(id = get_this_cost_data.wallet_id)
    the_wallet.wallet_status = (int(get_this_cost_data.wallet.wallet_status) + int(get_this_cost_data.amount))
    get_this_related_data = CostRelated.objects.get(id=get_this_cost_data.cost_related_id)

    the_wallet.save()
    # get_this_related_data.delete()
    get_this_cost_data.delete()

    return redirect('costs:my_costs')

def SearchUserCostList(request):
    if request.user.is_authenticated:
        get_user_settings = UsersSettings.objects.get(user = request.user)
        if get_user_settings.prefered_view == 'mobile':
            template_name = 'costs/cost_list_mobile.html'
        else:
            template_name = 'costs/cost_list.html'
        cost_related_form = CostRelatedForm
        cost_form = CostForm
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

        print(current_date)

        print(current_date)
        first_date_of_this_month, last_date_of_this_month, prev_month_first_day, prev_month_last_day, next_month_first_day, next_month_last_day = create_first_last_date(current_date)
        search_cost_title = request.GET.get('cost_type', '')
        search_cost_field = request.GET.get('cost_field', '')
        if request.GET.get('date_from') == '':
            search_date_from = datetime.strptime('2022-01-01', '%Y-%m-%d')
        else:
            search_date_from = datetime.strptime(request.GET.get('date_from'), '%Y-%m-%d')
        if request.GET.get('date_to') == '':
            search_date_to = date.today()
        else:
            search_date_to = datetime.strptime(request.GET.get('date_to'), '%Y-%m-%d')
        print(request.GET.get('wallet'))
        if request.GET.get('wallet') == '' or request.GET.get('wallet') == None:
            all_cost_list = Costs.objects.filter(cost_related_id__create_by_id = request.user.id, cost_related_id__short_info__icontains = search_cost_title, cost_related_id__cost_field__icontains = search_cost_field , cost_date__range = [search_date_from, search_date_to]).order_by('-cost_date', '-id')
        else:
            all_cost_list = Costs.objects.filter(cost_related_id__create_by_id = request.user.id, cost_related_id__short_info__icontains = search_cost_title, cost_date__range = [search_date_from, search_date_to], wallet_id = request.GET.get('wallet')).order_by('-cost_date', '-id')
        total_cost_of_running_month = all_cost_list.aggregate(the_count=Sum('amount'))
        print(total_cost_of_running_month['the_count'])
        all_cost_related_by_this_user = CostRelated.objects.filter(create_by_id= request.user.id)

        if request.method == "POST":
            cost_related_form = CostRelatedForm(request.POST)
            cost_form = CostForm(request.POST)
            wallet = Wallet.objects.get(id = int(request.POST.get('wallet')))
            cost_amount = int(request.POST.get('amount'))
            print("-------------")
            print(request.POST.get('select_short_info'))
            if request.POST.get('cost_date') == None or request.POST.get('cost_date') == '':
                cost_date_status = date.today()
            else:
                cost_date_status = request.POST.get('cost_date')

            if cost_related_form.is_valid()==False and request.POST.get('select_short_info') != '':
                prev_cost_related_info = request.POST.get('select_short_info')
                print(cost_form)
                if cost_form.is_valid():
                    cost_form = cost_form.save(commit=False)
                    cost_form.cost_related_id_id = int(prev_cost_related_info)
                    cost_form.cost_date = cost_date_status
                    print(cost_form.cost_related_id_id)
                    print(cost_form)
                    cost_form.save()
                    wallet.wallet_status = wallet.wallet_status - cost_amount
                    wallet.save()
            else:
                if cost_related_form.is_valid():
                    cost_related_form = cost_related_form.save(commit=False)
                    cost_related_form.create_by_id = int(request.user.id)
                    print(cost_related_form.create_by_id)
                    cost_related_form.save()

                    last_entry_by_this_user = CostRelated.objects.filter(create_by = request.user, short_info = cost_related_form.short_info).latest('created_at')
                    print(cost_form)
                    if cost_form.is_valid():
                        cost_form = cost_form.save(commit=False)
                        cost_form.cost_related_id_id = int(last_entry_by_this_user)
                        cost_form.cost_date = cost_date_status
                        print(cost_form.cost_related_id_id)
                        print(cost_form)
                        cost_form.save()
                        wallet.wallet_status = wallet.wallet_status - cost_amount
                        wallet.save()

            return redirect('costs:my_costs')
        full_url = request.GET
        print(full_url)
        # print(context['current_month'])
        # print(all_my_wallet)
        obj_per_page = 100 # number of items to be shown per page
        per_page_link = 5    # number of buttons in pagination
        context = eachPageObject(request, all_cost_list, obj_per_page, per_page_link)
        context['all_my_wallet'] = all_my_wallet
        context['all_cost_related']=all_cost_related_by_this_user
        context['total_cost']=total_cost_of_running_month['the_count']
        context['today_date']=date.today()
        context['prev_month_first_date'] = str(prev_month_first_day)
        context['prev_month_last_date'] = str(prev_month_last_day)
        context['next_month_first_date'] = str(next_month_first_day)
        context['next_month_last_date'] = str(next_month_last_day)
        context['current_month'] = datetime.strftime(datetime.strptime(str(current_date.date()), '%Y-%m-%d'), '%m-%Y')
        context['request_parameter']=full_url
        

        return render(request, template_name, context)
    else:
        return redirect('account:login_page')

from django.template.loader import get_template
from django.urls import resolve
def downloadCost(request):
    template_path = 'costs/cost_list_pdf.html'
    prev_url = request.META.get('HTTP_REFERER')

    date_from = ""
    date_to = ""
    cost_type = ""
    wallet = ""
    if '?' in prev_url:
        get_parameter_part = prev_url.rsplit('?', 2)[1].split('&')
        print(get_parameter_part)

        for i in get_parameter_part:
            key, value = i.split('=')
            if key == 'date_from':
                date_from = value
            elif key == 'date_to':
                date_to = value
            elif key == 'cost_type':
                cost_type = value
            elif key == 'wallet':
                wallet = value


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

    print(current_date)

    first_date_of_this_month, last_date_of_this_month, prev_month_first_day, prev_month_last_day, next_month_first_day, next_month_last_day = create_first_last_date(current_date)
    search_cost_title = cost_type
    search_cost_field = request.GET.get('cost_field', '')
    if date_from == None or date_from=='':
        search_date_from = first_date_of_this_month
    else:
        search_date_from = date_from
    if date_to == None or date_to=='':
        search_date_to = date.today()
    else:
        search_date_to = date_to
    print(wallet)
    if wallet == None or wallet == '':
        all_cost_list = Costs.objects.filter(cost_related_id__create_by_id = request.user.id, cost_related_id__short_info__icontains = search_cost_title, cost_related_id__cost_field__icontains = search_cost_field , cost_date__range = [search_date_from, search_date_to]).order_by('-cost_date', '-id')
    else:
        all_cost_list = Costs.objects.filter(cost_related_id__create_by_id = request.user.id, cost_related_id__short_info__icontains = search_cost_title, cost_date__range = [search_date_from, search_date_to], wallet_id = request.GET.get('wallet')).order_by('-cost_date', '-id')
    total_cost_of_running_month = all_cost_list.aggregate(the_count=Sum('amount'))
    print(total_cost_of_running_month['the_count'])
    all_cost_related_by_this_user = CostRelated.objects.filter(create_by_id= request.user.id)


    # if request.user.is_authenticated:
        
    #     if request.GET.get('date_to') == None and request.GET.get('date_from') == None:
    #         current_date = date.today()

    #     first_date_of_this_month, last_date_of_this_month, prev_month_first_day, prev_month_last_day, next_month_first_day, next_month_last_day = create_first_last_date(current_date)
    #     all_my_wallet = Wallet.objects.filter(wallet_of = request.user)
    #     all_cost_list = Costs.objects.filter(cost_related_id__create_by_id = request.user.id, cost_date__range = [first_date_of_this_month, last_date_of_this_month]).order_by('-cost_date').order_by('-id')
    #     total_cost_of_running_month = all_cost_list.aggregate(the_count=Sum('amount'))


    context = {'all_cost_related':all_cost_list}
    context['total_cost']=total_cost_of_running_month['the_count']
    context['user'] = request.user
    context['from_date'] = search_date_from
    context['to_date'] = search_date_to
    
    # response = HttpResponse(content_type='application/pdf')
    # response['Content-Disposition'] = 'filename="report.pdf"'

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'

    template = get_template(template_path)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(
        html, dest=response)
    # if error then show some funy view
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response