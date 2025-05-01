from django.db import models


class Courses(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name='Название курса')
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True, verbose_name='URL')

    class Meta:
        db_table = 'course'
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'

    def __str__(self):
        return self.name


class Tasks(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name='Название заадния')
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True, verbose_name='URL')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    notebook = models.FileField(upload_to='course_files', verbose_name='Блокнот')
    time = models.DecimalField(default=0.00, decimal_places=2, max_digits=7, verbose_name='Время')
    memory = models.PositiveIntegerField(default=0, verbose_name='Память')
    memory_unit = models.CharField(max_length=15, verbose_name='Единицы измерения памяти')
    course = models.ForeignKey(to=Courses, on_delete=models.PROTECT)


    class Meta:
        db_table = 'task'
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'

    def __str__(self):
        return self.name