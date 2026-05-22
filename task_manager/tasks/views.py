from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Project, Task, Comment
from .forms import ProjectForm, TaskForm, CommentForm


# ==================== PROJECT VIEWS ====================

@login_required
def project_list(request):
    # Show projects where user is member or creator
    projects_list = Project.objects.filter(
        Q(members=request.user) | Q(created_by=request.user)
    ).distinct()
    
    paginator = Paginator(projects_list, 5)
    page_number = request.GET.get('page')
    projects = paginator.get_page(page_number)
    
    return render(request, 'tasks/project_list.html', {'projects': projects})

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Check if user has access
    if request.user not in project.members.all() and request.user != project.created_by:
        messages.error(request, 'You do not have access to this project.')
        return redirect('tasks:project_list')
    
    tasks_list = project.tasks.all()
    
    # Pagination for tasks
    paginator = Paginator(tasks_list, 5)  # 5 tasks per page
    page_number = request.GET.get('page')
    tasks = paginator.get_page(page_number)
    
    return render(request, 'tasks/project_detail.html', {
        'project': project,
        'tasks': tasks,
    })

@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            form.save_m2m()  # Save many-to-many members
            messages.success(request, 'Project created successfully!')
            return redirect('tasks:project_detail', pk=project.pk)
    else:
        form = ProjectForm()
    
    return render(request, 'tasks/project_form.html', {'form': form, 'title': 'Create Project'})

@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Check if user is creator
    if request.user != project.created_by:
        messages.error(request, 'Only the project creator can edit this project.')
        return redirect('tasks:project_detail', pk=pk)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully!')
            return redirect('tasks:project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    
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
        form.fields['assigned_to'].queryset = project.members.all()
    
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
        form.fields['assigned_to'].queryset = task.project.members.all()
    
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

    if request.user not in task.project.members.all() and request.user != task.project.created_by:
        messages.error(request, "You don't have access to this task")
        return redirect('tasks:project_list')

    # Cycle status: TODO -> IN_PROGRESS -> DONE -> TODO
    if task.status == Task.Status.TODO:
        task.status = Task.Status.IN_PROGRESS
    elif task.status == Task.Status.IN_PROGRESS:
        task.status = Task.Status.DONE
    else:
        task.status = Task.Status.TODO
    
    task.save()
    messages.success(request, f'Task status changed to {task.get_status_display()}')
    return redirect('tasks:project_detail', pk=task.project.pk)

# ==================== COMMENT VIEWS ====================

@login_required
def comment_add(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    if request.user not in task.project.members.all() and request.user != task.project.created_by:
        messages.error(request, "Only Member of this Project can add Comment")
        return redirect('tasks:project_list')
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
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
    
    # Overdue tasks (deadline passed and not done)
    now = timezone.now()
    overdue_tasks = tasks.filter(
        deadline__lt=now,
        status__in=[Task.Status.TODO, Task.Status.IN_PROGRESS]
    ).count()
    
    # Tasks assigned to me
    assigned_to_me = tasks.filter(assigned_to=request.user).count()
    
    # Tasks I created
    created_by_me = tasks.filter(created_by=request.user).count()
    
    # Completion rate
    completion_rate = (done_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Recent tasks (last 7 days)
    week_ago = now - timezone.timedelta(days=7)
    recent_tasks = tasks.filter(created_at__gte=week_ago).count()
    
    # Projects with most tasks
    projects_with_counts = projects.annotate(task_count=Count('tasks')).order_by('-task_count')[:5]
    
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
        'overdue_tasks': overdue_tasks,
        'assigned_to_me': assigned_to_me,
        'created_by_me': created_by_me,
        'completion_rate': round(completion_rate, 1),
        'recent_tasks': recent_tasks,
        'projects_with_counts': projects_with_counts,
    }
    
    return render(request, 'tasks/dashboard.html', context)