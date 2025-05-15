from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from course.models import Tasks, Courses

class CourseCreationForm(forms.Form):

    class Meta:
        model = Courses

    name = forms.CharField()

class TaskCreationForm(forms.Form):

    class Meta:
        model = Tasks
    
    id = forms.CharField()
    name = forms.CharField()
    up_code = forms.Textarea()
    down_code = forms.Textarea()
    open_assert = forms.Textarea()
    close_assert = forms.Textarea()
    description = forms.Textarea()
    time = forms.DecimalField()
    memory = forms.DecimalField()
    no = forms.IntegerField()