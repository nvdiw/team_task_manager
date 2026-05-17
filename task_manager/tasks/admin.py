from django.contrib import admin
from .models import Project, Task, Comment

# Inline admin for Tasks inside Project
class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ['title', 'status', 'priority', 'assigned_to', 'deadline']
    show_change_link = True

# Inline admin for Comments inside Task
class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ['author', 'text', 'created_at']
    readonly_fields = ['created_at']

# Project Admin
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'created_at', 'member_count']
    list_filter = ['created_at', 'members']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [TaskInline]
    
    fieldsets = (
        ('Main Information', {
            'fields': ('title', 'description')
        }),
        ('User Management', {
            'fields': ('created_by', 'members')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = "Member Count"

# Task Admin
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'status', 'priority', 'assigned_to', 'deadline', 'is_overdue']
    list_filter = ['status', 'priority', 'project', 'assigned_to']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CommentInline]
    
    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description', 'project')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'created_by')
        }),
        ('Schedule', {
            'fields': ('deadline', 'created_at', 'updated_at')
        }),
    )
    
    def is_overdue(self, obj):
        if obj.deadline and obj.status != Task.Status.DONE:
            from django.utils import timezone
            return obj.deadline < timezone.now()
        return False
    is_overdue.boolean = True
    is_overdue.short_description = "Overdue"

# Comment Admin
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'author', 'short_text', 'created_at']
    list_filter = ['created_at', 'author']
    search_fields = ['text']
    readonly_fields = ['created_at']
    
    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    short_text.short_description = "Comment Preview"