from django.contrib.auth.models import User
from django import forms
from .models import Project, Task, Comment, TaskAttachment

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'team', 'members']  # اضافه کردن team
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter project title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Project description'}),
            'team': forms.Select(attrs={'class': 'form-control'}),  # اضافه کن
            'members': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['members'].help_text = 'Hold Ctrl to select multiple members'
        self.fields['members'].required = False

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'priority', 'deadline', 'depends_on']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter task title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Task description'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'depends_on': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop('project_id', None)
        super().__init__(*args, **kwargs)
        
        self.fields['assigned_to'].required = False
        self.fields['deadline'].required = False
        self.fields['depends_on'].required = False
        self.fields['depends_on'].help_text = "Select tasks that must be completed before this task."
        
        if project_id:
            self.fields['depends_on'].queryset = Task.objects.filter(project_id=project_id)
        else:
            self.fields['depends_on'].queryset = Task.objects.none()

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text', 'image']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Write a comment...'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
        }

class TaskAttachmentForm(forms.ModelForm):
    class Meta:
        model = TaskAttachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*,.pdf,.doc,.docx,.txt'})
        }