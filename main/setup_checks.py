from datetime import date

from django.contrib.auth import get_user_model
from django.db.models import Q

from main.models import ClassRepresentative
from main.permissions import (
    CAPO_DI_TUTTI_GROUP_NAME,
    VR_MEMBER_GROUP_NAME,
    WAGTAIL_EDITORS_GROUP_NAME,
    WELCOMING_TEAM_GROUP_NAME,
)


def check_setup() -> list[str]:
    """Zkontroluje konzistenci přiřazení skupin/rolí a vrátí seznam textových
    popisů nalezených nesrovnalostí (prázdný seznam = vše v pořádku)."""
    User = get_user_model()
    currently_valid = Q(valid_until__isnull=True) | Q(valid_until__gte=date.today())

    issues = []

    capo_not_vr = User.objects.filter(groups__name=CAPO_DI_TUTTI_GROUP_NAME).exclude(
        groups__name=VR_MEMBER_GROUP_NAME
    ).distinct().order_by('last_name', 'first_name')
    for user in capo_not_vr:
        issues.append(f"{user.get_full_name()} je v CapoDiTutti, ale není ve VRmember.")

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

    vr_not_editors = User.objects.filter(groups__name=VR_MEMBER_GROUP_NAME).exclude(
        groups__name=WAGTAIL_EDITORS_GROUP_NAME
    ).distinct().order_by('last_name', 'first_name')
    for user in vr_not_editors:
        issues.append(f"{user.get_full_name()} je ve VRmember, ale není v Editors.")

    welcoming_not_vr = User.objects.filter(groups__name=WELCOMING_TEAM_GROUP_NAME).exclude(
        groups__name=VR_MEMBER_GROUP_NAME
    ).distinct().order_by('last_name', 'first_name')
    for user in welcoming_not_vr:
        issues.append(f"{user.get_full_name()} je ve WelcomingTeam, ale není ve VRmember.")

    return issues
