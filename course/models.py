from django.db import models


class Courses(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name='Название курса')
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True, verbose_name='URL')
    notebook = models.FileField(blank=True, null=True, upload_to='course_files', verbose_name='Блокнот')

    class Meta:
        db_table = 'course'
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'

    def __str__(self):
        return self.name


class Tasks(models.Model):
    name = models.CharField(max_length=150, verbose_name='Название задания')
    up_code = models.TextField(blank=True, null=True, verbose_name='Код, выше кода пользователя')
    down_code = models.TextField(blank=True, null=True, verbose_name='Код, ниже кода пользователя')
    open_assert = models.TextField(blank=True, null=True, verbose_name='Открытые тесты')
    close_assert = models.TextField(blank=True, null=True, verbose_name='Закрытые тесты')
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True, verbose_name='URL')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    time = models.DecimalField(default=0.00, decimal_places=2, max_digits=7, verbose_name='Время')
    memory = models.DecimalField(default=0.00, decimal_places=2, max_digits=7, verbose_name='Память')
    # memory_unit = models.CharField(max_length=15, verbose_name='Единицы измерения памяти')
    course = models.ForeignKey(to=Courses, on_delete=models.CASCADE)


    class Meta:
        db_table = 'task'
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'

    def __str__(self):
        return self.name