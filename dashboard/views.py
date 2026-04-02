import csv
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile
from .models import Expense , Income
from django.db.models import Count, Sum
from django.contrib import messages
import json
from django.db.models.functions import TruncMonth
from decimal import Decimal
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.db.models.functions import TruncMonth
from django.utils.timezone import now
from datetime import datetime
from django.contrib.auth import update_session_auth_hash

@login_required
def MainBoard(request):
    
    expenses = Expense.objects.filter(user = request.user).order_by('-expense_date')
    incomes = Income.objects.filter(user = request.user)
    total_income = incomes.aggregate(total = Sum('amount'))['total'] or 0
    total_expense = expenses.aggregate(total = Sum('amount'))['total'] or 0
    profile,created = UserProfile.objects.get_or_create(user = request.user)

    today = now().date()
    category_data = Expense.objects.filter(
        user=request.user,
        expense_date=today
    ).values('category').annotate(total=Sum('amount'))

    category_data = [
        {
            'category':item['category'],
            'total':float(item['total'])
        }
        for item in category_data
    ]

    monthly_qs = Expense.objects.filter(user = request.user)\
                    .annotate(month = TruncMonth('expense_date'))\
                    .values('month')\
                    .annotate(total = Sum('amount'))\
                    .order_by('month')

    monthly_dict = {
        item['month'].month:float(item['total'])
        for item in monthly_qs if item['month']
    }
 

    monthly_data = []
    for m in range(1 ,13):
        monthly_data.append({
            'month':datetime(2024,m,1).strftime('%b'),
            'total':monthly_dict.get(m,0)
        })

    balance = total_income-total_expense

    context = {
            'expenses':expenses,
            'balance':balance,
            'category_data':json.dumps(category_data),
            'monthly_data':json.dumps(monthly_data),
            'profile':profile,
               }
    return render(request ,"MainBoard.html",context)
 
@login_required
def addExpenses(request):
    if request.method == "POST":
        expense_date = request.POST.get("expense_date")
        category = request.POST.get("category")
        amount = Decimal(request.POST.get("amount"))
        payment_mode = request.POST.get("payment_mode")
        notes = request.POST.get("notes")

        expenses = Expense.objects.filter(user = request.user).order_by('-expense_date')
        incomes = Income.objects.filter(user = request.user)
        tota_income = incomes.aggregate(total = Sum('amount'))['total'] or 0
        total_expense = expenses.aggregate(total = Sum('amount'))['total'] or 0
        current_balance = tota_income-total_expense

        if amount > current_balance:
            messages.error(request , f"Cannot add expense! Current balanace is ₹{current_balance}")
            return redirect('addExpenses')

        Expense.objects.create(
            user = request.user,
            expense_date = expense_date,
            category = category,
            amount = amount,
            payment_mode = payment_mode,
            notes = notes,
        )
        messages.success(request ,"Expense added succesfully")
        return redirect('/')
    return render(request , 'addexpense.html')

@login_required
def addIncome(request):
    if request.method == "POST":
        income_date = request.POST.get("income_date")
        source = request.POST.get("source")
        amount = float(request.POST.get("amount"))
        payment_mode = request.POST.get("payment_mode")
        notes = request.POST.get("notes")

        Income.objects.create(
            user = request.user,
            income_date = income_date,
            source = source,
            amount=amount,
            payment_mode=payment_mode,
            notes = notes,
        )
        return redirect('/')
    return render(request ,'addIncomepage.html')

@login_required
def profile(request):

    expenses = Expense.objects.filter(user = request.user)
    incomes = Income.objects.filter(user = request.user)
    user_profile , created = UserProfile.objects.get_or_create(user = request.user)
    total_expense = expenses.aggregate(total = Sum('amount'))['total'] or 0
    total_income = incomes.aggregate(total = Sum('amount'))['total'] or 0
    balance = total_income - total_expense
    total_transactions = expenses.count() + incomes.count()
    top_cat_query = expenses.values('category').annotate(count =Count('category')).order_by('-count').first()
    top_category = top_cat_query['category'] if top_cat_query else "N/A"
    recent_expense = expenses.order_by('-expense_date')[:7]

    today = now().date()
    monthly_total = expenses.filter(expense_date__year = today.year , expense_date__month = today.month ).aggregate(total= Sum('amount'))['total'] or 0

    context ={
        'total_income':total_income,
        'total_expense':total_expense,
        'balance':balance,
        'total_transactions':total_transactions,
        'top_category':top_category,
        'recent_expense':recent_expense,
        'monthly_total':monthly_total,
    }

    return render(request , "profile.html",context)


