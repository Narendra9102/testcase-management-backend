from django.contrib import admin
from .models import Project, TestCase, ProjectMember, TestExecution

# Register your models here.

admin.site.register(Project)
admin.site.register(ProjectMember)
admin.site.register(TestCase)
admin.site.register(TestExecution)
