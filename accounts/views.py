from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate , login
from django.contrib.auth import logout
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re
import random
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.core.files.base import ContentFile

from accounts.models import UserProfile

def Login(request):
   if request.method == "POST":
       email =request.POST.get('email')
       password = request.POST.get('password')

       try:
         user_obj = User.objects.get(email=email)
         username = user_obj.username
         user = authenticate(request , username=username,password=password)
       except User.DoesNotExist:
           user = None
       except User.MultipleObjectsReturned:
           return render(request , "loginpage.html",{
               'error':'Multiple Accounts found with this email.Please contact support.'
           })

       if user is not None:
           login(request , user)
           return redirect('/')
       else:
           return render(request , "loginpage.html",{
               'error':'Invalid Email or password'
           })
   return render(request , "loginpage.html")


def Register(request):
    if request.method == "POST":
        fullname = request.POST.get('fullname')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        gender = request.POST.get('gender')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        profile_pic = request.FILES.get('profile_pic')

        errors = []

        # validations
        if password != confirm_password:
            errors.append("Passwords do not match")

        if User.objects.filter(username=username).exists():
            errors.append("Username already exists")

        if User.objects.filter(email=email).exists():
            errors.append("Email already exists")

        try:
            validate_email(email)
        except ValidationError:
            errors.append("Invalid email format")

        if not phone.isdigit() or len(phone) != 10:
            errors.append("Invalid phone number")

        if len(password) < 6:
            errors.append("Password too short")

        if not re.search(r'[A-Z]', password):
            errors.append("Must contain uppercase letter")

        if not re.search(r'[0-9]', password):
            errors.append("Must contain a number")

        if not re.search(r'[!@#$%^&*]', password):
            errors.append("Must contain special character")

        if errors:
            return render(request, 'registerpage.html', {'errors': errors})

        # STORE DATA IN SESSION
        request.session['register_data'] = {
            'fullname': fullname,
            'username': username,
            'email': email,
            'phone': phone,
            'gender': gender,
            'password': password,
        }

        if profile_pic:
            request.session['profile_pic_name'] = profile_pic.name 
            request.session['profile_pic_content'] = profile_pic.read().decode('latin1')
        else:
            request.session['profile_pic_name'] = None
            request.session['profile_pic_content'] = None 

        otp = str(random.randint(100000, 999999))
        request.session['email_otp'] = otp

        send_mail(
            'Verify your Email - OTP',
            f'Hello {fullname}, your OTP for E-mail verification : {otp} It is safe',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False
        )

        return redirect('verify_otp')

    return render(request, 'registerpage.html')

def verify_otp(request):

    if request.method == "POST":
        input_otp = request.POST.get('otp', '').strip()
        session_otp = request.session.get('email_otp')

        if not session_otp:
            messages.error(request, "OTP expired. Register again.")
            return redirect('register')

        if input_otp == session_otp:
            data = request.session.get('register_data')
            pic_name = request.session.get('profile_pic_name')
            pic_content = request.session.get('profile_pic_content')

            if not data :
                messages.error(request, "Session expired.Please Register Again!")
                return redirect('register')

            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name = data['fullname'],
                is_active = True,
            )
            user.save()
            if pic_name and pic_content:
                profile_file = ContentFile(pic_content.encode('latin1'),name =pic_name )
            else:
                profile_file = None

            UserProfile.objects.create(
                user=user,
                phone=data['phone'],
                gender=data['gender'],
                profile_pic = profile_file
            )

            request.session.pop('register_data')
            request.session.pop('profile_pic_name')
            request.session.pop('profile_pic_content')
            request.session.pop('email_otp')

            messages.success(request, "Account created successfully!")
            return redirect('login')

        else:
            messages.error(request, "Invalid OTP")

    return render(request, 'verify_otp.html')


def forgotpass(request):
   if request.method == "POST":
       email = request.POST.get('email')

       if not User.objects.filter(email = email).exists():
           return render(request , 'forgotpassword.html',{
               'error':'Email not registered'
           })
       
       request.session['reset_email'] = email
       return redirect('reset_password')
   return render(request  , 'forgotpassword.html')

def reset_password(request):
    errors = []

    email = request.session.get('reset_email')

    if not email:
        return redirect('forgotpass')
    
    if request.method == "POST":
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password  != confirm_password:
            errors.append("Passwords do not match")

        if len(password) < 6:
            errors.append("Password must be at least 6 characters")

        if not re.search(r'[A-Z]',password):
            errors.append("Password must contain at least one Upper case letter")
        
        if not re.search(r'[0-9]',password):
            errors.append("Password must contain atleast one number")
        
        if not re.search(r'[!@#$%^&*]',password):
            errors.append("Password must contain a special chracter") 

        if errors:
            return render(request , 'resetpassword.html',{
                'errors':errors
            })
        
        
        users = User.objects.filter(email = email)
        if users.exists():
           user = users.first()
           user.set_password(password)
           user.save()
           request.session.pop('reset_email',None)
           return redirect('login')
        else:
            return redirect('login')
    
    return render(request , 'resetpassword.html')
 
def Logout(request):
    logout(request)
    return redirect('login')