@login_required
def settings(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        if 'old_password' in request.POST:
            old_password = request.POST.get('old_password')
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')

            if not request.user.check_password(old_password):
                messages.error(request, "Your current password is incorrect.")
            elif new_password1 != new_password2:
                messages.error(request, "New passwords do not match.")
            else:
                request.user.set_password(new_password1)
                request.user.save()
                update_session_auth_hash(request, request.user)  # keeps user logged in
                messages.success(request, "Password updated successfully!")
                return redirect('settings')

        else:
            request.user.username = request.POST.get("username")
            request.user.email = request.POST.get("email")
            profile.phone = request.POST.get("phone")
            if request.FILES.get('profile_pic'):
                profile.profile_pic = request.FILES.get('profile_pic')
                
            request.user.save()
            profile.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('settings')  

    return render(request, "settings.html", {"profile": profile})


def delete_account(request):
    if request.method == "POST":
        user = request.user

        try:
            profile = user.userprofile

            #if profile_pic exists
            if profile.profile_pic:
                profile.profile_pic.delete(save = False)

        except UserProfile.DoesNotExists:
            pass
        user.delete()

        messages.success(request, "Your account and all related data has been permanently deleted!")
        return redirect('login')
    
    return redirect('profile')


def report(request):

    expense = Expense.objects.filter(user = request.user)
    income = Income.objects.filter(user = request.user)

    total_expense = expense.aggregate(total = Sum('amount'))['total'] or 0
    total_income = income.aggregate(total = Sum('amount'))['total'] or 0
    balance = total_income - total_expense

    transactions = []

    for e in expense:
        transactions.append({
            "date":e.expense_date,
            "type":"Expense",
            "category":e.category,
            "amount":float(e.amount),
            "payment_mode":e.payment_mode
        })

  
    for i in income:
        transactions.append({
            "date":i.income_date,
            "type":"Income",
            "category":i.source,
            "amount":float(i.amount),
            "payment_mode":i.payment_mode
        })

    category_data = list(
        expense.values('category')
        .annotate(total = Sum('amount'))
    )
    category_data = [
        {'category': item['category'], 'total': float(item['total'])}
        for item in category_data
    ]

 
    monthly_qs = expense.annotate(month=TruncMonth('expense_date'))\
    .values('month')\
    .annotate(total=Sum('amount'))\
    .order_by('month')

    monthly_dict = {
    item['month'].month: float(item['total'])
    for item in monthly_qs if item['month']
   }
    
    monthly_data = []

    for m in range(1, 13):
       monthly_data.append({
        'month': datetime(1900, m, 1).strftime('%b'),
        'total': monthly_dict.get(m, 0)
    })

    top_category = None
    if category_data:
        top_category = max(category_data , key = lambda x: x['total'])['category']
    
    context = {
        "total_income":total_income,
        "total_expense":total_expense,
        "balance":balance,
        "transactions":transactions,
        "category_data":json.dumps(category_data),
        "monthly_data":json.dumps(monthly_data),
        "top_category":top_category,
        "total_transactions":len(transactions)
    }

    return render(request , 'reportpage.html',context)

def export_page(request):

    expenses = Expense.objects.filter(user=request.user)
    incomes = Income.objects.filter(user=request.user)

    start = request.GET.get('start_date')
    end = request.GET.get('end_date')
    t_type = request.GET.get('type')
    category = request.GET.get('category')

    if start:
        expenses = expenses.filter(expense_date__gte=start)
        incomes = incomes.filter(income_date__gte=start)

    if end:
        expenses = expenses.filter(expense_date__lte=end)
        incomes = incomes.filter(income_date__lte=end)

    if category:
        expenses = expenses.filter(category=category)

    transactions = []

    for e in expenses:
        transactions.append({
            "id": e.id,   
            "date": e.expense_date,
            "type": "Expense",
            "category": e.category,
            "amount": e.amount,
            "payment_mode": e.payment_mode
        })

    for i in incomes:
        transactions.append({
            "id": i.id,
            "date": i.income_date,
            "type": "Income",
            "category": i.source,
            "amount": i.amount,
            "payment_mode": i.payment_mode
        })

    if t_type:
        transactions = [t for t in transactions if t["type"] == t_type]

    transactions = sorted(transactions, key=lambda x: x['date'], reverse=True)

    return render(request, 'export.html', {
        'transactions': transactions
    })


def export_csv(request):
    expenses = Expense.objects.filter(user=request.user)
    incomes = Income.objects.filter(user=request.user)

    start = request.GET.get('start_date')
    end = request.GET.get('end_date')
    t_type = request.GET.get('type')
    category = request.GET.get('category')

    if start:
        expenses = expenses.filter(expense_date__gte=start)
        incomes = incomes.filter(income_date__gte=start)

    if end:
        expenses = expenses.filter(expense_date__lte=end)
        incomes = incomes.filter(income_date__lte=end)

    if category:
        expenses = expenses.filter(category=category)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Type', 'Category', 'Amount', 'Mode'])

    if not t_type or t_type == "Expense":
        for e in expenses:
            writer.writerow([e.expense_date, "Expense", e.category, e.amount, e.payment_mode])

    if not t_type or t_type == "Income":
        for i in incomes:
            writer.writerow([i.income_date, "Income", i.source, i.amount, i.payment_mode])

    return response


def export_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="transactions.pdf"'

    p = canvas.Canvas(response)
    y = 800

    expenses = Expense.objects.filter(user=request.user)
    incomes = Income.objects.filter(user=request.user)

    start = request.GET.get('start_date')
    end = request.GET.get('end_date')
    t_type = request.GET.get('type')
    category = request.GET.get('category')

    if start:
        expenses = expenses.filter(expense_date__gte=start)
        incomes = incomes.filter(income_date__gte=start)

    if end:
        expenses = expenses.filter(expense_date__lte=end)
        incomes = incomes.filter(income_date__lte=end)

    if category:
        expenses = expenses.filter(category=category)

    if not t_type or t_type == "Expense":
        for e in expenses:
            p.drawString(50, y, f"{e.expense_date} | Expense | {e.category} | ₹{e.amount}")
            y -= 20

    if not t_type or t_type == "Income":
        for i in incomes:
            p.drawString(50, y, f"{i.income_date} | Income | {i.source} | ₹{i.amount}")
            y -= 20

    p.save()
    return response



@login_required
def edit_expense(request, id):
    expense = get_object_or_404(Expense, id=id, user=request.user)

    if request.method == "POST":
        expense.expense_date = request.POST.get("expense_date")
        expense.category = request.POST.get("category")
        expense.amount = request.POST.get("amount")
        expense.payment_mode = request.POST.get("payment_mode")
        expense.notes = request.POST.get("notes")

        expense.save()
        messages.success(request, "Expense updated successfully!")
        return redirect('export_page')

    return render(request, 'edit_expense.html', {'expense': expense})

@login_required
def edit_income(request, id):
    income = get_object_or_404(Income, id=id, user=request.user)

    if request.method == "POST":
        income.income_date = request.POST.get("income_date")
        income.source = request.POST.get("source")
        income.amount = request.POST.get("amount")
        income.payment_mode = request.POST.get("payment_mode")
        income.notes = request.POST.get("notes")

        income.save()
        messages.success(request, "Income updated successfully!")
        return redirect('export_page')

    return render(request, 'edit_income.html', {'income': income})


@login_required
def delete_transaction(request, type, id):
    if type == "Expense":
        obj = get_object_or_404(Expense, id=id, user=request.user)
    else:
        obj = get_object_or_404(Income, id=id, user=request.user)

    obj.delete()
    messages.success(request, f"{type} deleted successfully!")

    return redirect('export_page')

@login_required
def edit_transaction(request, type, id):
    if type == "Expense":
        return redirect('edit_expense', id=id)
    else:
        return redirect('edit_income', id=id)

