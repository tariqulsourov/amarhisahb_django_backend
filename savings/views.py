# LEGACY VIEW FILE: Used only for old HTML templates. Safe to remove once fully transitioned to React.
from django.shortcuts import render, redirect
from django.db.models import Count, Sum
from django.contrib.auth.decorators import login_required
from savings.forms import SavingsForm, SavingsRelatedForm, WalletForm
from savings.models import SavingRelated, Savings, Wallet, PredefinedWalletList, TransferDetails
from costs.views import eachPageObject, create_first_last_date
from datetime import datetime, date, timedelta
from account.models import UsersSettings

# Create your views here.
@login_required(login_url="/account/login/")
def UserSavingsList(request):
    if request.user.is_authenticated:
        get_user_settings = UsersSettings.objects.get(user = request.user)
        if get_user_settings.prefered_view == 'mobile':
            template_name = 'savings/wallet_list_mobile.html'
        else:
            template_name = 'savings/savings_list.html'
        saving_related_form = SavingsRelatedForm
        saving_form = SavingsForm
        wallet_form = WalletForm
        if request.GET.get('date_to') == None and request.GET.get('date_from') == None:
            current_date = date.today()

        first_date_of_this_month, last_date_of_this_month, prev_month_first_day, prev_month_last_day, next_month_first_day, next_month_last_day = create_first_last_date(current_date)
        all_saving_list = Savings.objects.filter(create_by_id = request.user.id, saving_date__range = [first_date_of_this_month, last_date_of_this_month]).order_by('saving_date')
        total_saving_of_running_month = all_saving_list.aggregate(the_count=Sum('amount'))
        #all_saving_related_by_this_user = SavingRelated.objects.filter(create_by_id= request.user.id)
        all_wallet = Wallet.objects.filter(wallet_of = request.user)
        all_pre_wallet = PredefinedWalletList.objects.all()
        all_my_wallet = Wallet.objects.filter(wallet_of = request.user)
        all_transfer_details = TransferDetails.objects.filter(create_by=request.user).order_by("-tansfered_date")
        
        total_of_all_wallet = all_my_wallet.aggregate(the_count=Sum('wallet_status'))
        print(total_of_all_wallet)
        if request.method == "POST" and WalletForm(request.POST).is_valid():
            wallet_create_from = WalletForm(request.POST).save(commit=False)
            wallet_create_from.wallet_of = request.user
            print('creating wallte')
            try:
                wallet_create_from.save()
            except:
                pass

        elif request.method == "POST":
            saving_form = SavingsForm(request.POST)
            if saving_form.is_valid():
                saving_form = saving_form.save(commit=False)
                # saving_form.saving_related_id_id = int(last_entry_by_this_user)
                # print(saving_form.saving_related_id_id)
                saving_form.create_by = request.user
                print(saving_form)
                saving_form.save()

            return redirect('savings:my_savings')

        
        context = {
            'all_transfer_details':all_transfer_details
        }
        #context['all_saving_related']=all_saving_related_by_this_user
        context['total']=total_of_all_wallet['the_count']
        context['pre_wallet']= all_pre_wallet
        context['all_my_wallet']= all_my_wallet
        context['prev_month_first_date'] = str(prev_month_first_day)
        context['prev_month_last_date'] = str(prev_month_last_day)
        context['next_month_first_date'] = str(next_month_first_day)
        context['next_month_last_date'] = str(next_month_last_day)
        context['current_month'] = datetime.strftime(datetime.strptime(str(current_date), '%Y-%m-%d'), '%m-%Y')
        
        print(context)

        return render(request, template_name, context)

    else:
        return redirect('account:login_page')

def editSavings(request,id):
    if request.user.is_authenticated:
        template_name = 'savings/edit_savings.html'
        get_this_savings_data = Savings.objects.get(id=id)
        # get_this_related_data = SavingRelated.objects.get(id=get_this_savings_data.saving_related_id)

        if request.method == 'POST':

            # get_this_related_data.short_info = request.POST.get('short_info')
            # get_this_related_data.short_description = request.POST.get('short_description')
            # get_this_related_data.saving_where = request.POST.get('saving_source')

            get_this_savings_data.amount = request.POST.get('amount')
            get_this_savings_data.description = request.POST.get('description')
            get_this_savings_data.saving_date = request.POST.get('saving_date')

            # get_this_related_data.save()
            get_this_savings_data.save()

            return redirect('savings:my_savings')
        
        context ={
            # "this_saving_related_data": get_this_related_data,
            "this_saving_data": get_this_savings_data
        }
        return render(request, template_name, context)
    else:
        return redirect('account:login_page')

def deleteSavings(request,id):
    
    get_this_savings_data = Savings.objects.get(id=id)
    # get_this_related_data = SavingRelated.objects.get(id=get_this_savings_data.saving_related_id)


    # get_this_related_data.delete()
    get_this_savings_data.delete()

    return redirect('savings:my_savings')

def deleteWallet(request,id):
    
    get_this_wallet_data = Wallet.objects.get(id=id)
    # get_this_related_data = SavingRelated.objects.get(id=get_this_savings_data.saving_related_id)


    # get_this_related_data.delete()
    get_this_wallet_data.delete()

    return redirect('savings:my_savings')

def editWallet(request,id):
    
    get_this_savings_data = Wallet.objects.get(id=id)
    # get_this_related_data = SavingRelated.objects.get(id=get_this_savings_data.saving_related_id)


    # get_this_related_data.delete()
    # get_this_savings_data.delete()

    return redirect('savings:my_savings')

