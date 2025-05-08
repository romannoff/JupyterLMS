from django.urls import path

from course import views

app_name = 'course'

urlpatterns = [
    path('<slug:subject_slug>/', views.subject, name='subject'),
    path('task/<slug:task_slug>/', views.task, name='task'),
]