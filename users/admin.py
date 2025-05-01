from django.contrib import admin

# Register your models here.
from users.models import Solution, User

admin.site.register(Solution)
admin.site.register(User)


# @admin.register(Solution)
# class SolutionAdmin(admin.ModelAdmin):
#     prepopulated_fields = {'slug': ('name',)}

# @admin.register(User)
# class UserAdmin(admin.ModelAdmin):
#     prepopulated_fields = {'slug': ('name',)}