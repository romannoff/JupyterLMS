from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from course.models import Courses

@login_required
def index(request):

    courses = Courses.objects.all()

    context = {
        'title': 'Доступные курсы',
        'courses': courses
    }

    return render(request, 'main/index.html', context)

@login_required
def prep(request):

    context = {
        'title': 'Добавить новое задание',
    }

    return render(request, 'main/add_course.html', context)
