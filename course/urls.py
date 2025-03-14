from django.urls import path

from course import views

app_name = 'course'

urlpatterns = [
    path('', views.subject, name='subject'),
    path('task/', views.task, name='task'),
]