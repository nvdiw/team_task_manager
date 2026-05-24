from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Sum, FloatField, Case, When, Value, IntegerField
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth.models import User
import json
from datetime import datetime
from django.http import JsonResponse
from .models import Project, Task, Comment, TaskAttachment, UserProfile, PointTransaction
from .forms import ProjectForm, TaskForm, CommentForm, TaskAttachmentForm
from tasks.models import Team
# ==================== PROJECT VIEWS ====================

@login_required
@login_required
def project_list(request):
    # Get team filter from request
    team_filter = request.GET.get('team', '')
    
    # Base queryset
    projects_list = Project.objects.filter(
        Q(members=request.user) | Q(created_by=request.user)
    ).distinct()
    
    # Filter by team (if user is in that team)
    if team_filter:
        try:
            team = Team.objects.get(id=team_filter)
            if request.user in team.members.all():
                # Show projects where creator or members are in this team
                projects_list = projects_list.filter(
                    Q(created_by__in=team.members.all()) | 
                    Q(members__in=team.members.all())
                ).distinct()
        except Team.DoesNotExist:
            pass
    
    paginator = Paginator(projects_list, 5)
    page_number = request.GET.get('page')
    projects = paginator.get_page(page_number)
    
    # Get user's teams for filter dropdown
    user_teams = request.user.teams.all()
    
    return render(request, 'tasks/project_list.html', {
        'projects': projects,
        'user_teams': user_teams,
        'team_filter': team_filter,
    })

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Check if user has access (via team or manually added members)
    has_access = False

    if project.team:
        # If project has a team, check team membership
        if request.user in project.team.members.all():
            has_access = True
    elif project.members.filter(id=request.user.id).exists():
        # If no team, check direct membership
        has_access = True

    if not has_access and request.user != project.created_by:
        messages.error(request, 'You do not have access to this project.')
        return redirect('tasks:project_list')
    
    # Get filter parameters from request
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    assigned_filter = request.GET.get('assigned', '')
    deadline_from = request.GET.get('deadline_from', '')
    deadline_to = request.GET.get('deadline_to', '')
    
    # Get assigned user name for display
    assigned_username = ''
    if assigned_filter and assigned_filter != 'all' and assigned_filter != 'unassigned':
        try:
            assigned_user = User.objects.get(id=assigned_filter)
            assigned_username = assigned_user.username
        except User.DoesNotExist:
            assigned_username = ''

    # Start with all tasks
    tasks_list = project.tasks.all()
    
    # Apply filters
    if status_filter:
        tasks_list = tasks_list.filter(status=status_filter)
    
    if priority_filter:
        tasks_list = tasks_list.filter(priority=priority_filter)
    
    if assigned_filter and assigned_filter != 'all':
        if assigned_filter == 'unassigned':
            tasks_list = tasks_list.filter(assigned_to__isnull=True)
        else:
            tasks_list = tasks_list.filter(assigned_to__id=assigned_filter)
    
    if deadline_from:
        tasks_list = tasks_list.filter(deadline__gte=deadline_from)
    
    if deadline_to:
        tasks_list = tasks_list.filter(deadline__lte=deadline_to)

    # Instead of just comments, send activities for each task
    for task in tasks_list:
        task.activities = task.get_activities()

    # Pagination (5 tasks per page)
    paginator = Paginator(tasks_list, 5)
    page_number = request.GET.get('page')
    tasks = paginator.get_page(page_number)
    
    # Get list of users for assigned filter
    users = project.members.all()
    
    context = {
        'project': project,
        'tasks': tasks,
        'users': users,
        # Preserve filter values in template
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'assigned_filter': assigned_filter,
        'assigned_username': assigned_username,
        'deadline_from': deadline_from,
        'deadline_to': deadline_to,
    }
    
    return render(request, 'tasks/project_detail.html', context)

@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()

            if project.team:
                project.members.set(project.team.members.all())
            else:
                form.save_m2m()
            messages.success(request, 'Project created successfully!')
            return redirect('tasks:project_detail', pk=project.pk)
    else:
        form = ProjectForm()
        
        # Get user's teams
        user_teams = request.user.teams.all()
        team_members = []
        
        # Collect all members from user's teams
        for team in user_teams:
            for member in team.members.all():
                if member not in team_members:
                    team_members.append(member)
        
        # Get all users (excluding team members)
        other_users = User.objects.exclude(id__in=[u.id for u in team_members]).exclude(id=request.user.id)
        
        # Order: team members first, then other users, current user last?
        ordered_members = team_members + list(other_users)
        
        # Add current user at the beginning (optional)
        if request.user not in ordered_members:
            ordered_members.insert(0, request.user)
        
        # Create ordering for queryset
        preserved = Case(*[When(pk=member.pk, then=Value(index)) for index, member in enumerate(ordered_members)], default=Value(len(ordered_members)), output_field=IntegerField())
        
        form.fields['members'].queryset = User.objects.all().order_by(preserved)
    
    return render(request, 'tasks/project_form.html', {'form': form, 'title': 'Create Project'})

