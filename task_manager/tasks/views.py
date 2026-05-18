from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Project, Task, Comment
from .forms import ProjectForm, TaskForm, CommentForm

# ==================== PROJECT VIEWS ====================

@login_required
def project_list(request):
    # Show projects where user is member or creator
    projects = Project.objects.filter(
        Q(members=request.user) | Q(created_by=request.user)
    ).distinct()
    
    return render(request, 'tasks/project_list.html', {'projects': projects})

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Check if user has access
    if request.user not in project.members.all() and request.user != project.created_by:
        messages.error(request, 'You do not have access to this project.')
        return redirect('tasks:project_list')
    
    tasks = project.tasks.all()
    
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
    
    return render(request, 'tasks/task_form.html', {
        'form': form,
        'title': 'Create Task',
        'project': project
    })

@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully!')
            return redirect('tasks:project_detail', pk=task.project.pk)
    else:
        form = TaskForm(instance=task)
    
    return render(request, 'tasks/task_form.html', {
        'form': form,
        'title': 'Edit Task',
        'project': task.project
    })

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    project_pk = task.project.pk
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully!')
        return redirect('tasks:project_detail', pk=project_pk)
    
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})

@login_required
def task_toggle_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
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
    
    if request.user == comment.author:
        comment.delete()
        messages.success(request, 'Comment deleted successfully!')
    
    return redirect('tasks:project_detail', pk=project_pk)

@login_required
def search_projects(request):
    q = request.GET.get('q', '')
    
    projects = Project.objects.all()  # موقتاً
    
    if q:
        projects = projects.filter(
            Q(title__icontains=q) | Q(description__icontains=q)
        )
    
    return render(request, 'tasks/project_list.html', {
        'projects': projects,
        'search_query': q,
    })