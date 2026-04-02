from django.urls import path
from dashboard import views 
from django.urls import include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('',views.MainBoard , name = "dashboard"),
    path('expensepage/',views.addExpenses , name="addExpenses"),
    path('Incomepage/',views.addIncome , name = "addIncome"),
    path('profile-page/',views.profile , name="profile"),
    path('Settings',views.settings, name="settings"),
    path('delete-account/',views.delete_account , name='delete_account'),
    path('reports/',views.report , name="Report"),


    path('export/', views.export_page, name='export_page'),
    path('delete/<str:type>/<int:id>/', views.delete_transaction, name='delete_transaction'),
    path('edit/<str:type>/<int:id>/', views.edit_transaction, name='edit_transaction'),
    path('edit-expense/<int:id>/', views.edit_expense, name='edit_expense'),
    path('edit-income/<int:id>/', views.edit_income, name='edit_income'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),

]