@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    if request.user != project.created_by:
        messages.error(request, 'Only the project creator can edit this project.')
        return redirect('tasks:project_detail', pk=pk)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            if project.team:
                project.members.set(project.team.members.all())
            messages.success(request, 'Project updated successfully!')
            return redirect('tasks:project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)

        if project.team:
            form.fields['members'].queryset = project.team.members.all()
        else:
            form.fields['members'].queryset = User.objects.all()

        # Get user's teams
        user_teams = request.user.teams.all()
        team_members = []
        
        # Collect all members from user's teams
        for team in user_teams:
            for member in team.members.all():
                if member not in team_members:
                    team_members.append(member)
        
        # Get other users
        other_users = User.objects.exclude(id__in=[u.id for u in team_members]).exclude(id=request.user.id)
        
        # Order: team members first, then other users
        ordered_members = team_members + list(other_users)
        
        # Add current user at the beginning
        if request.user not in ordered_members:
            ordered_members.insert(0, request.user)
        
        # Create ordering for queryset
        preserved = Case(*[When(pk=member.pk, then=Value(index)) for index, member in enumerate(ordered_members)], default=Value(len(ordered_members)), output_field=IntegerField())
        
    
    return render(request, 'tasks/project_form.html', {'form': form, 'title': 'Edit Project'})

@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    if request.user != project.created_by:
        messages.error(request, 'Only the project creator can delete this project.')
        return redirect('tasks:project_detail', pk=pk)
    
    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Project deleted successfully!')
        return redirect('tasks:project_list')
    
    return render(request, 'tasks/project_confirm_delete.html', {'project': project})

# ==================== TASK VIEWS ====================

@login_required
def task_create(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if request.user not in project.members.all() and request.user != project.created_by:
        messages.error(request, "Only members of this project can Create Task")
        return redirect('tasks:project_detail', pk=project.pk)
    
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.created_by = request.user
            task.save()
            messages.success(request, 'Task created successfully!')
            return redirect('tasks:project_detail', pk=project.pk)
    else:
        form = TaskForm()
        
        # Get user's teams
        user_teams = request.user.teams.all()
        team_members = []
        
        # Collect all members from user's teams
        for team in user_teams:
            for member in team.members.all():
                if member not in team_members and member in project.members.all():
                    team_members.append(member)
        
        # Get other project members (not in user's teams)
        other_members = [m for m in project.members.all() if m not in team_members]
        
        # Combine: team members first, then other members
        ordered_members = team_members + other_members
        
        # Create a new queryset with ordered members
        from django.db.models import Case, When, Value, IntegerField
        preserved = Case(*[When(pk=member.pk, then=Value(index)) for index, member in enumerate(ordered_members)], default=Value(len(ordered_members)), output_field=IntegerField())
        
        form.fields['assigned_to'].queryset = project.members.all().order_by(preserved)
    
    return render(request, 'tasks/task_form.html', {
        'form': form,
        'title': 'Create Task',
        'project': project
    })

@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)

    if request.user != task.project.created_by and request.user != task.created_by:
        messages.error(request, "Only Creator of this Task, project can Edit Task")
        return redirect('tasks:project_detail', pk=task.project.pk)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully!')
            return redirect('tasks:project_detail', pk=task.project.pk)
    else:
        form = TaskForm(instance=task)
        
        # Get user's teams
        user_teams = request.user.teams.all()
        team_members = []
        
        # Collect all members from user's teams
        for team in user_teams:
            for member in team.members.all():
                if member not in team_members and member in task.project.members.all():
                    team_members.append(member)
        
        # Get other project members (not in user's teams)
        other_members = [m for m in task.project.members.all() if m not in team_members]
        
        # Combine: team members first, then other members
        ordered_members = team_members + other_members
        
        # Create a new queryset with ordered members
        from django.db.models import Case, When, Value, IntegerField
        preserved = Case(*[When(pk=member.pk, then=Value(index)) for index, member in enumerate(ordered_members)], default=Value(len(ordered_members)), output_field=IntegerField())
        
        form.fields['assigned_to'].queryset = task.project.members.all().order_by(preserved)
    
    return render(request, 'tasks/task_form.html', {
        'form': form,
        'title': 'Edit Task',
        'project': task.project
    })

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    project_pk = task.project.pk

    if request.user != task.project.created_by and request.user != task.created_by:
        messages.error(request, "Only Creator of this Task, project can Delete Task")
        return redirect('tasks:project_detail', pk=task.project.pk)
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully!')
        return redirect('tasks:project_detail', pk=project_pk)
    
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})

