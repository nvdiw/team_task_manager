from rest_framework import viewsets, permissions
from django.db.models import Q
from tasks.models import Project, Task, Comment
from .serializers import ProjectSerializer, TaskSerializer, CommentSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Project.objects.none()
    
    def get_queryset(self):
        return Project.objects.filter(
            Q(members=self.request.user) | Q(created_by=self.request.user)
        ).distinct()


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Task.objects.none()
    
    def get_queryset(self):
        return Task.objects.filter(
            Q(project__members=self.request.user) | Q(project__created_by=self.request.user)
        ).distinct()


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Comment.objects.none()
    
    def get_queryset(self):
        return Comment.objects.filter(
            Q(task__project__members=self.request.user) | Q(task__project__created_by=self.request.user)
        ).distinct()