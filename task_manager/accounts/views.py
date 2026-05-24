from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count
from tasks.models import Project, Task
from .forms import UserProfileForm
from tasks.models import Project, Task, Team, UserProfile

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
@login_required
def profile_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # Get user's projects
    user_projects = Project.objects.filter(
        Q(members=user) | Q(created_by=user)
    ).distinct()
    user_projects_count = user_projects.count()
    
    # Get user's tasks
    user_tasks = Task.objects.filter(
        Q(assigned_to=user) | Q(created_by=user)
    ).distinct()
    user_total_tasks = user_tasks.count()
    user_completed_tasks = user_tasks.filter(status=Task.Status.DONE).count()
    user_pending_tasks = user_total_tasks - user_completed_tasks
    user_completion_rate = round((user_completed_tasks / user_total_tasks * 100), 1) if user_total_tasks > 0 else 0
    
    # Score & Level
    user_profile = user.profile
    user_points = user_profile.points
    user_level = user_profile.level()
    user_tasks_completed = user_profile.total_tasks_completed
    
    user_rank = UserProfile.objects.filter(points__gt=user_points).count() + 1
    
    # Get all teams
    all_teams = Team.objects.all()
    
    # User's teams
    user_teams = user.teams.all()
    
    # Team management (only for profile owner)
    if request.user == user:
        if request.method == 'POST':
            if 'add_team' in request.POST:
                team_id = request.POST.get('team_id')
                team = get_object_or_404(Team, id=team_id)
                if team not in user.teams.all():
                    user.teams.add(team)
                    
                    # Add user to team projects
                    team_members = team.members.all()
                    projects = Project.objects.filter(
                        Q(created_by__in=team_members) | Q(members__in=team_members)
                    ).distinct()
                    
                    for project in projects:
                        if user not in project.members.all() and user != project.created_by:
                            project.members.add(user)
                    
                    messages.success(request, f'You joined the {team.name} team and added to its projects!')
            
            elif 'remove_team' in request.POST:
                team_id = request.POST.get('team_id')
                team = get_object_or_404(Team, id=team_id)
                if team in user.teams.all():
                    user.teams.remove(team)
                    messages.success(request, f'You left the {team.name} team.')
    
    context = {
        'profile_user': user,
        'user_projects_count': user_projects_count,
        'user_total_tasks': user_total_tasks,
        'user_completed_tasks': user_completed_tasks,
        'user_pending_tasks': user_pending_tasks,
        'user_completion_rate': user_completion_rate,
        'user_teams': user_teams,
        'all_teams': all_teams,
        'user_points': user_points,
        'user_level': user_level,
        'user_tasks_completed': user_tasks_completed,
        'user_rank': user_rank,
    }
    
    return render(request, 'accounts/profile.html', context)

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