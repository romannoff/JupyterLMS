from django.urls import path

from main import views

app_name = 'main'

urlpatterns = [
    path('', views.index, name='index'),
    path('prep/', views.prep, name='prep'),
    path('save/', views.save, name='save'),
]