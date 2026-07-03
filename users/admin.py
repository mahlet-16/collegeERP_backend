from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AuditLog, Notification, StudentProfile, SystemSetting, TeacherProfile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
	fieldsets = UserAdmin.fieldsets + (("ERP", {"fields": ("role", "phone")}),)
	list_display = ("username", "email", "role", "is_staff", "is_active")


admin.site.register(StudentProfile)
admin.site.register(TeacherProfile)
admin.site.register(Notification)
admin.site.register(AuditLog)
admin.site.register(SystemSetting)
