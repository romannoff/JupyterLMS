from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from pytils.translit import slugify

# from markdown_deux  import markdown
from mdtex2html import convert

from course.models import Courses, Tasks
from course.src.jupyter_parser import jupyter_parser
from main.forms import TaskCreationForm, CourseCreationForm

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

    notebook = request.FILES['notebook']

    with open("course_files/"+notebook.name, "wb+") as destination:
        for chunk in notebook.chunks():
            destination.write(chunk)

    parse_res = jupyter_parser("course_files/"+notebook.name)

    course_form = CourseCreationForm(
        data={
            'name': parse_res['course_name'],
        }
    )

    tasks = []
    no = 0
    for task in parse_res['tasks']:
        task_form = TaskCreationForm(
            data={
                'id': task['task_id'],
                'name': task['task_name'],
                'time': task['time_limit'],
                'memory': task['memory_limit'],
                'no': no
            }
        )
        task_form.up_code = task['backbone']
        task_form.down_code = 'return SOMETHING'
        task_form.open_assert = task['open_tests']
        task_form.close_assert = 'CLOSE ASSERT'
        task_form.description = task['task_description']
        no += 1
        tasks.append(task_form)


    context = {
        'title': 'Проверка нового курса',
        'form': course_form,
        'tasks': tasks,
        'len_task': len(tasks),
        'notebook': notebook,
    }
    return render(request, 'main/add_course.html', context)


@login_required
def save(request):

    course = Courses.objects.filter(slug=slugify(request.POST['course_name']))
    if course:
        course.update(notebook=request.POST['notebook'])
        course = course.first()
    else:
        course = Courses.objects.create(
            name=request.POST['course_name'],
            notebook=request.POST['notebook'],
            slug=slugify(request.POST['course_name']),
        )

    for i in range(int(request.POST['len_task'])):
        task = Tasks.objects.filter(slug=slugify(request.POST['course_name'])+'---'+slugify(request.POST[f'task_name-{i}']))
        if task:
            task.update(
                numb_of_task=request.POST[f'task_id-{i}'],
                up_code=request.POST[f'task_up_code-{i}'],
                down_code=request.POST[f'task_down_code-{i}'],
                open_assert=request.POST[f'task_open_assert-{i}'],
                close_assert=request.POST[f'task_close_assert-{i}'],
                description=convert(request.POST[f'task_description-{i}']),
                time=float(request.POST[f'task_time-{i}'].replace(',', '.')),
                memory=float(request.POST[f'task_memory-{i}'].replace(',', '.')),
                )
        else:
            Tasks.objects.create(
                numb_of_task=request.POST[f'task_id-{i}'],
                name=request.POST[f'task_name-{i}'],
                up_code=request.POST[f'task_up_code-{i}'],
                down_code=request.POST[f'task_down_code-{i}'],
                open_assert=request.POST[f'task_open_assert-{i}'],
                close_assert=request.POST[f'task_close_assert-{i}'],
                slug=slugify(request.POST['course_name'])+'---'+slugify(request.POST[f'task_name-{i}']),
                description=convert(request.POST[f'task_description-{i}']),
                time=float(request.POST[f'task_time-{i}'].replace(',', '.')),
                memory=float(request.POST[f'task_memory-{i}'].replace(',', '.')),
                course=course,
            )

    return redirect(reverse('main:index'))
