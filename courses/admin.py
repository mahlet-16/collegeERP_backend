from django.contrib import admin

from .models import Course, Department, Enrollment, Program

admin.site.register(Department)
admin.site.register(Program)
admin.site.register(Course)
admin.site.register(Enrollment)
