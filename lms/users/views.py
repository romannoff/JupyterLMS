from django.contrib import auth
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from users.forms import UserLoginForm, UserRegistrationForm

# Create your views here.
def login(request):
    if request.user.is_authenticated:
        return redirect(reverse('main:index'))
    if request.method == 'POST':
        form  = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = auth.authenticate(username=username, password=password)
            if user:
                auth.login(request, user)
                return HttpResponseRedirect(reverse('main:index'))
    else:
        form = UserLoginForm()
    context = {
        'title': 'Авторизация',
        'form': form,
    }
    return render(request, 'users/login.html', context)

def registration(request):
    if request.user.is_authenticated:
        return redirect(reverse('main:index'))
    if request.method == 'POST':
        form  = UserRegistrationForm(data=request.POST)
        if form.is_valid():
            form.save()
            user = form.instance
            auth.login(request, user)
            return HttpResponseRedirect(reverse('main:index'))
    else:
        form = UserRegistrationForm()
    context = {
        'title': 'Регистрация',
        'form': form,
    }
    return render(request, 'users/registration.html', context)

@login_required
def logout(request):
    auth.logout(request)
    return redirect(reverse('user:login'))