from django.db import models
from django.contrib.auth.models import AbstractUser
from course.models import Tasks



class User(AbstractUser):
    # solutions = models.ForeignKey(to=Solution, on_delete=models.PROTECT)

    class Meta:
        db_table = 'user'
        verbose_name = 'Пользователи'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Solution(models.Model):
    user_code = models.TextField(verbose_name='Код пользователя')
    text = models.TextField(blank=True, null=True, verbose_name='Ошибки в коде')
    timestamp = models.DateTimeField(verbose_name='Время загрузки')
    task = models.ForeignKey(to=Tasks, on_delete=models.CASCADE, verbose_name='Задание')
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, verbose_name='Пользователь')
    time = models.DecimalField(default=0.00, decimal_places=2, max_digits=7, verbose_name='Время')
    memory = models.PositiveIntegerField(default=0, verbose_name='Память')
    score = models.DecimalField(default=0.00, decimal_places=2, max_digits=7, verbose_name='Результат')

    class Meta:
        db_table = 'solution'
        verbose_name = 'Решение'
        verbose_name_plural = 'Решения'

    def __str__(self):
        return self.user_code
