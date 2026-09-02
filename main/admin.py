from typing import final

from allauth.socialaccount.models import SocialAccount
from django import forms
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html, format_html_join
from hijack.contrib.admin import HijackUserAdminMixin
from import_export.admin import ImportExportMixin
from import_export.forms import ConfirmImportForm, ImportForm
from simple_history.admin import SimpleHistoryAdmin

from main.models import (
    Circle,
    CircleMembership,
    ClassCollective,
    ClassRepresentative,
    ParentRelationship,
    Profile,
    ProfileMergeRequest,
    ProfileStudentRequest,
    Student,
)
from main.resources import StudentResource
from main.setup_checks import check_setup

# Django admin (Jazzmin) bundluje Font Awesome, ne Bootstrap Icons používané na veřejných stránkách.
SOCIAL_PROVIDER_ICONS = {
    'google': 'fab fa-google',
}


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
class ClassRepresentativeInlineForClass(admin.TabularInline):
    model = ClassRepresentative
    fk_name = "school_class"
    extra = 1
    autocomplete_fields = ["representative"]
    verbose_name = "Zástupce"
    verbose_name_plural = "Zástupci třídy"


@final
class ClassRepresentativeInlineForProfile(admin.TabularInline):
    model = ClassRepresentative
    fk_name = "representative"
    extra = 1
    autocomplete_fields = ["school_class"]
    verbose_name = "Zastupovaná třída"
    verbose_name_plural = "Zastupované třídy"


@final
class CircleMembershipInlineForCircle(admin.TabularInline):
    model = CircleMembership
    fk_name = "circle"
    extra = 1
    autocomplete_fields = ["profile"]
    verbose_name = "Člen kruhu"
    verbose_name_plural = "Členové kruhu"


@final
class CircleMembershipInlineForProfile(admin.TabularInline):
    model = CircleMembership
    fk_name = "profile"
    extra = 1
    autocomplete_fields = ["circle"]
    verbose_name = "Kruh"
    verbose_name_plural = "Kruhy"


class SocialAccountInlineChecks(admin.checks.InlineModelAdminChecks):
    """SocialAccount nemá FK na Profile (jen na auth.User), takže standardní kontrolu
    vztahu vypínáme - vazbu řeší SocialAccountInline.get_formset."""
    def _check_relation(self, obj, parent_model):
        return []


@final
class SocialAccountInline(admin.TabularInline):
    """SocialAccount má FK na auth.User, ne na Profile - formset proto při vytváření
    přesměruje `instance` z Profile na jeho `.user`, aby šlo účty editovat přímo tady."""
    model = SocialAccount
    extra = 0
    fields = ("provider", "uid")
    verbose_name = "Propojený účet"
    verbose_name_plural = "Propojené účty"
    checks_class = SocialAccountInlineChecks

    def get_formset(self, request, obj=None, **kwargs):
        base_formset = forms.inlineformset_factory(
            get_user_model(), SocialAccount,
            fields=self.fields, extra=self.extra, can_delete=self.can_delete,
        )

        class ProfileAwareFormSet(base_formset):
            def __init__(inner_self, *args, instance=None, **inner_kwargs):
                if isinstance(instance, Profile):
                    instance = instance.user
                super().__init__(*args, instance=instance, **inner_kwargs)

        return ProfileAwareFormSet


@final
@admin.register(ClassCollective)
class ClassCollectiveAdmin(SimpleHistoryAdmin):
    list_display = ("school_class_display", "variant", "year", "student_count")
    # list_display = ("school_class", "year", "variant")
    list_filter = ("year", "school_class")
    search_fields = ("school_class", "year", "variant")
    ordering = ("-year", "school_class", "variant")
    inlines = [StudentInline, ClassRepresentativeInlineForClass]

    @admin.display(description="Třída")
    def school_class_display(self, obj):
        return obj.get_school_class_display() or "Nespecifikováno"

    @admin.display(description="Počet žáků")
    def student_count(self, obj):
        # Spočítá žáky ve třídě (využívá related_name="students")
        return obj.students.count()


@final
@admin.register(Circle)
class CircleAdmin(SimpleHistoryAdmin):
    list_display = ("name", "tags_list", "member_count", "page_count")
    search_fields = ("name", "tags__name")
    ordering = ("name",)
    inlines = [CircleMembershipInlineForCircle]

    @admin.display(description="Počet členů")
    def member_count(self, obj):
        return obj.members.count()

    @admin.display(description="Počet stránek")
    def page_count(self, obj):
        return obj.pages.count()

    @admin.display(description="Tagy")
    def tags_list(self, obj):
        return ", ".join(tag.name for tag in obj.tags.all()) or "---"


