from django.db.models import Q
from django.utils import timezone

from .models import ClassCollective, ClassRepresentative, Profile, ProfileMergeRequest, ProfileStudentRequest, Student
from .permissions import can_approve_requests, can_view_all_classes, can_view_others


def pending_requests_count(request):
    context = {'show_issues_menu': False}

    if can_approve_requests(request.user):
        membership_count = Profile.objects.filter(status=Profile.ProfileStatus.PENDING).count()
        merge_count = ProfileMergeRequest.objects.filter(status=ProfileMergeRequest.RequestStatus.PENDING).count()
        student_count = ProfileStudentRequest.objects.filter(
            status=ProfileStudentRequest.RequestStatus.PENDING
        ).count()

        pending_requests_count = membership_count + merge_count + student_count
        context.update({
            'can_approve_requests': True,
            'pending_membership_requests_count': membership_count,
            'pending_merge_requests_count': merge_count,
            'pending_student_requests_count': student_count,
            'pending_requests_count': pending_requests_count,
        })
        if pending_requests_count:
            context['show_issues_menu'] = True

    if can_view_others(request.user):
        today = timezone.localdate()
        currently_valid = Q(valid_until__isnull=True) | Q(valid_until__gte=today)

        orphaned_students_qs = Student.objects.filter(parents__isnull=True)
        if not can_view_all_classes(request.user):
            represented_class_ids = ClassRepresentative.objects.filter(
                currently_valid, representative=getattr(request.user, 'profile', None),
                representant_type=ClassRepresentative.RepresentantType.VR,
            ).values_list('school_class_id', flat=True)
            orphaned_students_qs = orphaned_students_qs.filter(school_class_id__in=represented_class_ids)
        orphaned_students_count = orphaned_students_qs.count()

        orphaned_members_count = Profile.objects.filter(
            status=Profile.ProfileStatus.ACTIVE, children__isnull=True
        ).count()

        classes_with_vr = set(ClassRepresentative.objects.filter(
            currently_valid, representant_type=ClassRepresentative.RepresentantType.VR
        ).values_list('school_class_id', flat=True))
        classes_with_treasurer = set(ClassRepresentative.objects.filter(
            currently_valid, representant_type=ClassRepresentative.RepresentantType.TREASURER
        ).values_list('school_class_id', flat=True))
        orphaned_classes_count = (
            ClassCollective.objects.exclude(pk__in=classes_with_vr)
            | ClassCollective.objects.exclude(pk__in=classes_with_treasurer)
        ).distinct().count()

        issues_count = orphaned_students_count + orphaned_members_count + orphaned_classes_count
        context.update({
            'can_view_others': True,
            'orphaned_students_count': orphaned_students_count,
            'orphaned_members_count': orphaned_members_count,
            'orphaned_classes_count': orphaned_classes_count,
            'issues_count': issues_count,
        })
        if issues_count:
            context['show_issues_menu'] = True

    return context


def nastenka_pages(request):
    from wagtail.models import Page

    pages = Page.objects.live().filter(show_in_menus=True).order_by('title')
    visible_pages = [
        page for page in pages
        if all(restriction.accept_request(request) for restriction in page.get_view_restrictions())
    ]
    return {'nastenka_pages': visible_pages}


def user_avatar_url(request):
    """Adresa avataru z prvního propojeného účtu (Google apod.), který nějaký nabízí -
    viz SocialAccount.get_avatar_url(). Providery bez avataru (Facebook, MojeID) vrátí None."""
    if not request.user.is_authenticated:
        return {}

    for account in request.user.socialaccount_set.all():
        avatar_url = account.get_avatar_url()
        if avatar_url:
            return {'user_avatar_url': avatar_url}

    return {}


def available_classes(request):
    user = request.user
    profile = getattr(user, 'profile', None)
    if profile is None or profile.status != Profile.ProfileStatus.ACTIVE:
        return {}

    if can_view_all_classes(user):
        classes = ClassCollective.objects.all()
    else:
        classes = ClassCollective.objects.filter(students__parents=profile).distinct()

    return {'available_classes': classes}
