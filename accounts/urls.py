from django.urls import path
from accounts import views 
from django.urls import include

urlpatterns = [
    path('register/',views.Register , name="register"),
     path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('login/',views.Login , name='login'),
    path('logout/',views.Logout , name = 'logout'),
    path('forgot-password/',views.forgotpass , name="forgotpass"),
    path('reset-password/',views.reset_password , name='reset_password'),
]
