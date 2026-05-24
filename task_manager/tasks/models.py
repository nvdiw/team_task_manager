from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.db.models import Q

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
    team = models.ForeignKey('Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Updated")
    graph_node_positions = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return self.title
    
    def incomplete_tasks_count(self):
        """Return number of incomplete tasks (TODO and IN_PROGRESS)"""
        return self.tasks.exclude(status=Task.Status.DONE).count()

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
    points_awarded = models.BooleanField(default=False)
    depends_on = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='blocked_tasks')

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ['-priority', 'deadline']
    
    def get_activities(self):
        """Return all activities (comments + attachments) sorted by time"""
        activities = []
        
        # Add comments
        for comment in self.comments.all():
            activities.append({
                'type': 'comment',
                'date': comment.created_at,
                'data': comment,
                'author': comment.author,
                'text': comment.text
            })
        
        # Add attachments (if the model exists)
        if hasattr(self, 'attachments'):
            for attachment in self.attachments.all():
                activities.append({
                    'type': 'attachment',
                    'date': attachment.uploaded_at,
                    'data': attachment,
                    'author': attachment.uploaded_by,
                    'filename': attachment.filename,
                    'file_url': attachment.file.url,
                    'file_size': attachment.file_size
                })
        
        # Sort by date (newest first)
        activities.sort(key=lambda x: x['date'], reverse=True)
        
        return activities


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
    image = models.ImageField(upload_to='comment_images/%Y/%m/%d/', null=True, blank=True, verbose_name="Image")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"
    
    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ['created_at']


class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='task_attachments/%Y/%m/%d/')
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="File size in bytes")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.filename
    
    class Meta:
        ordering = ['-uploaded_at']


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(User, related_name='teams', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    icon = models.CharField(max_length=50, default='fas fa-users')
    
    def __str__(self):
        return self.name
    
    def member_count(self):
        return self.members.count()
    
    class Meta:
        ordering = ['name']


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    points = models.IntegerField(default=0)
    total_tasks_completed = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.points} pts"

    def level(self):
        # every 100 scores = 1 Level
        return (self.points // 100) + 1

    class Meta:
        ordering = ['-points']


class PointTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='point_transactions')
    task = models.ForeignKey('Task', on_delete=models.CASCADE)
    points_earned = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.username} +{self.points_earned} for task {self.task.id}"