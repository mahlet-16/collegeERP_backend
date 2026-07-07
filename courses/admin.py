from django.contrib import admin

from .models import AcademicYear, Classroom, College, Course, Department, Enrollment, Program, Section, Semester

admin.site.register(College)
admin.site.register(Department)
admin.site.register(Program)
admin.site.register(AcademicYear)
admin.site.register(Semester)
admin.site.register(Section)
admin.site.register(Classroom)
admin.site.register(Course)
admin.site.register(Enrollment)