@final
@admin.register(Profile)
class ProfileAdmin(HijackUserAdminMixin, SimpleHistoryAdmin):
    list_display = ("full_name", "email", "phone_number", "membership", "status_badge", "social_accounts", "created_at")
    list_filter = ("status", "membership", "city")
    search_fields = ("user__first_name", "user__last_name", "user__email", "phone_number", "city")
    ordering = ("user__last_name", "user__first_name")
    # Použití upraveného inline s novým pojmenováním
    inlines = [
        StudentInlineForParent, SocialAccountInline, ClassRepresentativeInlineForProfile,
        CircleMembershipInlineForProfile,
    ]

    autocomplete_fields = ["user"]
    readonly_fields = ("created_at",)

    fieldsets = (
        ("Účet", {
            "fields": ("user", "created_at")
        }),
        ("Osobní údaje", {
            "fields": ("birth_date",)
        }),
        ("Kontaktní údaje", {
            "fields": ("phone_number", "phone_visible")
        }),
        ("Adresa (Ověřuje se přes Mapy.cz)", {
            "fields": ("street_and_number", "city", "zip_code")
        }),
        ("Nastavení členství", {
            "fields": ("membership", "status", "comments")
        }),
    )

    def get_hijack_user(self, obj):
        # HijackUserAdminMixin ze základu předpokládá, že admin spravuje přímo User -
        # tady spravuje Profile, takže mu musíme ukázat na propojený účet.
        return obj.user

    @admin.display(description="Celé jméno", ordering="user__last_name")
    def full_name(self, obj):
        return f"{obj.user.last_name} {obj.user.first_name}"

    @admin.display(description="Email")
    def email(self, obj):
        return obj.user.email

    @admin.display(description="Propojené účty")
    def social_accounts(self, obj):
        accounts = obj.user.socialaccount_set.all()
        if not accounts:
            return "---"

        def account_row(account):
            icon = SOCIAL_PROVIDER_ICONS.get(account.provider, 'fas fa-user-circle')
            identifier = (
                account.extra_data.get('email')
                or account.extra_data.get('username')
                or account.user.username
            )
            return (icon, identifier)

        return format_html_join(
            ", ", '<i class="{}"></i> {}', (account_row(account) for account in accounts)
        )

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
class StudentImportForm(ImportForm):
    school_class = forms.ModelChoiceField(
        queryset=ClassCollective.objects.all(),
        label="Třída",
        help_text="Všichni žáci ze souboru budou přiřazeni do této třídy.",
    )


@final
class StudentConfirmImportForm(ConfirmImportForm):
    school_class = forms.ModelChoiceField(
        queryset=ClassCollective.objects.all(),
        widget=forms.HiddenInput(),
    )


@final
@admin.register(Student)
class StudentAdmin(ImportExportMixin, SimpleHistoryAdmin):
    resource_classes = [StudentResource]
    import_form_class = StudentImportForm
    confirm_form_class = StudentConfirmImportForm

    list_display = ("full_name", "school_class", "get_parents")
    list_filter = ("school_class__year", "school_class")
    search_fields = ("first_name", "last_name")
    ordering = ("last_name", "first_name")
    inlines = [ParentInline,]

    def get_confirm_form_initial(self, request, import_form):
        initial = super().get_confirm_form_initial(request, import_form)
        cleaned_data = getattr(import_form, "cleaned_data", None) or {}
        if "school_class" in cleaned_data:
            initial["school_class"] = cleaned_data["school_class"].pk
        return initial

    def get_import_resource_kwargs(self, request, **kwargs):
        resource_kwargs = super().get_import_resource_kwargs(request, **kwargs)
        form = kwargs.get("form")
        # Na první (nevalidovaný) render importní stránky ještě `cleaned_data` neexistuje.
        cleaned_data = getattr(form, "cleaned_data", None) or {}
        if "school_class" in cleaned_data:
            resource_kwargs["school_class"] = cleaned_data["school_class"]
        return resource_kwargs

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
    list_display = ("user", "old_email", "first_name", "last_name", "student_by_name", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username", "old_email", "first_name", "last_name")
    autocomplete_fields = ["student_by_name"]

@final
@admin.register(ProfileStudentRequest)
class ProfileStudentRequestAdmin(admin.ModelAdmin):
    list_display = ("profile", "action", "first_name", "last_name", "student_by_name", "status", "created_at")
    list_filter = ("action", "status")
    search_fields = ("profile__user__last_name", "first_name", "last_name")
    autocomplete_fields = ["profile", "student_by_name"]


admin.site.unregister(Group)


@final
@admin.register(Group)
class SetupCheckingGroupAdmin(GroupAdmin):
    """Standardní GroupAdmin doplněný o varování při nekonzistenci v přiřazení
    rolí/skupin (viz main.setup_checks.check_setup) - právě tady se tyto
    nesrovnalosti opravují, takže se hlásí přímo na této stránce."""

    def changelist_view(self, request, extra_context=None):
        for issue in check_setup():
            messages.warning(request, issue)
        return super().changelist_view(request, extra_context=extra_context)
