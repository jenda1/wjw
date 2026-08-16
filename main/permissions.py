from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

WELCOMING_TEAM_GROUP_NAME = "WelcomingTeam"
VR_MEMBER_GROUP_NAME = "VRmember"


def can_approve_requests(user) -> bool:
    """Členové skupiny WelcomingTeam (a superuživatelé) mohou schvalovat žádosti
    (o členství, sloučení účtů, přidání žáka)."""
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name=WELCOMING_TEAM_GROUP_NAME).exists()
    )


def approver_required(view_func):
    """Nahrazuje staff_member_required - přístup mají členové skupiny WelcomingTeam."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not can_approve_requests(request.user):
            raise PermissionDenied("Nemáte oprávnění schvalovat žádosti.")
        return view_func(request, *args, **kwargs)

    return login_required(wrapper)


def can_view_others(user) -> bool:
    """Členové skupiny VRmembers mohou videt data o vsech clenech (o členství, sloučení účtů, přidání žáka)."""
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name=VR_MEMBER_GROUP_NAME).exists()
    )


def view_others_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not can_view_others(request.user):
            raise PermissionDenied("Nemáte oprávnění prohlizet data ostatnich.")
        return view_func(request, *args, **kwargs)

    return login_required(wrapper)
