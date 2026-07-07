from django.contrib import admin

from .models import ExamSchedule, TimetableEntry

admin.site.register(TimetableEntry)
admin.site.register(ExamSchedule)