@login_required
def task_toggle_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    if request.user != task.assigned_to and request.user != task.project.created_by:
        messages.error(request, 'You do not have permission to change this task status.')
        return redirect('tasks:project_detail', pk=task.project.pk)
    
    new_status = request.POST.get('status')
    
    if new_status and new_status in [Task.Status.TODO, Task.Status.IN_PROGRESS, Task.Status.DONE]:
        old_status = task.status
        task.status = new_status
        task.save()
        messages.success(request, f'Task status changed to {task.get_status_display()}')
        
        # اگر تسک به DONE تغییر کرده و قبلاً DONE نبوده و امتیاز هنوز داده نشده
        if new_status == Task.Status.DONE and old_status != Task.Status.DONE and not task.points_awarded:
            # محاسبه امتیاز بر اساس اولویت
            points_map = {
                Task.Priority.LOW: 10,
                Task.Priority.MEDIUM: 20,
                Task.Priority.HIGH: 30,
                Task.Priority.URGENT: 50,
            }
            points = points_map.get(task.priority, 10)
            
            # به کاربر اختصاص یافته (assigned_to) امتیاز بده، اگر وجود داشته باشد
            if task.assigned_to:
                profile = task.assigned_to.profile
                profile.points += points
                profile.total_tasks_completed += 1
                profile.save()
                
                # ثبت تراکنش
                PointTransaction.objects.create(
                    user=task.assigned_to,
                    task=task,
                    points_earned=points,
                    description=f"Completed task '{task.title}' (Priority: {task.get_priority_display()})"
                )
                
                task.points_awarded = True
                task.save()
                
                messages.success(request, f'🎉 +{points} points awarded to {task.assigned_to.username}!')
    
    next_url = request.META.get('HTTP_REFERER', f"/projects/{task.project.pk}/")
    return redirect(next_url)

# ==================== COMMENT VIEWS ====================

