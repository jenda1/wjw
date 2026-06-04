from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import MyUser


@admin.register(MyUser)
class MyUserAdmin(UserAdmin):
    # Optimize DB queries with an SQL JOIN
    list_select_related = ['profile']

    # Add 'profile' to the edit and creation forms
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('profile',)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('profile',)}),
    )

    # Main grid list configuration
    list_display = ['email', 'get_profile_name']

    @admin.display(description='Profile Name')
    def get_profile_name(self, instance):
        return instance.profile.name if instance.profile else 'No Profile Assigned'

    @admin.display(description='Phone Number')
    def get_phone_number(self, instance):
        return instance.profile.phone_number if instance.profile else ''
