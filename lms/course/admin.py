from django.contrib import admin

from course.models import Courses, Tasks


@admin.register(Courses)
class CoursesAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Tasks)
class TasksAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}