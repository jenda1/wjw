from typing import final

from django.utils.html import format_html
from django.contrib import admin

from main.models import ClassCollective, ParentRelationship, Profile, ProfileMergeRequest, ProfileStudentRequest, Student


@final
class StudentInline(admin.TabularInline):
    model = Student
    extra = 1
    fields = ("first_name", "last_name", "birth_date")
    verbose_name = "Žák"
    verbose_name_plural = "Žáci ve třídě"


@final
class StudentInlineForParent(admin.TabularInline):
    model = ParentRelationship
    fk_name = "parent"
    extra = 1
    autocomplete_fields = ["student"]
    verbose_name = "Žák"
    verbose_name_plural = "Žáci"


@final
class ParentInline(admin.TabularInline):
    model = ParentRelationship
    fk_name = "student"
    extra = 1
    autocomplete_fields = ["parent"]
    verbose_name = "Zákonný zástupce"
    verbose_name_plural = "Zákonní zástupci"


@final
@admin.register(ClassCollective)
class ClassCollectiveAdmin(admin.ModelAdmin):
    list_display = ("school_class_display", "variant", "year", "student_count")
    # list_display = ("school_class", "year", "variant")
    list_filter = ("year", "school_class")
    search_fields = ("school_class", "year", "variant")
    ordering = ("-year", "school_class", "variant")
    inlines = [StudentInline]

    @admin.display(description="Třída")
    def school_class_display(self, obj):
        return obj.get_school_class_display() or "Nespecifikováno"

    @admin.display(description="Počet žáků")
    def student_count(self, obj):
        # Spočítá žáky ve třídě (využívá related_name="students")
        return obj.students.count()


@final
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone_number", "membership", "status_badge")
    list_filter = ("status", "membership", "city")
    search_fields = ("user__first_name", "user__last_name", "user__email", "phone_number", "city")
    ordering = ("user__last_name", "user__first_name")
    # Použití upraveného inline s novým pojmenováním
    inlines = [StudentInlineForParent]

    autocomplete_fields = ["user"]

    fieldsets = (
        ("Účet", {
            "fields": ("user",)
        }),
        ("Osobní údaje", {
            "fields": ("birth_date",)
        }),
        ("Kontaktní údaje", {
            "fields": ("phone_number",)
        }),
        ("Adresa (Ověřuje se přes Mapy.cz)", {
            "fields": ("street_and_number", "city", "zip_code")
        }),
        ("Nastavení členství", {
            "fields": ("membership", "status", "comments")
        }),
    )

    @admin.display(description="Celé jméno", ordering="user__last_name")
    def full_name(self, obj):
        return f"{obj.user.last_name} {obj.user.first_name}"

    @admin.display(description="Email")
    def email(self, obj):
        return obj.user.email

    @admin.display(description="Stav")
    def status_badge(self, obj):
        colors = {
            Profile.ProfileStatus.PENDING: "orange",
            Profile.ProfileStatus.ACTIVE: "green",
            Profile.ProfileStatus.CANCELLED: "red",
        }
        color = colors.get(obj.status, "black")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )


@final
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "school_class", "get_parents")
    list_filter = ("school_class__year", "school_class")
    search_fields = ("first_name", "last_name")
    ordering = ("last_name", "first_name")
    inlines = [ParentInline,]

    @admin.display(description="Celé jméno", ordering="last_name")
    def full_name(self, obj):
        return f"{obj.last_name} {obj.first_name}"

    @admin.display(description="Zákonní zástupci")
    def get_parents(self, obj):
        parents = obj.parents.all()
        return ", ".join([f"{p.user.first_name} {p.user.last_name}" for p in parents]) or "---"


@final
@admin.register(ProfileMergeRequest)
class ProfileMergeRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "old_email", "student_name", "student_by_rc_linked")
    search_fields = ("user__username", "old_email", "student_name")
    autocomplete_fields = ["student_by_rc"]

@final
@admin.register(ProfileStudentRequest)
class ProfileStudentRequestAdmin(admin.ModelAdmin):
    list_display = ("profile", "action", "student_name", "student_by_rc")
    list_filter = ("action",)
    search_fields = ("profile__user__last_name", "student_name")
    autocomplete_fields = ["profile", "student_by_rc"]


@admin.register(ParentRelationship)
class ParentRelationshipAdmin(admin.ModelAdmin):
    list_display = ("parent", "student", "valid_from", "valid_until")
    search_fields = ("parent__user__last_name", "student__last_name")
    autocomplete_fields = ["parent", "student"]
