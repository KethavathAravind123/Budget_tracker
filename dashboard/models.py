from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('Food','Food'),
        ('Travel','Travels'),
        ('Shopping','Shopping'),
        ('Bills','Bills'),
        ('Others','Others'),
    ]

    PAYMENT_CHOICES =[
        ('Cash','Cash'),
        ('Card','Card'),
        ('Online','Online'),
    ]

    user = models.ForeignKey(User , on_delete=models.CASCADE)
    expense_date = models.DateField()
    category = models.CharField(max_length=20 , choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10 , decimal_places=2)
    payment_mode = models.CharField(max_length=10 , choices=PAYMENT_CHOICES)
    notes = models.TextField(blank=True,null=True)

    def __str__(self):
        return f"{self.category} - {self.amount}"
    
class Income(models.Model):

    INCOME_SOURCE = [
        ("Salary","Salary"),
        ("Freelance","Freelance"),
        ("Investment","Investment"),
        ("Gift","Gift"),
        ("Others","Others"),
    ]

    PAYMENT_MODE = [
        ("Cash" , "Cash"),
        ("Bank Transfer","Bank Transfer"),
        ("Online Payment","Online Payment"),
        ("Cheque","Cheque"),
    ]

    user = models.ForeignKey(User , on_delete=models.CASCADE)
    income_date = models.DateField()
    source = models.CharField(max_length=20 , choices=INCOME_SOURCE)
    amount = models.DecimalField(max_digits=10 , decimal_places=2)
    payment_mode = models.CharField(max_length=20 , choices=PAYMENT_MODE)
    notes = models.TextField(max_length=50 , null=True , blank=True)

    def __str__(self):
        return f"{self.source}-{self.amount}"