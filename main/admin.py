from django.contrib import admin
from .models import ClassCollective, Parent, Student, ParentRelationship

class StudentInline(admin.TabularInline):
    model = Student
    extra = 1
    fields = ("first_name", "last_name", "school_class")

class ParentRelationshipInline(admin.TabularInline):
    model = ParentRelationship

@admin.register(ClassCollective)
class ClassCollectiveAdmin(admin.ModelAdmin):
    list_display = ("school_class", "year", "variant")
    list_filter = ("school_class",)
    search_fields = ("school_class", "year", "variant")
    inlines = [StudentInline]


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "phone_number")
    inlines = [ParentRelationshipInline]

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "school_class")
    inlines = [ParentRelationshipInline]
    search_fields = ("first_name", "last_name", "school_class")


