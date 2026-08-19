from datetime import date

from django.contrib.auth import get_user_model
from django.db.models import Q

from main.models import ClassRepresentative
from main.permissions import (
    CAPO_DI_TUTTI_GROUP_NAME,
    VR_MEMBER_GROUP_NAME,
    WAGTAIL_EDITORS_GROUP_NAME,
    WAGTAIL_MODERATORS_GROUP_NAME,
    WELCOMING_TEAM_GROUP_NAME,
)


def _check_capo() -> list[str]:
    """Nesrovnalosti v přiřazení skupin/rolí členům CapoDiTutti."""
    User = get_user_model()
    issues = []

    capo_not_vr = User.objects.filter(groups__name=CAPO_DI_TUTTI_GROUP_NAME).exclude(
        groups__name=VR_MEMBER_GROUP_NAME
    ).distinct().order_by('last_name', 'first_name')
    for user in capo_not_vr:
        issues.append(f"{user.get_full_name()} je v CapoDiTutti, ale není ve VRmember.")

    capo_not_staff = User.objects.filter(groups__name=CAPO_DI_TUTTI_GROUP_NAME, is_staff=False).distinct().order_by(
        'last_name', 'first_name'
    )
    for user in capo_not_staff:
        issues.append(f"{user.get_full_name()} je v CapoDiTutti, ale nemá přístup do administrace (is_staff).")

    capo_not_moderator = User.objects.filter(groups__name=CAPO_DI_TUTTI_GROUP_NAME).exclude(
        groups__name=WAGTAIL_MODERATORS_GROUP_NAME
    ).distinct().order_by('last_name', 'first_name')
    for user in capo_not_moderator:
        issues.append(f"{user.get_full_name()} je v CapoDiTutti, ale není v Moderators.")

    return issues


def _check_vr_member() -> list[str]:
    """Nesrovnalosti v přiřazení skupin/rolí členům VRmember."""
    User = get_user_model()
    currently_valid = Q(valid_until__isnull=True) | Q(valid_until__gte=date.today())
    issues = []

    reps_not_vr = ClassRepresentative.objects.filter(
        currently_valid, representant_type=ClassRepresentative.RepresentantType.VR,
    ).exclude(
        representative__user__groups__name=VR_MEMBER_GROUP_NAME
    ).select_related('representative__user', 'school_class').order_by('school_class__year')
    for rep in reps_not_vr:
        issues.append(
            f"{rep.representative.user.get_full_name()} zastupuje třídu {rep.school_class} ve VR, "
            "ale není ve skupině VRmember."
        )

    welcoming_not_vr = User.objects.filter(groups__name=WELCOMING_TEAM_GROUP_NAME).exclude(
        groups__name=VR_MEMBER_GROUP_NAME
    ).distinct().order_by('last_name', 'first_name')
    for user in welcoming_not_vr:
        issues.append(f"{user.get_full_name()} je ve WelcomingTeam, ale není ve VRmember.")

    editor_not_vr = User.objects.filter(groups__name=WAGTAIL_EDITORS_GROUP_NAME).exclude(
        groups__name=VR_MEMBER_GROUP_NAME
    ).distinct().order_by('last_name', 'first_name')
    for user in editor_not_vr:
        issues.append(f"{user.get_full_name()} je v Editors, ale není ve VRmember.")

    moderator_not_vr = User.objects.filter(groups__name=WAGTAIL_MODERATORS_GROUP_NAME).exclude(
        groups__name=VR_MEMBER_GROUP_NAME
    ).distinct().order_by('last_name', 'first_name')
    for user in moderator_not_vr:
        issues.append(f"{user.get_full_name()} je v Moderators, ale není ve VRmember.")

    return issues


def check_setup() -> list[str]:
    return _check_capo() + _check_vr_member()
