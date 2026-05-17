from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import UserProfileForm

# Signup view
def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('/')
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/signup.html', {'form': form})

# Custom login view
def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('/')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')

# Profile view
def profile_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'accounts/profile.html', {'profile_user': user})

# Profile edit view
@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile', user_id=request.user.id)
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/profile_edit.html', {'form': form})

from django.contrib.auth import logout

def custom_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')