from django.http import HttpResponse
from django.shortcuts import render

def index(request):
    return HttpResponse('Home page')

def task(request):
    return HttpResponse('Task page')