def SearchUserSavingsList(request):

    template_name = 'savings/savings_list.html'
    savings_related_form = SavingsRelatedForm
    savings_form = SavingsForm
    all_pre_wallet = PredefinedWalletList.objects.all()
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
    search_savings_title = request.GET.get('saving_title', '')
    search_savings_field = request.GET.get('saving_field', '')
    if request.GET.get('date_from') == '':
        search_date_from = datetime.strptime('2022-01-01', '%Y-%m-%d')
    else:
        search_date_from = datetime.strptime(request.GET.get('date_from'), '%Y-%m-%d')
    if request.GET.get('date_to') == '':
        search_date_to = date.today()
    else:
        search_date_to = datetime.strptime(request.GET.get('date_to'), '%Y-%m-%d')

    if request.GET.get('wallet') == '' or request.GET.get('wallet') == None:
        all_savings_list = Savings.objects.filter(create_by_id = request.user.id , saving_date__range = [search_date_from, search_date_to]).order_by('saving_date')
    else:
        all_savings_list = Savings.objects.filter(create_by_id = request.user.id , saving_date__range = [search_date_from, search_date_to], wallet_id = request.GET.get('wallet')).order_by('saving_date')
    total_savings_of_running_month = all_savings_list.aggregate(the_count=Sum('amount'))
    print(total_savings_of_running_month['the_count'])
    #all_savings_related_by_this_user = SavingRelated.objects.filter(create_by_id= request.user.id)

    if request.method == "POST" and WalletForm(request.POST).is_valid():
        wallet_create_from = WalletForm(request.POST).save(commit=False)
        wallet_create_from.wallet_of = request.user
        print('creating wallte')
        wallet_create_from.save()


    elif request.method == "POST":
        # saving_related_form = SavingsRelatedForm(request.POST)
        saving_form = SavingsForm(request.POST)
        # if request.POST.get('select_short_info') != '':
        #     # prev_saving_related_info = request.POST.get('select_short_info')
        #     print(saving_form)
        #     if saving_form.is_valid():
        #         saving_form = saving_form.save(commit=False)
        #         # saving_form.saving_related_id_id = int(prev_saving_related_info)
        #         # print(saving_form.saving_related_id_id)
        #         saving_form
        #         print(saving_form)
        #         saving_form.save()
        
        # if saving_related_form.is_valid():
        #     saving_related_form = saving_related_form.save(commit=False)
        #     saving_related_form.create_by_id = int(request.user.id)
        #     print(saving_related_form.create_by_id)
        #     saving_related_form.save()

            # last_entry_by_this_user = SavingRelated.objects.filter(create_by = request.user).latest('created_at')
        # print(saving_form)
        if saving_form.is_valid():
            saving_form = saving_form.save(commit=False)
            # saving_form.saving_related_id_id = int(last_entry_by_this_user)
            # print(saving_form.saving_related_id_id)
            saving_form.create_by = request.user
            print(saving_form)
            saving_form.save()

        return redirect('savings:my_savings')

    obj_per_page = 100 # number of items to be shown per page
    per_page_link = 5    # number of buttons in pagination
    context = eachPageObject(request, all_savings_list, obj_per_page, per_page_link)
    #context['all_savings_related']=all_savings_related_by_this_user
    context['total']=total_savings_of_running_month['the_count']
    context['pre_wallet']= all_pre_wallet
    context['all_my_wallet']= all_my_wallet
    context['prev_month_first_date'] = str(prev_month_first_day)
    context['prev_month_last_date'] = str(prev_month_last_day)
    context['next_month_first_date'] = str(next_month_first_day)
    context['next_month_last_date'] = str(next_month_last_day)
    context['current_month'] = datetime.strftime(datetime.strptime(str(current_date.date()), '%Y-%m-%d'), '%m-%Y')
    print(context)

    return render(request, template_name, context)

def transferBalance(request):
    transer_from = Wallet.objects.get(id = request.POST.get('transfer_from'))
    transfer_to  = Wallet.objects.get(id = request.POST.get('transfer_to'))
    transfer_details_db = TransferDetails()
    if request.method == "POST":
        transferable_amount = request.POST.get('amount')

        transfer_details_db.transfer_from_wallet = transer_from.wallet_name
        transfer_details_db.transfer_to_wallet = transfer_to.wallet_name
        transfer_details_db.prev_amount_of_transfered_from = transer_from.wallet_status
        transfer_details_db.current_amount_of_transfered_from = transer_from.wallet_status - int(transferable_amount)
        transfer_details_db.prev_amount_of_transfered_to = transfer_to.wallet_status
        transfer_details_db.current_amount_of_transfered_to = transfer_to.wallet_status + int(transferable_amount)
        transfer_details_db.transfered_amount = int(transferable_amount)
        transfer_details_db.create_by = request.user
        transfer_details_db.save()

        transer_from.wallet_status = transer_from.wallet_status - int(transferable_amount)
        transfer_to.wallet_status = transfer_to.wallet_status + int(transferable_amount)
        transer_from.save()
        transfer_to.save()

        


        return redirect('savings:my_savings')
    
def edit_wallet_name(request, id):
    get_the_wallet = Wallet.objects.get(id = id)
    get_the_wallet.wallet_name = request.POST.get('wallet_name_edit')
    get_the_wallet.save()

    return redirect('savings:my_savings')

def edit_wallet_amount(request, id):
    get_the_wallet = Wallet.objects.get(id = id)
    get_the_wallet.wallet_status = request.POST.get('wallet_balance_edit')
    get_the_wallet.save()

    return redirect('savings:my_savings')