@login_required
def comment_add(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    if request.user not in task.project.members.all() and request.user != task.project.created_by:
        messages.error(request, "Only Member of this Project can add Comment")
        return redirect('tasks:project_list')
    
    if request.method == 'POST':
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment added successfully!')
    
    return redirect('tasks:project_detail', pk=task.project.pk)

@login_required
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    project_pk = comment.task.project.pk

    if request.user not in comment.task.project.members.all() and request.user != comment.task.project.created_by:
        messages.error(request, "Only Member of this Project can delete Comment")
        return redirect('tasks:project_list')
    
    if request.user == comment.author:
        comment.delete()
        messages.success(request, 'Comment deleted successfully!')
    else:
        messages.error(request, "You can only delete your own comments")
    
    return redirect('tasks:project_detail', pk=project_pk)

@login_required
def search_projects(request):
    q = request.GET.get('q', '')
    
    projects = Project.objects.filter(
        Q(members=request.user) | Q(created_by=request.user)).distinct()
    
    if q:
        projects = projects.filter(
            Q(title__icontains=q) | Q(description__icontains=q)
        )
    
    return render(request, 'tasks/project_list.html', {
        'projects': projects,
        'search_query': q,
    })

@login_required
def dashboard(request):
    # Get user's projects
    projects = Project.objects.filter(
        Q(members=request.user) | Q(created_by=request.user)
    ).distinct()
    
    # Get all tasks from user's projects
    tasks = Task.objects.filter(
        Q(project__members=request.user) | Q(project__created_by=request.user)
    ).distinct()
    
    # Statistics
    total_projects = projects.count()
    total_tasks = tasks.count()
    
    # Task status counts
    todo_tasks = tasks.filter(status=Task.Status.TODO).count()
    in_progress_tasks = tasks.filter(status=Task.Status.IN_PROGRESS).count()
    done_tasks = tasks.filter(status=Task.Status.DONE).count()
    
    # Task priority counts
    low_priority = tasks.filter(priority=Task.Priority.LOW).count()
    medium_priority = tasks.filter(priority=Task.Priority.MEDIUM).count()
    high_priority = tasks.filter(priority=Task.Priority.HIGH).count()
    urgent_priority = tasks.filter(priority=Task.Priority.URGENT).count()
    
    # Tasks assigned to me
    assigned_to_me = tasks.filter(assigned_to=request.user).count()
    
    # Tasks I created
    created_by_me = tasks.filter(created_by=request.user).count()
    
    # Completion rate
    completion_rate = (done_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Recent tasks (last 7 days)
    now = timezone.now()
    week_ago = now - timezone.timedelta(days=7)
    recent_tasks = tasks.filter(created_at__gte=week_ago).count()
    
    # Projects with most tasks
    projects_with_counts = projects.annotate(task_count=Count('tasks')).order_by('-task_count')[:5]
    
    # Overdue tasks count (for stat card)
    overdue_tasks_count = tasks.filter(
        deadline__lt=now,
        status__in=[Task.Status.TODO, Task.Status.IN_PROGRESS]
    ).count()
    
    # Overdue tasks list (for displaying)
    overdue_tasks_list = tasks.filter(
        deadline__lt=now,
        status__in=[Task.Status.TODO, Task.Status.IN_PROGRESS]
    ).select_related('project', 'assigned_to')[:10]
    
    # Deadline today
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    deadline_today_count = tasks.filter(
        deadline__range=(today_start, today_end),
        status__in=[Task.Status.TODO, Task.Status.IN_PROGRESS]
    ).count()
    
    # Overall project progress
    project_progress = []
    for p in projects:
        total = p.tasks.count()
        done = p.tasks.filter(status=Task.Status.DONE).count()
        progress = (done / total * 100) if total > 0 else 0
        project_progress.append(progress)
    overall_progress = round(sum(project_progress) / len(project_progress), 1) if project_progress else 0
    
    # Top projects with most overdue tasks
    top_overdue_projects = Project.objects.filter(
        Q(members=request.user) | Q(created_by=request.user)
    ).annotate(
        overdue_count=Count('tasks', filter=Q(tasks__deadline__lt=now, tasks__status__in=[Task.Status.TODO, Task.Status.IN_PROGRESS]))
    ).filter(overdue_count__gt=0).order_by('-overdue_count')[:3]
    
    # Recent comments
    recent_comments = Comment.objects.filter(
        Q(task__project__members=request.user) | Q(task__project__created_by=request.user)
    ).select_related('author', 'task__project').order_by('-created_at')[:5]
    
    # Urgent tasks in progress
    urgent_in_progress = tasks.filter(
        priority=Task.Priority.URGENT,
        status=Task.Status.IN_PROGRESS
    ).select_related('project', 'assigned_to')[:5]

    top_users = UserProfile.objects.select_related('user').order_by('-points')[:5]

    context = {
        'total_projects': total_projects,
        'total_tasks': total_tasks,
        'todo_tasks': todo_tasks,
        'in_progress_tasks': in_progress_tasks,
        'done_tasks': done_tasks,
        'low_priority': low_priority,
        'medium_priority': medium_priority,
        'high_priority': high_priority,
        'urgent_priority': urgent_priority,
        'overdue_tasks': overdue_tasks_count,
        'assigned_to_me': assigned_to_me,
        'created_by_me': created_by_me,
        'completion_rate': round(completion_rate, 1),
        'recent_tasks': recent_tasks,
        'projects_with_counts': projects_with_counts,
        'overdue_tasks_list': overdue_tasks_list,
        'deadline_today_count': deadline_today_count,
        'overall_progress': overall_progress,
        'top_overdue_projects': top_overdue_projects,
        'recent_comments': recent_comments,
        'urgent_in_progress': urgent_in_progress,
        'leaderboard': top_users,
    }
    
    return render(request, 'tasks/dashboard.html', context)


@login_required
def upload_attachment(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    
    # Check permission
    if request.user not in task.project.members.all() and request.user != task.project.created_by:
        messages.error(request, 'You do not have permission to upload files.')
        return redirect('tasks:project_detail', pk=task.project.pk)
    
    if request.method == 'POST':
        form = TaskAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.task = task
            attachment.uploaded_by = request.user
            attachment.filename = request.FILES['file'].name
            attachment.file_size = request.FILES['file'].size
            attachment.save()
            messages.success(request, f'File "{attachment.filename}" uploaded successfully!')
    
    return redirect('tasks:project_detail', pk=task.project.pk)


@login_required
def delete_attachment(request, pk):
    attachment = get_object_or_404(TaskAttachment, pk=pk)
    task_pk = attachment.task.project.pk
    
    # Check permission (only uploader or project creator)
    if request.user != attachment.uploaded_by and request.user != attachment.task.project.created_by:
        messages.error(request, 'You do not have permission to delete this file.')
        return redirect('tasks:project_detail', pk=task_pk)
    
    # Delete the file from storage
    attachment.file.delete()
    attachment.delete()
    messages.success(request, 'File deleted successfully!')
    
    return redirect('tasks:project_detail', pk=task_pk)


@login_required
def calendar_view(request):
    return render(request, 'tasks/calendar.html')

@login_required
def calendar_tasks(request, date):
    """Return tasks for a specific date as JSON"""
    try:
        selected_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Get user's projects
    projects = Project.objects.filter(
        Q(members=request.user) | Q(created_by=request.user)
    ).distinct()
    
    # Get tasks with deadline on selected date
    tasks = Task.objects.filter(
        Q(project__members=request.user) | Q(project__created_by=request.user),
        deadline__date=selected_date
    ).select_related('project', 'assigned_to')
    
    tasks_data = []
    for task in tasks:
        tasks_data.append({
            'id': task.id,
            'title': task.title,
            'status': task.status,
            'priority': task.priority,
            'project_title': task.project.title,
            'project_id': task.project.id,
            'assigned_to': task.assigned_to.username if task.assigned_to else 'Unassigned',
            'deadline': task.deadline.strftime('%Y-%m-%d %H:%M') if task.deadline else None,
        })
    
    return JsonResponse({'tasks': tasks_data, 'date': date})


@login_required
def calendar_data(request):
    """Return tasks as JSON for calendar"""
    tasks = Task.objects.filter(
        Q(project__members=request.user) | Q(project__created_by=request.user)
    ).select_related('project', 'assigned_to')
    
    tasks_list = []
    for task in tasks:
        tasks_list.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'deadline': task.deadline.isoformat() if task.deadline else None,
            'project': task.project.id,
            'project_title': task.project.title,
            'assigned_to': task.assigned_to.username if task.assigned_to else None,
        })
    
    return JsonResponse(tasks_list, safe=False)


@login_required
def team_list(request):
    """Show all teams"""
    teams = Team.objects.all()
    user_teams = request.user.teams.all()
    
    return render(request, 'tasks/team_list.html', {
        'teams': teams,
        'user_teams': user_teams,
    })


@login_required
def team_detail(request, pk):
    """Show team details and its members"""
    team = get_object_or_404(Team, pk=pk)
    
    # Check if user is a member of this team (optional - for privacy)
    # if request.user not in team.members.all():
    #     messages.error(request, 'You are not a member of this team.')
    #     return redirect('tasks:team_list')
    
    members = team.members.all()
    
    # Get projects related to this team
    projects = Project.objects.filter(
        Q(created_by__in=members) | Q(members__in=members)
    ).distinct()
    
    return render(request, 'tasks/team_detail.html', {
        'team': team,
        'members': members,
        'projects': projects,
    })

@login_required
def my_tasks(request):
    """Show tasks assigned to the current user"""
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    
    # Start with tasks assigned to current user
    tasks_list = Task.objects.filter(assigned_to=request.user).select_related('project', 'created_by')
    
    # Apply filters
    if status_filter:
        tasks_list = tasks_list.filter(status=status_filter)
    
    if priority_filter:
        tasks_list = tasks_list.filter(priority=priority_filter)
    
    # Pagination
    paginator = Paginator(tasks_list, 10)
    page_number = request.GET.get('page')
    tasks = paginator.get_page(page_number)
    
    # Get counts for badges
    todo_count = Task.objects.filter(assigned_to=request.user, status=Task.Status.TODO).count()
    in_progress_count = Task.objects.filter(assigned_to=request.user, status=Task.Status.IN_PROGRESS).count()
    done_count = Task.objects.filter(assigned_to=request.user, status=Task.Status.DONE).count()
    
    context = {
        'tasks': tasks,
        'todo_count': todo_count,
        'in_progress_count': in_progress_count,
        'done_count': done_count,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
    }
    
    return render(request, 'tasks/my_tasks.html', context)