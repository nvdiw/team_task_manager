from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Project Model
class Project(models.Model):
    title = models.CharField(max_length=200, verbose_name="Project Title")
    description = models.TextField(verbose_name="Description", blank=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='projects_created',
        verbose_name="Created By"
    )
    members = models.ManyToManyField(
        User, 
        related_name='projects',
        blank=True,
        verbose_name="Team Members"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Updated")
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ['-created_at']


# Task Model
class Task(models.Model):
    # Status Choices
    class Status(models.TextChoices):
        TODO = 'TODO', 'To Do'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        DONE = 'DONE', 'Done'
    
    # Priority Choices
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'
    
    title = models.CharField(max_length=200, verbose_name="Task Title")
    description = models.TextField(verbose_name="Description", blank=True)
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='tasks',
        verbose_name="Related Project"
    )
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_tasks',
        verbose_name="Assigned To"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_tasks',
        verbose_name="Created By"
    )
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.TODO,
        verbose_name="Status"
    )
    priority = models.CharField(
        max_length=20, 
        choices=Priority.choices, 
        default=Priority.MEDIUM,
        verbose_name="Priority"
    )
    deadline = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Deadline"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Updated")
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ['-priority', 'deadline']


# Comment Model
class Comment(models.Model):
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name="Task"
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name="Author"
    )
    text = models.TextField(verbose_name="Comment Text")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"
    
    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ['created_at']