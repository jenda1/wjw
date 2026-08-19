from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

WELCOMING_TEAM_GROUP_NAME = "WelcomingTeam"
VR_MEMBER_GROUP_NAME = "VRmember"
CAPO_DI_TUTTI_GROUP_NAME = "CapoDiTutti"
SECRETARY_OF_THE_TREASURY_GROUP_NAME = "SecretaryOfTheTreasury"
WAGTAIL_EDITORS_GROUP_NAME = "Editors"  # vestavěná Wagtail skupina (wagtailcore 0002_initial_data)
WAGTAIL_MODERATORS_GROUP_NAME = "Moderators"  # vestavěná Wagtail skupina (wagtailcore 0002_initial_data)


APPROVER_GROUP_NAMES = [WELCOMING_TEAM_GROUP_NAME, CAPO_DI_TUTTI_GROUP_NAME, SECRETARY_OF_THE_TREASURY_GROUP_NAME]


def can_approve_requests(user) -> bool:
    """Členové skupiny WelcomingTeam, CapoDiTutti a SecretaryOfTheTreasury (a superuživatelé)
    mohou schvalovat žádosti (o členství, sloučení účtů, přidání žáka)."""
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name__in=APPROVER_GROUP_NAMES).exists()
    )


def approver_required(view_func):
    """Nahrazuje staff_member_required - přístup mají členové skupiny WelcomingTeam."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not can_approve_requests(request.user):
            raise PermissionDenied("Nemáte oprávnění schvalovat žádosti.")
        return view_func(request, *args, **kwargs)

    return login_required(wrapper)


VIEW_OTHERS_GROUP_NAMES = [VR_MEMBER_GROUP_NAME, CAPO_DI_TUTTI_GROUP_NAME, SECRETARY_OF_THE_TREASURY_GROUP_NAME]


def can_view_others(user) -> bool:
    """Členové skupiny VRmembers, CapoDiTutti a SecretaryOfTheTreasury (a superuživatelé)
    mohou videt data o vsech clenech (o členství, sloučení účtů, přidání žáka)."""
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name__in=VIEW_OTHERS_GROUP_NAMES).exists()
    )


def view_others_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not can_view_others(request.user):
            raise PermissionDenied("Nemáte oprávnění prohlizet data ostatnich.")
        return view_func(request, *args, **kwargs)

    return login_required(wrapper)


ALL_CLASSES_GROUP_NAMES = [CAPO_DI_TUTTI_GROUP_NAME, SECRETARY_OF_THE_TREASURY_GROUP_NAME]


def can_view_all_classes(user) -> bool:
    """Členové skupiny CapoDiTutti a SecretaryOfTheTreasury (a superuživatelé) vidí
    kontakty na členy ve všech třídách, ne jen ve třídách svých dětí."""
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name__in=ALL_CLASSES_GROUP_NAMES).exists()
    )
