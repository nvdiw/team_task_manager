from django.urls import path
from django.http import HttpResponse

app_name = 'tasks'

# Temporary placeholder - will be replaced in Phase 3
urlpatterns = [
    path('', lambda request: HttpResponse("Task Manager - Working! Proceed to Phase 3")),
]