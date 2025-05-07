from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from pytils.translit import slugify

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
        'title': 'Проверка нового курса',
    }

    notebook = request.FILES['notebook']

    slug = slugify("привет ПОПА попная")

        # with open("course_files/"+notebook.name, "wb+") as destination:
        #     for chunk in notebook.chunks():
        #         destination.write(chunk)



    course_name = 'course_name'
    tasks_name = ['task_name', ]
    tasks_description = ['task_description', ]
    tasks_open_asserts = ['task_open_asserts', ]
    tasks_time = ['task_time', ]
    tasks_memory = ['task_memory', ]
    tasks_memory_unit = ['task_memory_unit', ]
    tasks_up_code = ['task_up_code', ]
    tasks_down_code = ['task_down_code', ]

    return render(request, 'main/add_course.html', context)


# @login_required
# def prep(request):

#     context = {
#         'title': 'Добавить новое задание',
#     }
#     if request.method == 'POST':
#         # form = UploadFileForm(request.POST, request.FILES)
#         # if form.is_valid():

#         notebook = request.FILES['notebook']

#         slug = slugify("привет ПОПА попная")

#         # with open("course_files/"+notebook.name, "wb+") as destination:
#         #     for chunk in notebook.chunks():
#         #         destination.write(chunk)



#         course_name = 'course_name'
#         tasks_name = ['task_name', ]
#         tasks_description = ['task_description', ]
#         tasks_open_asserts = ['task_open_asserts', ]
#         tasks_time = ['task_time', ]
#         tasks_memory = ['task_memory', ]
#         tasks_memory_unit = ['task_memory_unit', ]
#         tasks_up_code = ['task_up_code', ]
#         tasks_down_code = ['task_down_code', ]



#         # Courses.objects.create(
#         #     name=course_name,
#         #     notebook=notebook
#         # )

#     return render(request, 'main/add_course.html', context)
